"""Index analyzer plugin for Yeti indicators."""

import json
import re

from typing import Dict, List

from flask import current_app
import requests

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib import emojis


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


class YetiTriageIndicators(interface.BaseAnalyzer):
    """Analyzer for Yeti threat intel indicators."""

    NAME = "yetitriageindicators"
    DISPLAY_NAME = "Yeti triage indicators"
    DESCRIPTION = "Mark triage events using forensics indicators from Yeti"

    DEPENDENCIES = frozenset(["domain"])

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
        self._intelligence_attribute = None

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

    def find_indicators(
        self, yeti_object: Dict, max_hops: int, indicator_types: List[str]
    ) -> List[Dict]:
        """Retrieves a list of neighbors associated to a given entity.

        Args:
          yeti_object: The Yeti object to get neighbors from.
          max_hops: The number of hops to traverse from the entity.
          indicator_types: A list of Yeti indicator types to filter by.

        Returns:
          A list of JSON objects describing a Yeti entity.
        """
        if yeti_object["id"] in NEIGHBOR_CACHE:
            return NEIGHBOR_CACHE[yeti_object["id"]]

        extended_id = f"{yeti_object['root_type']}/{yeti_object['id']}"
        results = self.authenticated_session.post(
            f"{self.yeti_api_root}/graph/search",
            json={
                "count": 0,
                "source": extended_id,
                "graph": "links",
                "min_hops": 1,
                "max_hops": max_hops,
                "direction": "outbound",
                "include_original": False,
                "target_types": indicator_types,
            },
        )
        if results.status_code != 200:
            raise RuntimeError(
                f"Error {results.status_code} retrieving neighbors for "
                f"{extended_id} from Yeti:" + str(results.json())
            )
        neighbors = {}
        for neighbor in results.json().get("vertices", {}).values():
            if neighbor["type"] in ["regex"]:
                neighbors[neighbor["id"]] = neighbor
            NEIGHBOR_CACHE[yeti_object["id"]] = neighbors
        return neighbors

    def get_entities(self, tags: list[str]) -> Dict[str, dict]:
        """Fetches Entities with a certain tag on Yeti.

        Args:
            tags: A list of tags to filter entities with.

        Returns:
            A dictionary of entities obtained from Yeti, keyed by entity ID.
        """
        response = self.authenticated_session.post(
            self.yeti_api_root + "/entities/search",
            json={"query": {"name": "", "tags": tags}, "count": 0},
        )
        data = response.json()
        if response.status_code != 200:
            raise RuntimeError(
                f"Error {response.status_code} retrieving entities from Yeti:"
                + str(data)
            )
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
        tags = [slugify(tag) for tag in indicator["relevant_tags"]]
        for n in neighbors:
            tags.append(slugify(n["name"]))
            emoji_name = TYPE_TO_EMOJI[n["type"]]
            event.add_emojis([emojis.get_emoji(emoji_name)])

        event.add_tags(tags)
        event.commit()

        msg = f'Indicator match: "{indicator["name"]}" (ID: {indicator["id"]})\n'
        if neighbors:
            msg += f'Related entities: {[n["name"] for n in neighbors]}'

        comments = {c.comment for c in event.get_comments()}
        if msg not in comments:
            event.add_comment(msg)
            event.commit()

    def add_intelligence_entry(self, indicator, event, entity):
        uri = f"{self.yeti_web_root}/indicators/{indicator['id']}"

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

    def add_intelligence(self, items):
        intelligence_items = self._intelligence_attribute.get("data", [])
        intelligence_items.extend(items)

        self.sketch.add_sketch_attributes(
            "intelligence",
            [json.dumps({"data": intelligence_items})],
            ontology="intelligence",
            overwrite=True,
        )
        self.sketch.commit()

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

        entities = self.get_entities(tags=["triage"])
        for entity in entities.values():
            indicators = self.find_indicators(
                entity, max_hops=5, indicator_types=["regex"]
            )
            for indicator in indicators.values():
                query_dsl = {
                    "query": {
                        "regexp": {
                            "message.keyword": ".*" + indicator["pattern"] + ".*"
                        }
                    }
                }
                events = self.event_stream(
                    query_dsl=query_dsl, return_fields=["message"], scroll=False
                )

                for event in events:
                    total_matches += 1
                    self.mark_event(indicator, event, [entity])
                    matching_indicators.add(indicator["id"])
                    if entity["type"] in HIGH_SEVERITY_TYPES:
                        priority = "HIGH"
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

        success_note = (
            f"{total_matches} events matched {len(matching_indicators)} "
            f"indicators (out of {total_processed} processed).\n\n"
            f"Entities found: {', '.join(entities_found)}"
        )
        self.output.result_summary = success_note

        return str(self.output)


manager.AnalysisManager.register_analyzer(YetiTriageIndicators)
