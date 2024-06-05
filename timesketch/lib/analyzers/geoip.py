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

# This geoip analyzer uses GeoLite2 data created by MaxMind,
# available from https://maxmind.com

"""Sketch analyzer plugin for geolocating IP addresses."""

import os
import ipaddress
import logging

from collections import defaultdict
from typing import Tuple, Union

from flask import current_app

import geoip2.database
import geoip2.errors
import geoip2.webservice
import maxminddb

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


logger = logging.getLogger("timesketch.analyzers.geoip")


class GeoIPClientError(Exception):
    """An error raised by the GeoIP client"""


class GeoIpClientAdapter(object):
    """Base adapter interface for a third party geolocation service."""

    def __enter__(self):
        """Initialise and open a new a client (self) for performing IP address
        lookups against a database or service.
        """
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        """Close and clean up client."""
        raise NotImplementedError

    def ip2geo(self, ip_address: str) -> Union[Tuple[str, str, str, str, str], None]:
        """Perform a IP to geolocation lookup.

        Args:
            ip_address - the IPv4 or IPv6 address to geolocate

        Returns:
            Either:
            A tuple comprising of the following in order
            - iso_code (str) - the ISO 31661 alpha-2 code of the country
            - latitude (str) - the north-south coordinate
            - longitude (str) - the east-west coordinate
            - country_name (str) - the full country name
            - city (str) - the city name that approximates the location
            Or None:
            - when the IP address does not have a resolvable location
        """
        raise NotImplementedError


class MaxMindGeoDbClient(geoip2.database.Reader, GeoIpClientAdapter):
    """A GeoIP client using the MaxMind database."""

    def __init__(self):
        self._geolite_database = current_app.config.get("MAXMIND_DB_PATH")
        if not self._geolite_database:
            raise GeoIPClientError("MaxMind Database configuration not set.")
        if not os.path.exists(self._geolite_database):
            raise GeoIPClientError("MaxMind Database does not exist.")
        super().__init__(self._geolite_database)

    def __enter__(self):
        """Initialise and open a new a client (self) for performing IP address
        lookups against a database or service.
        """
        return self

    # pylint: disable=W0235
    def __exit__(self, exc_type, exc_value, traceback):
        """Close and clean up client."""
        return super().__exit__(exc_type, exc_value, traceback)

    def ip2geo(self, ip_address) -> Union[Tuple[str, str, str, str, str], None]:
        """Perform a IP to geolocation lookup.

        Args:
            ip_address - the IPv4 or IPv6 address to geolocate

        Returns:
            Either:
            A tuple comprising of the following in order
            - iso_code (str) - the ISO 31661 alpha-2 code of the country
            - latitude (str) - the north-south coordinate
            - longitude (str) - the east-west coordinate
            - country_name (str) - the full country name
            - city (str) - the city name that approximates the location
            Or None:
            - when the IP address does not have a resolvable location
        """
        try:
            response = self.city(ip_address)
        except geoip2.errors.AddressNotFoundError:
            logging.debug("IP address {0} not found.".format(ip_address))
            return None
        except maxminddb.InvalidDatabaseError as error:
            logging.error("Error while geolocating {0} - {1}".format(ip_address, error))
            return None

        latitude = response.location.latitude
        longitude = response.location.longitude
        country_name = response.country.name
        iso_code = response.country.iso_code
        city = response.city.name

        return (iso_code, latitude, longitude, country_name, city)


class MaxMindGeoWebClient(geoip2.webservice.Client, GeoIpClientAdapter):
    """A GeoIP client using the MaxMind web service api."""

    def __init__(self):
        self._account_id = current_app.config.get("MAXMIND_WEB_ACCOUNT_ID")
        self._license_key = current_app.config.get("MAXMIND_WEB_LICENSE_KEY")
        self._host = current_app.config.get("MAXMIND_WEB_HOST")
        if not self._account_id:
            raise GeoIPClientError("MaxMind Account ID not set.")
        if not self._license_key:
            raise GeoIPClientError("MaxMind License key not set.")
        if not self._host:
            raise GeoIPClientError("MaxMind host not set.")
        super().__init__(self._account_id, self._license_key, host=self._host)

    def __enter__(self):
        """Initialise and open a new a client (self) for performing IP address
        lookups against a database or service.
        """
        return self

    # pylint: disable=W0235
    def __exit__(self, exc_type, exc_value, traceback):
        """Close and clean up client."""
        return super().__exit__(exc_type, exc_value, traceback)

    def ip2geo(self, ip_address) -> Union[Tuple[str, str, str, str, str], None]:
        """Perform a IP to geolocation lookup.

        Args:
            ip_address - the IPv4 or IPv6 address to geolocate

        Returns:
            Either:
            A tuple comprising of the following in order
            - iso_code (str) - the ISO 31661 alpha-2 code of the country
            - latitude (str) - the north-south coordinate
            - longitude (str) - the east-west coordinate
            - country_name (str) - the full country name
            - city (str) - the city name that approximates the location
            Or None:
            - when the IP address does not have a resolvable location
        """
        try:
            response = self.city(ip_address)
        except geoip2.errors.AddressNotFoundError:
            logging.debug("IP address {0} not found.".format(ip_address))
            return None
        except geoip2.errors.GeoIP2Error as error:
            logging.error("Error while geolocating {0} - {1}".format(ip_address, error))
            return None

        latitude = response.location.latitude
        longitude = response.location.longitude
        country_name = response.country.name
        iso_code = response.country.iso_code
        city = response.city.name

        return (iso_code, latitude, longitude, country_name, city)


