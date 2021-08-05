# Copyright 2021 Google Inc. All rights reserved.
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

"""Sketch analyzer plugin for geolocating IP addresses."""
from __future__ import unicode_literals

import ipaddress
import logging

from collections import defaultdict

from flask import current_app

import geoip2.database
import geoip2.errors

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


logger = logging.getLogger('timesketch.analyzers.geoip')


class GeoIPSketchPlugin(interface.BaseAnalyzer):
    """Sketch analyzer for geolocating IP addresses."""

    NAME = 'geo_ip'
    DISPLAY_NAME = 'Geolocate IP addresses'
    DESCRIPTION = ('Find the approximate geolocation of an IP address using ' +
                   'MaxMind GeoLite2')
    DEPENDENCIES = frozenset(['feature_extraction'])
    IP_FIELDS = ['ip', 'host_ip', 'src_ip', 'dst_ip', 'source_ip', 'dest_ip', 
        'ip_address', 'client_ip', 'address', 'saddr', 'daddr', 
        'requestMetadata_callerIp', 'a_answer']
    
    def __init__(self, index_name, sketch_id, timeline_id=None):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        self._geolite_database = current_app.config.get('GEO_LITE_2_DB_PATH')
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def _validate_ip(self, ip_address):
        """Return true if ip_address is in a valid format and is non-private."""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_global
        except ValueError as exception:
            return False

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = ' OR '.join(
            ['{0}:*'.format(ip_field) for ip_field in self.IP_FIELDS])
        
        return_fields = self.IP_FIELDS.copy()

        events = self.event_stream(
            query_string=query,
            return_fields=return_fields
        )

        if self._geolite_database is None:
            return 'GeoIP analyzer error - database configuration not set.'

        try:
            with geoip2.database.Reader(self._geolite_database) as reader:
                ip_addresses = defaultdict(lambda: defaultdict(list))

                for event in events:
                    for ip_address_field in self.IP_FIELDS:
                        ip_address = event.source.get(ip_address_field)
                        if ip_address is None:
                            continue
                        
                        ip_address = [ip_address] if isinstance(ip_address, str) else ip_address
                        
                        for ip_addr in ip_address:
                            if not self._validate_ip(ip_addr):
                                logger.debug('Value {0} in {1} not valid.'
                                    .format(ip_addr, ip_address_field))
                                continue
                            ip_addresses[ip_addr][ip_address_field].append(event)

                logger.info('Found {0} ip address(es)'.format(len(ip_addresses)))

                for ip_address, ip_address_fields in ip_addresses.items():
                    try:
                        response = reader.city(ip_address)
                    except geoip2.errors.AddressNotFoundError as exception:
                        logging.debug('IP address {0} not found.'.format(
                            ip_address))
                        continue

                    latitude = response.location.latitude
                    longitude = response.location.longitude
                    country_name = response.country.name
                    iso_code = response.country.iso_code
                    city = response.city.name

                    flag_emoji = emojis.get_emoji(iso_code)

                    if flag_emoji is None:
                        logger.error(
                        'Invalid ISO code {0} encountered for IP {1}.'
                            .format(iso_code, ip_address))
                    for ip_address_field, events in ip_address_fields.items():
                        for event in events:

                            new_attributes = {}
                            if latitude and longitude:
                                new_attributes['{0}_latitude'
                                    .format(ip_address_field)] = latitude
                                new_attributes['{0}_longitude'
                                    .format(ip_address_field)] = longitude
                            if iso_code:
                                new_attributes['{0}_iso_code'
                                    .format(ip_address_field)] = iso_code
                            if city:
                                new_attributes['{0}_city'
                                    .format(ip_address_field)] = city
                            event.add_attributes(new_attributes)

                            if flag_emoji:
                                event.add_emojis([flag_emoji])

                            event.add_tags([country_name])
                            event.commit()

                return 'GeoIP analyzer completed.'
        except FileNotFoundError as exception:
            logger.error('GeoLite2 database not found')
            return 'GeoIP analyzer error - database not found.'
        except geoip2.database.maxminddb.InvalidDatabaseError as exception:
            logger.error('Geolite2 database is corrupt')
            return 'GeoIP analyzer error - corrupt database.'


manager.AnalysisManager.register_analyzer(GeoIPSketchPlugin)
