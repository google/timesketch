# Copyright 2019 Google Inc. All rights reserved.
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
"""This file contains utilities for analyzers."""

from __future__ import unicode_literals

try:
    from urlparse import urlparse
except ImportError:
    from urllib import parse as urlparse  # pylint: disable=no-name-in-module


def get_domain_from_url(url):
    """Extract domain from URL.

    Args:
        url: URL to parse.

    Returns:
        String with domain from URL.
    """
    # TODO: See if we can optimize this because it is rather slow.
    domain_parsed = urlparse(url)
    domain_full = domain_parsed.netloc
    domain, _, _ = domain_full.partition(':')
    return domain


def get_tld_from_domain(domain):
    """Get the top level domain from a domain string.

    Args:
        domain: string with a full domain, eg. www.google.com

    Returns:
        string: TLD or a top level domain extracted from the domain,
        eg: google.com
    """
    return '.'.join(domain.split('.')[-2:])


def strip_www_from_domain(domain):
    """Strip www. from beginning of domain names.

    Args:
        domain: string with a full domain, eg. www.google.com

    Returns:
        string: Domain without any www, eg: google.com
    """
    if domain.startswith('www.'):
        return domain[4:]
    return domain
