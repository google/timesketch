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
"""Utilities for OpenSearch index name validation and canonicalization."""

import re
from typing import Optional
import uuid

_HEX32_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")
_HEX32_LOWER_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_PREFIX_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def validate_index_prefix(prefix: Optional[str]) -> None:
    """Validate that prefix is a valid OpenSearch index name prefix.

    A valid prefix must be a lowercase string, start with an alphanumeric
    character, and contain only lowercase alphanumeric characters, underscores,
    or hyphens. Empty string and None are valid (indicating no prefix).

    Args:
        prefix: The prefix string to validate.

    Raises:
        ValueError: If prefix is not a string or contains invalid characters.
    """
    if prefix is None or prefix == "":
        return
    if not isinstance(prefix, str):
        raise ValueError(f"Index prefix must be a string, got {type(prefix).__name__}")
    if not _PREFIX_PATTERN.fullmatch(prefix):
        raise ValueError(
            f"Invalid index prefix {prefix!r}. Prefix must be lowercase, start with "
            "an alphanumeric character, and contain only [a-z0-9_-]."
        )


def is_uuid_hex(value: Optional[str]) -> bool:
    """Check if value is a 32-character hexadecimal string.

    Args:
        value: String to check.

    Returns:
        True if value is a 32-character hex string, False otherwise.
    """
    if not value or not isinstance(value, str):
        return False
    return bool(_HEX32_PATTERN.fullmatch(value))


def is_canonical_index_name(index_name: Optional[str], prefix: str = "") -> bool:
    """Check if index_name matches the canonical Timesketch index naming pattern.

    OpenSearch requires index names to be strictly lowercase.
    When prefix is non-empty, index_name must start with prefix and end with
    exactly 32 lowercase hex characters (^<prefix>[0-9a-f]{32}$).
    When prefix is empty, index_name must be a 32 lowercase hex character string.

    Args:
        index_name: The index name to validate.
        prefix: The configured prefix string (default "").

    Returns:
        True if index_name is in canonical format, False otherwise.
    """
    validate_index_prefix(prefix)
    if not index_name or not isinstance(index_name, str):
        return False
    prefix = prefix or ""
    if prefix:
        if not index_name.startswith(prefix):
            return False
        suffix = index_name[len(prefix) :]
        return bool(_HEX32_LOWER_PATTERN.fullmatch(suffix))
    return bool(_HEX32_LOWER_PATTERN.fullmatch(index_name))


def canonicalize_index_name(index_name: Optional[str] = None, prefix: str = "") -> str:
    """Canonicalize an index name according to configured prefix.

    OpenSearch requires index names to be strictly lowercase.

    When prefix is set (non-empty):
        - None or empty string -> f"{prefix}{uuid4().hex}"
        - Bare 32-hex string -> f"{prefix}{index_name.lower()}"
        - Already prefixed 32-hex string -> f"{prefix}{suffix.lower()}"
        - Anything else -> raises ValueError

    When prefix is empty (""):
        - None or empty string -> uuid4().hex
        - Bare 32-hex string -> index_name.lower()
        - Anything else -> raises ValueError

    Args:
        index_name: Optional candidate index name.
        prefix: Configured index prefix (default "").

    Returns:
        The canonical lowercase index name string.

    Raises:
        ValueError: If index_name or prefix is invalid.
    """
    validate_index_prefix(prefix)
    prefix = prefix or ""

    if index_name is not None and not isinstance(index_name, str):
        raise ValueError(
            f"Index name must be a string, got {type(index_name).__name__}"
        )

    if index_name is None or index_name == "":
        return f"{prefix}{uuid.uuid4().hex}"

    clean_name = index_name.strip()
    if not clean_name:
        return f"{prefix}{uuid.uuid4().hex}"

    # Check bare 32 hex
    if is_uuid_hex(clean_name):
        return f"{prefix}{clean_name.lower()}"

    # Check prefixed 32 hex (case-insensitive suffix, canonical lowercase)
    if prefix:
        clean_lower = clean_name.lower()
        if clean_lower.startswith(prefix):
            suffix = clean_lower[len(prefix) :]
            if bool(_HEX32_LOWER_PATTERN.fullmatch(suffix)):
                return f"{prefix}{suffix}"

    raise ValueError(
        f"Invalid index name {index_name!r} for prefix {prefix!r}. "
        "Must be a 32-character hex UUID or match the canonical prefixed format."
    )
