"""Index analyzer plugin for Yeti indicators."""

import json
import logging
import re
from typing import Dict, List, Optional, Union

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

NEIGHBOR_CACHE = {}

HIGH_SEVERITY_TYPES = {
    "malware",
    "threat-actor",
    "intrusion-set",
    "campaign",
    "vulnerability",
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

    # Entities with these tags will be fetched from Yeti
    _TAG_SELECTOR: List[str] = []
    # Entities of this type will be fetched from Yeti
    _TYPE_SELECTOR: Union[str, None] = None
    # Graph will be traversed from the entities looking for these types
    # of neighbors
    _TARGET_NEIGHBOR_TYPE: List[str] = []
    # If True, will save intelligence to the sketch
    _SAVE_INTELLIGENCE: bool = False

    # Number of hops to traverse from the entity
    _MAX_HOPS = 5
    # Direction to traverse the graph
    _DIRECTION = "outbound"

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

    def _get_neighbors_request(self, params):
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
        if yeti_object["id"] in NEIGHBOR_CACHE:
            return NEIGHBOR_CACHE[yeti_object["id"]]

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
            # Yeti will return all vertices in the graph's path, not just
            # the ones that are fo type target_types. We still want these
            # in the cache.
            if neighbor["type"] in neighbor_types:
                neighbors[neighbor["id"]] = neighbor
            NEIGHBOR_CACHE[yeti_object["id"]] = neighbors
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

    def get_entities(self, _type: str, tags: List[str]) -> Dict[str, dict]:
        """Fetches Entities with a certain tag on Yeti.

        Args:
            _type: Search entities of this type
            tags: A list of tags to filter entities with.

        Returns:
            A dictionary of entities obtained from Yeti, keyed by entity ID.
        """
        query = {"name": "", "tags": tags}
        if _type:
            query["type"] = _type
        data = self._get_entities_request({"query": query, "count": 0})
        entities = {item["id"]: item for item in data["entities"]}
        return entities

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
        tags = {slugify(tag) for tag in indicator["relevant_tags"]}
        for neighbor in neighbors:
            tags.add(slugify(neighbor["name"]))
            emoji_name = TYPE_TO_EMOJI[neighbor["type"]]
            event.add_emojis([emojis.get_emoji(emoji_name)])

        event.add_tags(list(tags))
        event.commit()

        msg = f'Indicator match: "{indicator["name"]}" (ID: {indicator["id"]})\n'
        if neighbors:
            msg += f'Related entities: {[neighbor["name"] for neighbor in neighbors]}'

        comments = {comment.comment for comment in event.get_comments()}
        if msg not in comments:
            event.add_comment(msg)
            event.commit()

    def add_intelligence_entry(self, indicator, event, entity):
        uri = f"{self.yeti_web_root}/indicators/{indicator['id']}"

        if "compiled_regexp" not in indicator:
            indicator["compiled_regexp"] = re.compile(indicator["pattern"])
        regexp = indicator["compiled_regexp"]
        match = regexp.search(event.source.get("message"))
        if match:
            match_in_sketch = match.group(0)
        if not match:
            return

        if (match_in_sketch, uri) in self._intelligence_refs:
            return

        intel = {
            "externalURI": uri,
            "ioc": match_in_sketch,
            "tags": indicator["relevant_tags"] + [entity["name"]],
            "type": "other",
        }

        self._intelligence_attribute["data"].append(intel)
        self._intelligence_refs.add((match_in_sketch, uri))

    def get_intelligence_attribute(self):
        try:
            self._intelligence_attribute = self.sketch.get_sketch_attributes(
                "intelligence"
            )
            self._intelligence_refs = {
                (ioc["ioc"], ioc["externalURI"])
                for ioc in self._intelligence_attribute["data"]
            }
        except ValueError:
            print("Intelligence not set on sketch, will be created from scratch.")

    def save_intelligence(self):
        self.sketch.add_sketch_attribute(
            "intelligence",
            [json.dumps(self._intelligence_attribute)],
            ontology="intelligence",
            overwrite=True,
        )

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
            String with summary of the analyzer result
        """
        if not self.yeti_api_root or not self.yeti_api_key:
            return "No Yeti configuration settings found, aborting."

        total_matches = 0
        total_processed = 0
        entities_found = set()
        matching_indicators = set()
        priority = "NOTE"

        if self._SAVE_INTELLIGENCE:
            self.get_intelligence_attribute()

        entities = self.get_entities(_type=self._TYPE_SELECTOR, tags=self._TAG_SELECTOR)
        for entity in entities.values():
            indicators = self.get_neighbors(
                entity,
                max_hops=self._MAX_HOPS,
                neighbor_types=self._TARGET_NEIGHBOR_TYPE,
            )
            for indicator in indicators.values():
                query_dsl = None
                if indicator["type"] == "regex":
                    query_dsl = self.build_query_from_regexp(indicator)
                if indicator["type"] == "sigma":
                    query_dsl = self.build_query_from_sigma(indicator)
                if (
                    indicator["type"] == "query"
                    and indicator["query_type"] == "opensearch"
                ):
                    query_dsl = {
                        "query": {"query_string": {"query": indicator["pattern"]}}
                    }
                if not query_dsl:
                    continue
                events = self.event_stream(
                    query_dsl=query_dsl, return_fields=["message"], scroll=False
                )

                for event in events:
                    total_matches += 1
                    self.mark_event(indicator, event, [entity])
                    matching_indicators.add(indicator["id"])
                    if entity["type"] in HIGH_SEVERITY_TYPES:
                        priority = "HIGH"
                        if self._SAVE_INTELLIGENCE:
                            self.add_intelligence_entry(indicator, event, entity)

                    entities_found.add(f"{entity['name']}:{entity['type']}")

                total_processed += 1

        self.output.result_status = "SUCCESS"
        self.output.result_priority = priority

        if not total_matches:
            note = "No indicators were found in the timeline."
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
            f"{total_matches} events matched {len(matching_indicators)} "
            f"indicators (out of {total_processed} processed).\n\n"
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
    )

    DEPENDENCIES = frozenset(["domain"])

    _TAG_SELECTOR = ["triage"]
    _TYPE_SELECTOR = "attack-pattern"
    _TARGET_NEIGHBOR_TYPE = ["regex", "query"]
    _SAVE_INTELLIGENCE = False


class YetiMalwareIndicators(YetiBaseAnalyzer):
    """Analyzer for Yeti malware indicators."""

    NAME = "yetimalwareindicators"
    DISPLAY_NAME = "Yeti CTI malware indicators"
    DESCRIPTION = (
        "Mark malware-related events using forensic indicators from "
        "Yeti. Will fetch all malware entities and traverse the"
        " graph searching for regex indicators, and save matches to the "
        " sketch's intelligence attribute."
    )

    DEPENDENCIES = frozenset(["domain"])

    _TAG_SELECTOR = []
    _TYPE_SELECTOR = "malware"
    _TARGET_NEIGHBOR_TYPE = ["regex"]
    _SAVE_INTELLIGENCE = True


class YetiLOLBASIndicators(YetiBaseAnalyzer):
    """Analyzer for Yeti LOLBAS indicators."""

    NAME = "yetilolbasindicators"
    DISPLAY_NAME = "Yeti LOLBAS Sigma indicators"
    DESCRIPTION = (
        "Mark events that match Yeti Sigma indicators linked to tools"
        " that are tagged `lolbas`."
    )

    DEPENDENCIES = frozenset(["yetitriageindicators"])

    _TAG_SELECTOR = ["lolbas"]
    _TYPE_SELECTOR = "tool"
    _TARGET_NEIGHBOR_TYPE = ["sigma", "query"]
    _SAVE_INTELLIGENCE = True
    _DIRECTION = "inbound"
    _MAX_HOPS = 1


manager.AnalysisManager.register_analyzer(YetiTriageIndicators)
manager.AnalysisManager.register_analyzer(YetiMalwareIndicators)
manager.AnalysisManager.register_analyzer(YetiLOLBASIndicators)
