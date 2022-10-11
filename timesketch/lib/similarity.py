# Copyright 2018 Google Inc. All rights reserved.
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
"""Similarity scorer."""

from __future__ import unicode_literals

import re

from six.moves import filter

from datasketch.minhash import MinHash
from datasketch.lsh import MinHashLSH


# Parameters for Jaccard and Minhash calculations.
DEFAULT_DELIMITERS = [" ", "-", "/"]
DEFAULT_THRESHOLD = 0.5
DEFAULT_PERMUTATIONS = 128


def _shingles_from_text(text, delimiters):
    """Splits string into words.

    Args:
        text: string to extract words from.
        delimiters: list of strings used as delimiters for splitting text
            into words.

    Returns:
        List of words.
    """
    # TODO: Remove stopwords using the NLTK python package.
    # TODO: Remove configured patterns from string.
    return list(filter(None, re.split("|".join(delimiters), text)))


def minhash_from_text(text, num_perm, delimiters):
    """Calculate minhash of text.

    Args:
        text: string to calculate minhash of.
        num_perm: number of random permutation functions used by MinHash to
            be indexed.
        delimiters: list of strings used as delimiters for splitting text
            into words.

    Returns:
        A minhash (instance of datasketch.minhash.MinHash)
    """
    minhash = MinHash(num_perm)
    for word in _shingles_from_text(text, delimiters):
        minhash.update(word.encode("utf8"))
    return minhash


def new_lsh_index(events, field, delimiters=None, num_perm=None, threshold=None):
    """Create a new LSH from a set of Timesketch events.

    Args:
        events: list or an iterator of Event objects.
        field: string denoting the event field to use for the LSH.
        delimiters: list of strings used as delimiters for splitting text
            into words.
        num_perm: number of random permutation functions used by MinHash to
            be indexed.
        threshold: a float for the Jaccard similarity threshold between 0.0 and
            1.0. The initialized MinHash LSH will be optimized for the
            threshold by minizing the false positive and false negative.

    Returns:
        A tuple with an LSH (instance of datasketch.lsh.LSH) and a
        dictionary with event ID as key and minhash as value.
    """
    if delimiters is None:
        delimiters = DEFAULT_DELIMITERS
    if num_perm is None:
        num_perm = DEFAULT_PERMUTATIONS
    if threshold is None:
        threshold = DEFAULT_THRESHOLD

    minhashes = {}
    lsh = MinHashLSH(threshold, num_perm)

    with lsh.insertion_session() as lsh_session:
        for event in events:
            # Insert minhash in LSH index.
            key = (event.event_id, event.index_name)
            minhash = minhash_from_text(event.source[field], num_perm, delimiters)
            minhashes[key] = minhash
            lsh_session.insert(key, minhash)

    return lsh, minhashes


def calculate_score(lsh, minhash, total_num_events):
    """Calculate a score based on Jaccard distance.

    The score is calculated based on how many similar events that there are
    for the event being scored. This is called neighbours and we simply
    calculate how many neighbours the event has divided by the total events
    in the LSH.

    Args:
        lsh: instance of datasketch.lsh.MinHashLSH
        minhash: instance of datasketch.minhash.MinHash
        total_num_events: integer of how many events in the LSH

    Returns:
        A float between 0 and 1.
    """
    neighbours = lsh.query(minhash)
    return float(len(neighbours)) / float(total_num_events)
