"""Index analyzer plugin for Yeti indicators."""

import datetime
import json
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

import requests
import yaml
from flask import current_app

from timesketch.lib import emojis, sigma_util
from timesketch.lib.analyzers import interface, manager

TYPE_TO_EMOJI = {
    "malware": "SPIDER",
    "threat-actor": "SKULL",
    "intrusion-set": "SKULL",
    "tool": "HAMMER",
    "investigation": "FIRE",
    "campaign": "BOMB",
    "vulnerability": "SHIELD",
    "attack-pattern": "HIGH_VOLTAGE",
}

# Maps Yeti indicator locations to a Timesketch intelligence type
INDICATOR_LOCATION_MAPPING = {"filesystem": "fs_path"}


# Maps Yeti observable types to Timesketch observable types
OBSERVABLE_INTEL_MAPPING = {
    "path": "fs_path",
    "filename": "fs_path",
    "hostname": "hostname",
    "ipv4": "ipv4",
    "sha256": "hash_sha256",
    "sha1": "hash_sha1",
    "md5": "hash_md5",
}

HIGH_SEVERITY_TYPES = {
    "malware",
    "threat-actor",
    "intrusion-set",
    "campaign",
    "vulnerability",
    "investigation",
}


def slugify(text: str) -> str:
    """Converts a string to a slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


class YetiBaseAnalyzer(interface.BaseAnalyzer):
    """Base class for Yeti indicator analyzers."""

    DEPENDENCIES = frozenset(["domain"])

    # Entities of this type will be fetched from Yeti
    # Can optionally contain tags after a `:`
    # e.g. `malware:ransomware,tag2`
    _TYPE_SELECTOR: List[str]
    # Graph will be traversed from the entities looking for these types
    # of neighbors
    _TARGET_NEIGHBOR_TYPE: List[str] = []
    # If True, will save intelligence to the sketch
    _SAVE_INTELLIGENCE: bool = False

    # Number of hops to traverse from the entity
    _MAX_HOPS = 5
    # Direction to traverse the graph. One of {inbound, outbound, any}
    _DIRECTION = "inbound"

    def __init__(self, index_name, sketch_id, timeline_id=None):
        """Initialize the Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: The ID of the sketch.
            timeline_id: The ID of the timeline.
        """
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)
        self.intel = {}
        root = current_app.config.get("YETI_API_ROOT")
        if root.endswith("/"):
            root = root[:-1]
        self.yeti_api_root = root
        self.yeti_web_root = root.replace("/api/v2", "")
        self.yeti_api_key = current_app.config.get("YETI_API_KEY")

        self._yeti_session = requests.Session()
        tls_cert = current_app.config.get("YETI_TLS_CERTIFICATE")
        if tls_cert and self.yeti_web_root.startswith("https://"):
            self._yeti_session.verify = tls_cert

        self._intelligence_refs = set()
        self._intelligence_attribute = {"data": []}

    @property
    def authenticated_session(self) -> requests.Session:
        """Returns a requests.Session object with an authenticated Yeti session.

        Returns:
          A requests.Session object with an authenticated Yeti session.
        """
        if not self._yeti_session.headers.get("authorization"):
            self.authenticate_session()
        return self._yeti_session

    def authenticate_session(self) -> None:
        """Fetches an access token for Yeti."""

        response = self._yeti_session.post(
            f"{self.yeti_api_root}/auth/api-token",
            headers={"x-yeti-apikey": self.yeti_api_key},
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Error {response.status_code} authenticating with Yeti API"
            )

        access_token = response.json()["access_token"]
        self._yeti_session.headers.update({"authorization": f"Bearer {access_token}"})

    def _get_neighbors_request(self, params: Dict) -> Dict:
        """Simple wrapper around requests call to make testing easier."""
        results = self.authenticated_session.post(
            f"{self.yeti_api_root}/graph/search",
            json=params,
        )
        if results.status_code != 200:
            raise RuntimeError(
                f"Error {results.status_code} retrieving neighbors for "
                f"{params['source']} from Yeti:" + str(results.json())
            )
        return results.json()

    def get_neighbors(
        self, yeti_object: Dict, max_hops: int, neighbor_types: List[str]
    ) -> List[Dict]:
        """Retrieves a list of neighbors associated to a given entity.

        Args:
          yeti_object: The Yeti object to get neighbors from.
          max_hops: The number of hops to traverse from the entity.
          neighbor_types: A list of Yeti object types to filter by.

        Returns:
          A list of dictionaries describing a Yeti object.
        """
        extended_id = f"{yeti_object['root_type']}/{yeti_object['id']}"
        request = {
            "count": 0,
            "source": extended_id,
            "graph": "links",
            "min_hops": 1,
            "max_hops": max_hops,
            "direction": self._DIRECTION,
            "include_original": False,
            "target_types": neighbor_types,
        }
        results = self._get_neighbors_request(request)
        neighbors = {}
        for neighbor in results.get("vertices", {}).values():
            if (
                neighbor["type"] in neighbor_types
                or neighbor["root_type"] in neighbor_types
            ):
                neighbors[neighbor["id"]] = neighbor
        return neighbors

    def _get_entities_request(self, params):
        """Simple wrapper around requests call to make testing easier."""
        results = self.authenticated_session.post(
            f"{self.yeti_api_root}/entities/search",
            json=params,
        )
        if results.status_code != 200:
            raise RuntimeError(
                f"Error {results.status_code} retrieving entities from Yeti:"
                + str(results.json())
            )
        return results.json()

    def get_entities(self, type_selector: List[str]) -> Dict[str, dict]:
        """Fetches Entities with a certain tag on Yeti.

        Args:
            type_selector: Use these type selectors to search entities. Type
              Selectors have a TYPE:TAG1,TAG2 format.

        Returns:
            A dictionary of entities obtained from Yeti, keyed by entity ID.
        """
        all_entities = {}
        for _type in type_selector:
            tags = []
            if ":" in _type:
                tag_suffix = _type.split(":")[1]
                _type = _type.replace(":" + tag_suffix, "")
                tags = tag_suffix.split(",")

            query = {"name": "", "tags": tags}
            if _type:
                query["type"] = _type
            data = self._get_entities_request({"query": query, "count": 0})
            entities = {item["id"]: item for item in data["entities"]}
            all_entities.update(entities)
        return all_entities

    def mark_event(
        self, indicator: Dict, event: interface.Event, neighbors: List[Dict]
    ):
        """Annotate an event with data from indicators and neighbors.

        Tags with skull emoji, adds a comment to the event.
        Args:
            indicator: a dictionary representing a Yeti indicator object.
            event: a Timesketch sketch Event object.
            neighbors: a list of Yeti entities related to the indicator.
        """
        if indicator["root_type"] == "indicator":
            tags = {slugify(tag) for tag in indicator["relevant_tags"]}
            msg = f'Indicator match: "{indicator["name"]}" (ID: {indicator["id"]})\n'
        if indicator["root_type"] == "observable":
            tags = {slugify(tag) for tag in indicator["tags"].keys()}
            msg = f'Observable match: "{indicator["value"]}" (ID: {indicator["id"]})\n'
        for neighbor in neighbors:
            tags.add(slugify(neighbor["name"]))
            emoji_name = TYPE_TO_EMOJI[neighbor["type"]]
            event.add_emojis([emojis.get_emoji(emoji_name)])

        event.add_tags(list(tags))
        event.commit()

        if neighbors:
            msg += f'Related entities: {[neighbor["name"] for neighbor in neighbors]}'

        comments = {comment.comment for comment in event.get_comments()}
        if msg not in comments:
            event.add_comment(msg)
            event.commit()

    def add_intelligence_entry(
        self, indicator: Dict, event: interface.Event, entity: Dict
    ) -> None:
        """Adds an intelligence entry to the local intelligence attribute.

        For regex indicators, the intelligence will be the match that is
        extracted from the event. For observables, the full message event
        message attribute is used.

        Args:
            indicator: The Yeti indicator that matched the event.
            event: The Timesketch event that intelligence needs to be extracted
                from.
            entity: The Yeti Entity that is linked to the indicator.
        """
        intel_type = "other"
        match_in_sketch = None

        if indicator["type"] == "regex":
            if "compiled_regexp" not in indicator:
                indicator["compiled_regexp"] = re.compile(indicator["pattern"])
            regexp = indicator["compiled_regexp"]
            match = regexp.search(event.source.get("message"))
            if match:
                match_in_sketch = match.group(0)
            if not match:
                return

            uri = f"{self.yeti_web_root}/indicators/{indicator['id']}"
            intel_type = INDICATOR_LOCATION_MAPPING.get(indicator["location"], "other")
            tags = indicator["relevant_tags"]

        if indicator["root_type"] == "observable":
            match_in_sketch = indicator["value"]
            intel_type = OBSERVABLE_INTEL_MAPPING.get(indicator["type"], "other")
            uri = f"{self.yeti_web_root}/observables/{indicator['id']}"
            tags = list(indicator["tags"].keys())

        if not match_in_sketch:
            return

        if (match_in_sketch, uri) in self._intelligence_refs:
            return

        intel = {
            "externalURI": uri,
            "ioc": match_in_sketch,
            "tags": [slugify(tag) for tag in tags + [entity["name"]]],
            "type": intel_type,
        }

        self._intelligence_attribute["data"].append(intel)
        self._intelligence_refs.add((match_in_sketch, uri))

    def _merge_intelligence_attributes(self, attribute_values):
        """Merges multiple intelligence values that might have been stored."""
        data = []
        existing_refs = set()
        for value in attribute_values:
            for ioc in value["data"]:
                if ioc["externalURI"] in existing_refs:
                    continue
                data.append(ioc)
                existing_refs.add(ioc["externalURI"])
        return {"data": data}

    def get_intelligence_attribute(self) -> Tuple[Dict, Set[Tuple[str, str]]]:
        """Fetches the intelligence attribute from the database."""
        try:
            intelligence_attribute = self.sketch.get_sketch_attributes("intelligence")

            # In some cases, the intelligence attribute may be split into
            # multiple "values" due tu race conditions. Merge them if that's
            # the case. The API will return only the first value if the list
            # has 1 element, so this check is necessary.
            if isinstance(intelligence_attribute, list):
                intelligence_attribute = self._merge_intelligence_attributes(
                    intelligence_attribute
                )

            refs = {
                (ioc["ioc"], ioc["externalURI"])
                for ioc in intelligence_attribute["data"]
            }
            return intelligence_attribute, refs

        except ValueError:
            logging.debug(
                "Intelligence not set on sketch, will be created from scratch."
            )
        return {"data": []}, set()

    def save_intelligence(self) -> None:
        """Saves the intelligence attribute to the database."""
        # This is necessary to take into account changes that may
        # have been made by other runs of this analyzer or other analyzers
        # that add intelligence to the sketch.
        db_attribute, _ = self.get_intelligence_attribute()
        for ioc in db_attribute["data"]:
            if (ioc["ioc"], ioc["externalURI"]) not in self._intelligence_refs:
                self._intelligence_attribute["data"].append(ioc)

        attribute_string = json.dumps(self._intelligence_attribute)
        self.sketch.add_sketch_attribute(
            "intelligence",
            [attribute_string],
            ontology="intelligence",
            overwrite=True,
        )

    def build_query_from_observable(self, observable: Dict) -> Dict:
        """Builds a query DSL from a Yeti observable.

        Uses a wildcard query on the keyword field of message, given that
        we want to surface all events that contain the verbatim observable
        value.

        Args:
            observable: a dictionary representing a Yeti observable object.

        Returns:
            A dictionary representing a query DSL.
        """
        escaped = observable["value"].replace("\\", "\\\\")
        field = "message.keyword"
        search = f"*{escaped}*"

        if observable["type"] == "sha256":
            field = "sha256_hash"
            search = escaped

        return {
            "query": {
                "wildcard": {
                    field: {
                        "value": search,
                        "case_insensitive": True,
                    }
                },
            },
        }

    def build_query_from_regexp(self, indicator: Dict) -> Dict:
        """Builds a query DSL from a Yeti Regex indicator.

        Args:
            indicator: a dictionary representing a Yeti Regex indicator object.

        Returns:
            A dictionary representing a query DSL.
        """
        field = ""
        if indicator["location"] == "registry":
            field = "key_path.keyword"
        elif indicator["location"] == "filesystem":
            field = "filename.keyword"
        else:
            field = "message.keyword"

        return {
            "query": {
                "bool": {
                    "should": [
                        {
                            "regexp": {
                                field: {
                                    "value": f".*{indicator['pattern']}.*",
                                    "case_insensitive": True,
                                }
                            }
                        },
                        {
                            "regexp": {
                                "display_name.keyword": {
                                    "value": f".*{indicator['pattern']}.*",
                                    "case_insensitive": True,
                                }
                            }
                        },
                    ]
                }
            }
        }

    def build_query_from_sigma(self, indicator: Dict) -> Optional[Dict]:
        """Builds a query DSL from a Yeti Sigma indicator.

        Args:
            indicator: a dictionary representing a Yeti Sigma indicator object.

        Returns:
            A dictionary representing a query DSL.
        """
        try:
            parsed_sigma = sigma_util.parse_sigma_rule_by_text(
                indicator["pattern"], sanitize=False
            )
        except yaml.scanner.ScannerError as exception:
            logging.error(
                "Error parsing Sigma rule %s: %s",
                indicator["id"],
                str(exception),
            )
            return None
        return {"query": {"query_string": {"query": parsed_sigma["search_query"]}}}

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        if not self.yeti_api_root or not self.yeti_api_key:
            return "No Yeti configuration settings found, aborting."

        total_matches = 0
        total_processed = 0
        total_failed = 0
        entities_found = set()
        matching_indicators = set()
        priority = "NOTE"

        self.save_intelligence()

        if self._SAVE_INTELLIGENCE:
            self._intelligence_attribute, self._intelligence_refs = (
                self.get_intelligence_attribute()
            )

        entities = self.get_entities(type_selector=self._TYPE_SELECTOR)
        for entity in entities.values():
            indicators = self.get_neighbors(
                entity,
                max_hops=self._MAX_HOPS,
                neighbor_types=self._TARGET_NEIGHBOR_TYPE,
            )
            logging.debug(
                "Found %d neighbor indicators for %s",
                len(indicators),
                entity["name"],
            )

            for indicator in indicators.values():
                query_dsl = None
                if indicator["root_type"] == "observable":
                    query_dsl = self.build_query_from_observable(indicator)
                elif indicator["type"] == "regex":
                    query_dsl = self.build_query_from_regexp(indicator)
                elif indicator["type"] == "sigma":
                    query_dsl = self.build_query_from_sigma(indicator)
                elif indicator["type"] == "query":
                    if indicator["query_type"] == "opensearch":
                        query_dsl = {
                            "query": {"query_string": {"query": indicator["pattern"]}}
                        }
                if not query_dsl:
                    logging.warning(
                        "Unsupported indicator type, skipping: %s (%s)",
                        indicator["type"],
                        indicator["root_type"],
                    )
                    continue
                events = self.event_stream(
                    query_dsl=query_dsl, return_fields=["message"], scroll=False
                )
                logging.debug("Searching for %s", str(query_dsl))
                try:
                    indicator_match = 0
                    start = datetime.datetime.now()
                    for event in events:
                        total_matches += 1
                        self.mark_event(indicator, event, [entity])
                        matching_indicators.add(indicator["id"])
                        if entity["type"] in HIGH_SEVERITY_TYPES:
                            priority = "HIGH"
                            if self._SAVE_INTELLIGENCE:
                                self.add_intelligence_entry(indicator, event, entity)

                        entities_found.add(f"{entity['name']}:{entity['type']}")
                        indicator_match += 1
                    logging.debug(
                        "Found %s matches for indicator %s in %s",
                        indicator_match,
                        indicator["id"],
                        str(datetime.datetime.now() - start),
                    )
                except Exception as exception:  # pylint: disable=broad-except
                    # No matter the exception, we don't want to stop the
                    # analyzer. Errors are logged and reported in the UI.
                    logging.error(
                        "Error processing events for indicator %s: %s",
                        indicator["id"],
                        str(exception),
                    )
                    total_failed += 1

                total_processed += 1

        self.output.result_status = "SUCCESS"
        self.output.result_priority = priority

        if not total_matches:
            note = (
                f"0/{total_processed} indicators were found in the "
                f"timeline ({total_failed} failed)"
            )
            self.output.result_summary = note
            return str(self.output)

        for entity in entities_found:
            name, _type = entity.split(":")
            self.sketch.add_view(
                f"Indicator matches for {name} ({_type})",
                self.NAME,
                query_string=f'tag:"{name}"',
            )

        if self._SAVE_INTELLIGENCE:
            self.save_intelligence()

        success_note = (
            f"{total_matches} events matched "
            f"{len(matching_indicators)}/{total_processed} "
            f"indicators ({total_failed} failed).\n\n"
            f"Entities found: {', '.join(entities_found)}"
        )
        self.output.result_summary = success_note

        return str(self.output)


class YetiTriageIndicators(YetiBaseAnalyzer):
    """Analyzer for Yeti triage indicators."""

    NAME = "yetitriageindicators"
    DISPLAY_NAME = "Yeti forensics triage indicators"
    DESCRIPTION = (
        "Mark triage events using forensics indicators from Yeti. Will fetch"
        ' all attack-patterns tagged with the "triage" tag, and traverse the'
        " graph searching for regex indicators."
        " {attack-pattern:triage} → {regex, query}"
    )

    DEPENDENCIES = frozenset(["domain"])

    _TYPE_SELECTOR = ["attack-pattern:triage"]
    _TARGET_NEIGHBOR_TYPE = ["regex", "query"]
    _DIRECTION = "inbound"
    _SAVE_INTELLIGENCE = False


class YetiBadnessIndicators(YetiBaseAnalyzer):
    """Analyzer for Yeti indicators related to attacks."""

    NAME = "yetibadnessindicators"
    DISPLAY_NAME = "Yeti badness indicators"
    DESCRIPTION = (
        "Mark badness-related events using indicators from "
        "Yeti. Will fetch all malware and exploit-tagged attack-pattern "
        "entities and traverse the graph searching for regex indicators,"
        " and save matches to the sketch's intelligence attribute. "
        "{malware, attack-pattern:exploit} ← {regex, query}"
    )

    DEPENDENCIES = frozenset(["domain"])

    _TYPE_SELECTOR = ["malware", "attack-pattern:exploit"]
    _TARGET_NEIGHBOR_TYPE = ["regex", "query"]
    _DIRECTION = "inbound"
    _SAVE_INTELLIGENCE = True


class YetiLOLBASIndicators(YetiBaseAnalyzer):
    """Analyzer for Yeti LOLBAS indicators."""

    # YetiTriageIndicators gives extra context around execution, etc.
    DEPENDENCIES = frozenset(["yetitriageindicators"])

    NAME = "yetilolbasindicators"
    DISPLAY_NAME = "Yeti LOLBAS indicators"
    DESCRIPTION = (
        "Mark events that match Yeti indicators linked to tools"
        " that are tagged `lolbas`. {tool:lobas} ← {sigma, query, regex}"
    )

    _TYPE_SELECTOR = ["tool:lolbas"]
    _TARGET_NEIGHBOR_TYPE = ["sigma", "query", "regex"]
    _SAVE_INTELLIGENCE = True
    _DIRECTION = "inbound"
    _MAX_HOPS = 1


class YetiInvestigations(YetiBaseAnalyzer):
    """Analyzer for Yeti investigation-related indicators."""

    NAME = "yetiinvestigations"
    DISPLAY_NAME = "Yeti Investigations intelligence"
    DESCRIPTION = (
        "Mark events that match Yeti investigation indicators and observables."
        " {investigation} ← {indicators, observables}"
    )

    _TYPE_SELECTOR = ["investigation"]
    _TARGET_NEIGHBOR_TYPE = ["sigma", "query", "regex", "observable"]
    _SAVE_INTELLIGENCE = True
    _DIRECTION = "any"
    _MAX_HOPS = 1


manager.AnalysisManager.register_analyzer(YetiTriageIndicators)
manager.AnalysisManager.register_analyzer(YetiBadnessIndicators)
manager.AnalysisManager.register_analyzer(YetiLOLBASIndicators)
manager.AnalysisManager.register_analyzer(YetiInvestigations)
