"""Index analyzer plugin for Yeti indicators."""

import json
import re

from typing import Dict, List

from flask import current_app
import requests

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib import emojis


class YetiIndicators(interface.BaseAnalyzer):
    """Analyzer for Yeti threat intel indicators."""

    NAME = "yetiindicators"
    DISPLAY_NAME = "Yeti CTI indicators"
    DESCRIPTION = "Mark events using CTI indicators from Yeti"

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

    def get_neighbors(self, yeti_object: Dict) -> List[Dict]:
        """Retrieves a list of neighbors associated to a given entity.

        Args:
          yeti_object: The Yeti object to get neighbors from.

        Returns:
          A list of JSON objects describing a Yeti entity.
        """
        extended_id = f"{yeti_object['root_type']}/{yeti_object['id']}"
        results = requests.post(
            f"{self.yeti_api_root}/graph/search",
            json={
                "source": extended_id,
                "graph": "links",
                "hops": 1,
                "direction": "any",
                "include_original": False,
            },
            headers={"X-Yeti-API": self.yeti_api_key},
        )
        if results.status_code != 200:
            return []
        neighbors = []
        for neighbor in results.json().get("vertices", {}).values():
            neighbors.append(neighbor)

        return neighbors

    def get_indicators(self, indicator_type: str) -> dict[str, dict]:
        """Populates the intel attribute with entities from Yeti.

        Returns:
            A dictionary of indicators obtained from yeti, keyed by indicator
            ID.
        """
        response = requests.post(
            self.yeti_api_root + "/indicators/search",
            json={"name": "", "type": indicator_type},
            headers={"X-Yeti-API": self.yeti_api_key},
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Error {response.status_code} retrieving indicators from Yeti:"
                + response.json()
            )
        data = response.json()
        indicators = {item["id"]: item for item in data["indicators"]}
        for _id, indicator in indicators.items():
            indicator["compiled_regexp"] = re.compile(indicator["pattern"])
            indicators[_id] = indicator
        return indicators

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
        event.add_emojis([emojis.get_emoji("SKULL")])
        tags = indicator["relevant_tags"]
        for n in neighbors:
            slug = re.sub(r"[^a-z0-9]", "-", n["name"].lower())
            slug = re.sub(r"-+", "-", slug)
            tags.append(slug)
        event.add_tags(tags)
        event.commit()

        msg = f'Indicator match: "{indicator["name"]}" ({indicator["id"]})\n'
        msg += f'Related entities: {[n["name"] for n in neighbors]}'
        comments = {c.comment for c in event.get_comments()}
        if msg not in comments:
            event.add_comment(msg)
            event.commit()

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        if not self.yeti_api_root or not self.yeti_api_key:
            return "No Yeti configuration settings found, aborting."

        indicators = self.get_indicators("regex")

        entities_found = set()
        total_matches = 0
        new_indicators = set()

        intelligence_attribute = {"data": []}
        existing_refs = set()

        try:
            intelligence_attribute = self.sketch.get_sketch_attributes("intelligence")
            existing_refs = {
                ioc["externalURI"] for ioc in intelligence_attribute["data"]
            }
        except ValueError:
            print("Intelligence not set on sketch, will create from scratch.")

        intelligence_items = []

        for indicator in indicators.values():
            query_dsl = {
                "query": {
                    "regexp": {"message.keyword": ".*" + indicator["pattern"] + ".*"}
                }
            }

            events = self.event_stream(query_dsl=query_dsl, return_fields=["message"])
            neighbors = self.get_neighbors(indicator)

            for event in events:
                total_matches += 1
                self.mark_event(indicator, event, neighbors)

            match = regex.search(event.source.get("message"))
            if match:
                match_in_sketch = match.group()
            else:
                match_in_sketch = indicator["pattern"]

            for n in neighbors:
                entities_found.add(f"{n['name']}:{n['type']}")

            uri = f"{self.yeti_web_root}/indicators/{indicator['id']}"
            intel = {
                "externalURI": uri,
                "ioc": match_in_sketch,
                "tags": [n["name"] for n in neighbors],
                "type": "other",
            }
            if uri not in existing_refs:
                intelligence_items.append(intel)
                existing_refs.add(indicator["id"])
            new_indicators.add(indicator["id"])

        if not total_matches:
            self.output.result_status = "SUCCESS"
            self.output.result_priority = "NOTE"
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

        all_iocs = intelligence_attribute["data"] + intelligence_items
        self.sketch.add_sketch_attribute(
            "intelligence",
            [json.dumps({"data": all_iocs})],
            ontology="intelligence",
            overwrite=True,
        )

        success_note = (
            f"{total_matches} events matched {len(new_indicators)} "
            f"new indicators. Found: {', '.join(entities_found)}"
        )
        self.output.result_status = "SUCCESS"
        self.output.result_priority = "HIGH"
        self.output.result_summary = success_note

        return str(self.output)


manager.AnalysisManager.register_analyzer(YetiIndicators)