class BaseGeoIpAnalyzer(interface.BaseAnalyzer):
    """Sketch analyzer for geolocating IP addresses.

    Concrete plugin implementations should define the following attributes
    - NAME (str)
    - DISPLAY_NAME (str)
    - DESCRIPTION (str)
    - GEOIP_CLIENT (concrete subclass of GeoIpClientAdapter).
    """

    NAME = ""
    DISPLAY_NAME = ""
    DESCRIPTION = ""

    GEOIP_CLIENT: type = None

    DEPENDENCIES = frozenset(["feature_extraction"])
    IP_FIELDS = [
        "ip",
        "host_ip",
        "src_ip",
        "dst_ip",
        "source_ip",
        "dest_ip",
        "ip_address",
        "client_ip",
        "address",
        "saddr",
        "daddr",
        "requestMetadata_callerIp",
        "a_answer",
    ]

    def __init__(self, index_name, sketch_id, timeline_id=None):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: Sketch ID
            timeline_id: Timeline ID
        """
        self.index_name = index_name
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def _validate_ip(self, ip_address):
        """Validate an IP address for analysis.

        Args:
            ip_address: the IP address to validate

        Returns:
            True if given IP address is valid and global
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_global
        except ValueError:
            return False

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        if self.GEOIP_CLIENT is None:
            return "GeoIP Client not configured in analyzer"

        query = f'_exists_:({" OR ".join(self.IP_FIELDS)})'

        return_fields = self.IP_FIELDS.copy()

        events = self.event_stream(query_string=query, return_fields=return_fields)

        ip_addresses = defaultdict(lambda: defaultdict(list))

        for event in events:
            for ip_address_field in self.IP_FIELDS:
                ip_address = event.source.get(ip_address_field)
                if ip_address is None:
                    continue

                if isinstance(ip_address, str):
                    ip_address = [ip_address]

                for ip_addr in ip_address:
                    if not self._validate_ip(ip_addr):
                        logger.debug(
                            f"Value {0} in {1} not valid.".format(
                                ip_addr, ip_address_field
                            )
                        )
                        continue
                    ip_addresses[ip_addr][ip_address_field].append(event)

        try:
            client = self.GEOIP_CLIENT()  # pylint: disable=E1102
        except GeoIPClientError as error:
            return f"GeoIP Client error - {error}"

        for ip_address, ip_address_fields in ip_addresses.items():
            response = client.ip2geo(ip_address)

            if not response:
                continue

            try:
                iso_code, latitude, longitude, country_name, city_name = response
            except ValueError:
                logging.error(
                    "GeoIP client must return 5 fields: "
                    "<iso_code, latitude, longitude, country_name, "
                    "city_name>. "
                    " Number of fields returned: {0:d}".format(len(response))
                )
                continue

            flag_emoji = emojis.get_emoji(f"FLAG_{iso_code}")

            if flag_emoji is None:
                logger.error(
                    "Invalid ISO code {0} encountered for IP {1}.".format(
                        iso_code, ip_address
                    )
                )

            for ip_address_field, events in ip_address_fields.items():
                for event in events:
                    new_attributes = {}
                    if latitude and longitude:
                        new_attributes[f"{ip_address_field}_latitude"] = latitude
                        new_attributes[f"{ip_address_field}_longitude"] = longitude
                    if iso_code:
                        new_attributes[f"{ip_address_field}_iso_code"] = iso_code
                    if city_name:
                        new_attributes[f"{ip_address_field}_city"] = city_name
                    event.add_attributes(new_attributes)

                    if flag_emoji:
                        event.add_emojis([flag_emoji])

                    if country_name:
                        event.add_tags([country_name])
                    event.commit()

        return f"Found {len(ip_addresses)} IP address(es)."


class MaxMindDbGeoIPAnalyzer(BaseGeoIpAnalyzer):
    GEOIP_CLIENT = MaxMindGeoDbClient

    NAME = "geo_ip_maxmind_db"
    DISPLAY_NAME = "Geolocate IP addresses (MaxMind Database based)"
    DESCRIPTION = (
        "Find the approximate geolocation of an IP address using "
        "a MaxMind GeoLite2 database, available from https://maxmind.com"
    )


class MaxMindDbWebIPAnalyzer(BaseGeoIpAnalyzer):
    GEOIP_CLIENT = MaxMindGeoWebClient

    NAME = "geo_ip_maxmind_web"
    DISPLAY_NAME = "Geolocate IP addresses (MaxMind Web client based)"
    DESCRIPTION = (
        "Find the approximate geolocation of an IP address using "
        "a MaxMind GeoLite2 web client API, available from https://maxmind.com"
    )


manager.AnalysisManager.register_analyzer(MaxMindDbGeoIPAnalyzer)
manager.AnalysisManager.register_analyzer(MaxMindDbWebIPAnalyzer)
