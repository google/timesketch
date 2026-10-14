# Copyright 2026 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Compatibility helpers for event attributes renamed by Plaso.

Plaso 20260720 renamed several event attributes, e.g. "body" to "message_body"
and "computer_name" to "hostname". Timesketch requires Plaso >= 20260720 for
new imports, but existing timelines created with older Plaso versions still
contain the legacy field names.

This module only maps the renamed Plaso fields that are referenced by
Timesketch's built-in analyzers and graph plugins. Code that reads or queries
these fields should use the current field name together with the helpers in
this module, which fall back to the legacy field names (one-directional:
current name -> legacy name(s)).

Once timelines created with Plaso < 20260720 are no longer supported, remove
the corresponding entries from PLASO_FIELD_ALIASES.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

# Maps the current Plaso field name to its legacy field name(s) for fields
# used by Timesketch's built-in analyzers and graph plugins.
PLASO_FIELD_ALIASES: Dict[str, Tuple[str, ...]] = {
    # log2timeline/plaso#5130: syslog, systemd journal and other text logs.
    "message_body": ("body",),
    # log2timeline/plaso#5136: Windows EventLog (EVT/EVTX) records and others.
    "hostname": ("computer_name",),
}


def get_field_names(field_name: str) -> Tuple[str, ...]:
    """Returns a field name and its legacy aliases in order of preference.

    Args:
        field_name (str): current name of the field, e.g. "message_body".

    Returns:
        tuple[str]: the field name followed by its legacy aliases, e.g.
            ("message_body", "body"). Field names without aliases (including
            legacy names) are returned as a single-element tuple.
    """
    return (field_name, *PLASO_FIELD_ALIASES.get(field_name, ()))


def expand_field_names(field_names: Iterable[str]) -> List[str]:
    """Expands a list of field names with their legacy aliases.

    Useful to build the list of fields to return from a search.

    Args:
        field_names (Iterable[str]): names of fields.

    Returns:
        list[str]: unique field names including legacy aliases, in order of
            first occurrence.
    """
    expanded_field_names = []
    for field_name in field_names:
        for name in get_field_names(field_name):
            if name not in expanded_field_names:
                expanded_field_names.append(name)
    return expanded_field_names


def get_field_value(
    source: Optional[Dict[str, Any]], field_name: str, default: Any = None
) -> Any:
    """Returns the value of a field, falling back to its legacy aliases.

    Args:
        source (dict): event source, e.g. the "_source" of an OpenSearch hit.
        field_name (str): current name of the field, e.g. "hostname".
        default (Any): value to return if neither the field nor any of its
            aliases are set.

    Returns:
        Any: the value of the first field that is set, where None, "-" and
            empty strings, lists, tuples or dicts are considered not set, or
            the default value.
    """
    if not source:
        return default

    for name in get_field_names(field_name):
        value = source.get(name)
        if value in (None, "-"):
            continue
        if isinstance(value, (str, list, tuple, dict)) and not value:
            continue
        return value
    return default


def build_field_query(field_name: str, value: str) -> str:
    """Builds a query string clause that matches a field or its legacy aliases.

    Args:
        field_name (str): current name of the field, e.g. "message_body".
        value (str): query string value, e.g. "*Accepted*".

    Returns:
        str: query string clause, e.g.
            "(message_body:*Accepted* OR body:*Accepted*)", or
            "field_name:value" if the field has no aliases.
    """
    field_names = get_field_names(field_name)
    if len(field_names) == 1:
        return f"{field_name}:{value}"
    clauses = " OR ".join(f"{name}:{value}" for name in field_names)
    return f"({clauses})"
