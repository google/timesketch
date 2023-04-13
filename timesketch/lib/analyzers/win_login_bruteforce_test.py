# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for WindowsLoginBruteForcePlugin."""

from __future__ import unicode_literals

from datetime import datetime, timezone

import logging
import json
import sys
import textwrap

import mock


from timesketch.lib.analyzers.analyzer_output import AnalyzerOutput
from timesketch.lib.analyzers.win_login_bruteforce import WindowsLoginEventData
from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj
from timesketch.lib.analyzers.win_login_bruteforce import WindowsLoginBruteForcePlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

log = logging.getLogger("timesketch")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


def expected_eventdata_4624() -> WindowsLoginEventData:
    """Returns successful login event."""
    event = WindowsLoginEventData()
    event.event_id = ""
    event.timestamp = 0
    event.hostname = ""
    event.event_type = ""
    event.auth_method = ""
    event.auth_result = ""
    event.domain = "WIN-VQB2KAEFA34"
    event.username = "Administrator"
    event.source_ip = "192.168.40.23"
    event.source_port = 0
    event.source_hostname = "kali"
    event.session_id = "0x0000000001e69eb6"
    event.eid = None
    event.logon_type = 3
    event.process_id = "0x0000000000000000"
    event.process_name = "-"

    return event


def expected_eventdata_4625() -> WindowsLoginEventData:
    """Returns successful login event."""
    event = WindowsLoginEventData()
    event.event_id = ""
    event.timestamp = 0
    event.hostname = ""
    event.event_type = ""
    event.auth_method = ""
    event.auth_result = ""
    event.domain = None
    event.username = "administrator"
    event.source_ip = "192.168.40.23"
    event.source_port = 46658
    event.source_hostname = None
    event.eid = None
    event.logon_type = 3
    event.process_id = "0x0000000000000000"
    event.process_name = "-"

    return event


def expected_eventdata_4634() -> WindowsLoginEventData:
    """Returns successful login event."""
    event = WindowsLoginEventData()
    event.event_id = ""
    event.timestamp = 0
    event.hostname = ""
    event.event_type = ""
    event.auth_method = ""
    event.auth_result = ""
    event.domain = "WIN-VQB2KAEFA34"
    event.username = "Administrator"
    event.source_ip = ""
    event.source_port = 0
    event.source_hostname = ""
    event.session_id = "0x0000000001e69eb6"
    event.eid = None
    event.logon_type = 3
    event.process_id = None
    event.process_name = None

    return event


def expected_bruteforce_output() -> str:
    """Returns brute force output."""
    output = AnalyzerOutput(
        analyzer_id="analyzer.bruteforce.windows",
        analyzer_name="Windows BruteForce Analyzer",
    )
    output.result_status = "Success"
    output.result_priority = "HIGH"
    output.result_summary = "1 brute force from 172.16.51.224"
    output.result_markdown = textwrap.dedent(
        """
        #### Brute Force Analyzer

        ##### Brute Force Summary for 172.16.51.224
        - Successful brute force on 2022-12-26 23:26:14 as Administrator

        ###### 172.16.51.224 Summary
        - IP first seen on 2022-12-26 23:25:49
        - IP last seen on 2022-12-26 23:26:14
        - First successful auth on 2022-12-26 23:26:14
        - First successful source IP: 172.16.51.224
        - First successful username: Administrator

        ###### Top Usernames
        - Administrator: 26"""
    )

    return str(output)


def expected_bruteforce_output_2() -> str:
    """Returns brute force output."""
    output = AnalyzerOutput(
        analyzer_id="analyzer.bruteforce.windows",
        analyzer_name="Windows BruteForce Analyzer",
    )
    output.result_status = "Success"
    output.result_priority = "LOW"
    output.result_summary = "No brute force activity"
    output.result_markdown = textwrap.dedent(
        """
        #### Brute Force Analyzer
        No brute force detected"""
    )

    return str(output)


def _create_success_events(datastore, config: dict, event_count: int = 1) -> None:
    """Creates successful Windows logon events"""
    event_id = config["event_id"]
    computer_name = config["computer_name"]
    timestamp = config["timestamp"]
    event_identifier = config["event_identifier"]
    event_record_id = config["event_record_id"]
    target_logon_id = config["target_logon_id"]

    for _ in range(event_count):
        win_event = {
            "source_name": "Microsoft-Windows-Security-Auditing",
            "computer_name": computer_name,
            "event_identifier": event_identifier,
        }

        dt = datetime.utcfromtimestamp(timestamp / 1000000)
        win_event["datetime"] = dt.astimezone(timezone.utc).isoformat()

        timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        xml_string = f"""
        <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
            <System>
                <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{{54849625-5478-4994-A5BA-3E3B0328C30D}}"/>
                <EventID>4624</EventID>
                <Version>2</Version>
                <Level>0</Level>
                <Task>12544</Task>
                <Opcode>0</Opcode>
                <Keywords>0x8020000000000000</Keywords>
                <TimeCreated SystemTime="{timestamp_string}"/>
                <EventRecordID>{event_record_id}</EventRecordID>
                <Correlation ActivityID="{{BBC53E82-1C88-0000-AB3E-C5BB881CD901}}"/>
                <Execution ProcessID="540" ThreadID="2684"/>
                <Channel>Security</Channel>
                <Computer>WIN-EFPSBTQIU5K</Computer>
                <Security/>
            </System>
            <EventData>
                <Data Name="SubjectUserSid">S-1-0-0</Data>
                <Data Name="SubjectUserName">-</Data>
                <Data Name="SubjectDomainName">-</Data>
                <Data Name="SubjectLogonId">0x0000000000000000</Data>
                <Data Name="TargetUserSid">S-1-5-21-4266454899-2378428059-188620673-500</Data>
                <Data Name="TargetUserName">Administrator</Data>
                <Data Name="TargetDomainName">WIN-EFPSBTQIU5K</Data>
                <Data Name="TargetLogonId">{target_logon_id:#0{16}x}</Data>
                <Data Name="LogonType">3</Data>
                <Data Name="LogonProcessName">NtLmSsp </Data>
                <Data Name="AuthenticationPackageName">NTLM</Data>
                <Data Name="WorkstationName">kali</Data>
                <Data Name="LogonGuid">{{00000000-0000-0000-0000-000000000000}}</Data>
                <Data Name="TransmittedServices">-</Data>
                <Data Name="LmPackageName">NTLM V2</Data>
                <Data Name="KeyLength">128</Data>
                <Data Name="ProcessId">0x0000000000000000</Data>
                <Data Name="ProcessName">-</Data>
                <Data Name="IpAddress">172.16.51.224</Data>
                <Data Name="IpPort">0</Data>
                <Data Name="ImpersonationLevel">%%1833</Data>
                <Data Name="RestrictedAdminMode">-</Data>
                <Data Name="TargetOutboundUserName">-</Data>
                <Data Name="TargetOutboundDomainName">-</Data>
                <Data Name="VirtualAccount">%%1843</Data>
                <Data Name="TargetLinkedLogonId">0x0000000000000000</Data>
                <Data Name="ElevatedToken">%%1842</Data>
            </EventData>
        </Event>
        """
        win_event["xml_string"] = xml_string
        _create_eventObj(datastore, event_id, timestamp, win_event)

        event_id += 1
        timestamp += 1000000
        event_record_id += 1
        target_logon_id += 1


def _create_failed_events(datastore, config: dict, event_count: int = 1) -> None:
    """Creates failed events."""
    event_id = config["event_id"]
    computer_name = config["computer_name"]
    timestamp = config["timestamp"]
    event_identifier = config["event_identifier"]
    event_record_id = config["event_record_id"]
    port = config["port"]

    for _ in range(event_count):
        win_event = {
            "source_name": "Microsoft-Windows-Security-Auditing",
            "computer_name": computer_name,
            "event_identifier": event_identifier,
        }

        dt = datetime.utcfromtimestamp(timestamp / 1000000)
        win_event["datetime"] = dt.astimezone(timezone.utc).isoformat()

        timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        xml_string = f"""
            <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
                <System>
                    <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{{54849625-5478-4994-A5BA-3E3B0328C30D}}"/>
                    <EventID>4625</EventID>
                    <Version>0</Version>
                    <Level>0</Level>
                    <Task>12544</Task>
                    <Opcode>0</Opcode>
                    <Keywords>0x8010000000000000</Keywords>
                    <TimeCreated SystemTime="{timestamp_string}"/>
                    <EventRecordID>{event_record_id}</EventRecordID>
                    <Correlation ActivityID="{{2A4DC290-1A12-0000-B9C2-4D2A121AD901}}"/>
                    <Execution ProcessID="540" ThreadID="3340"/>
                    <Channel>Security</Channel>
                    <Computer>WIN-EFPSBTQIU5K</Computer>
                    <Security/>
                </System>
                <EventData>
                    <Data Name="SubjectUserSid">S-1-0-0</Data>
                    <Data Name="SubjectUserName">-</Data>
                    <Data Name="SubjectDomainName">-</Data>
                    <Data Name="SubjectLogonId">0x0000000000000000</Data>
                    <Data Name="TargetUserSid">S-1-0-0</Data>
                    <Data Name="TargetUserName">Administrator</Data>
                    <Data Name="TargetDomainName"/>
                    <Data Name="Status">0xc000006d</Data>
                    <Data Name="FailureReason">%%2313</Data>
                    <Data Name="SubStatus">0xc0000064</Data>
                    <Data Name="LogonType">3</Data>
                    <Data Name="LogonProcessName">NtLmSsp </Data>
                    <Data Name="AuthenticationPackageName">NTLM</Data>
                    <Data Name="WorkstationName">\\172.16.51.224</Data>
                    <Data Name="TransmittedServices">-</Data>
                    <Data Name="LmPackageName">-</Data>
                    <Data Name="KeyLength">0</Data>
                    <Data Name="ProcessId">0x0000000000000000</Data>
                    <Data Name="ProcessName">-</Data>
                    <Data Name="IpAddress">172.16.51.224</Data>
                    <Data Name="IpPort">{port}</Data>
                </EventData>
            </Event>"""
        win_event["xml_string"] = xml_string

        _create_eventObj(datastore, event_id, timestamp, win_event)

        event_id += 1
        timestamp += 1000000
        event_record_id += 1
        port += 1


def _create_logout_events(datastore, config: dict, event_count: int = 1) -> None:
    """ "Creates logout events."""
    event_id = config["event_id"]
    computer_name = config["computer_name"]
    timestamp = config["timestamp"]
    event_identifier = config["event_identifier"]
    event_record_id = config["event_record_id"]
    target_logon_id = config["target_logon_id"]

    for _ in range(event_count):
        win_event = {
            "source_name": "Microsoft-Windows-Security-Auditing",
            "computer_name": computer_name,
            "event_identifier": event_identifier,
        }

        dt = datetime.utcfromtimestamp(timestamp / 1000000)
        win_event["datetime"] = dt.astimezone(timezone.utc).isoformat()

        timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        xml_string = f"""
        <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
            <System>
                <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{{54849625-5478-4994-A5BA-3E3B0328C30D}}"/>
                <EventID>4634</EventID>
                <Version>0</Version>
                <Level>0</Level>
                <Task>12545</Task>
                <Opcode>0</Opcode>
                <Keywords>0x8020000000000000</Keywords>
                <TimeCreated SystemTime="{timestamp_string}"/>
                <EventRecordID>{event_record_id}</EventRecordID>
                <Correlation/>
                <Execution ProcessID="540" ThreadID="2672"/>
                <Channel>Security</Channel>
                <Computer>WIN-EFPSBTQIU5K</Computer>
                <Security/>
            </System>
            <EventData>
                <Data Name="TargetUserSid">S-1-5-21-4266454899-2378428059-188620673-500</Data>
                <Data Name="TargetUserName">Administrator</Data>
                <Data Name="TargetDomainName">WIN-EFPSBTQIU5K</Data>
                <Data Name="TargetLogonId">{target_logon_id:#0{16}x}</Data>
                <Data Name="LogonType">3</Data>
            </EventData>
            </Event>
            """
        win_event["xml_string"] = xml_string
        _create_eventObj(datastore, event_id, timestamp, win_event)

        event_id += 1
        timestamp += 1000000
        target_logon_id += 1


def _create_mock_event(datastore, failed_events=25, success_events=1, logout_event=1):
    """Create mock brute force events."""

    event_id = 0
    timestamp = 1672097149681987
    computer_name = "WIN-EFPSBTQIU5K"
    event_record_id = 413449
    port = 50224

    # Failed login events
    for _ in range(failed_events):
        win_event = {
            "source_name": "Microsoft-Windows-Security-Auditing",
            "computer_name": computer_name,
            "event_identifier": 4625,
        }

        dt = datetime.utcfromtimestamp(timestamp / 1000000)
        win_event["datetime"] = dt.astimezone(timezone.utc).isoformat()

        timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        xml_string = f"""
            <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
                <System>
                    <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{{54849625-5478-4994-A5BA-3E3B0328C30D}}"/>
                    <EventID>4625</EventID>
                    <Version>0</Version>
                    <Level>0</Level>
                    <Task>12544</Task>
                    <Opcode>0</Opcode>
                    <Keywords>0x8010000000000000</Keywords>
                    <TimeCreated SystemTime="{timestamp_string}"/>
                    <EventRecordID>{event_record_id}</EventRecordID>
                    <Correlation ActivityID="{{2A4DC290-1A12-0000-B9C2-4D2A121AD901}}"/>
                    <Execution ProcessID="540" ThreadID="3340"/>
                    <Channel>Security</Channel>
                    <Computer>WIN-EFPSBTQIU5K</Computer>
                    <Security/>
                </System>
                <EventData>
                    <Data Name="SubjectUserSid">S-1-0-0</Data>
                    <Data Name="SubjectUserName">-</Data>
                    <Data Name="SubjectDomainName">-</Data>
                    <Data Name="SubjectLogonId">0x0000000000000000</Data>
                    <Data Name="TargetUserSid">S-1-0-0</Data>
                    <Data Name="TargetUserName">Administrator</Data>
                    <Data Name="TargetDomainName"/>
                    <Data Name="Status">0xc000006d</Data>
                    <Data Name="FailureReason">%%2313</Data>
                    <Data Name="SubStatus">0xc0000064</Data>
                    <Data Name="LogonType">3</Data>
                    <Data Name="LogonProcessName">NtLmSsp </Data>
                    <Data Name="AuthenticationPackageName">NTLM</Data>
                    <Data Name="WorkstationName">\\172.16.51.224</Data>
                    <Data Name="TransmittedServices">-</Data>
                    <Data Name="LmPackageName">-</Data>
                    <Data Name="KeyLength">0</Data>
                    <Data Name="ProcessId">0x0000000000000000</Data>
                    <Data Name="ProcessName">-</Data>
                    <Data Name="IpAddress">172.16.51.224</Data>
                    <Data Name="IpPort">{port}</Data>
                </EventData>
            </Event>"""
        win_event["xml_string"] = xml_string

        _create_eventObj(datastore, event_id, timestamp, win_event)

        timestamp += 1000000
        event_id += 1
        event_record_id += 1
        port += 1

    # Successful login event
    target_logon_id = 0x00000000005C338A
    for _ in range(success_events):
        win_event = {
            "source_name": "Microsoft-Windows-Security-Auditing",
            "computer_name": computer_name,
            "event_identifier": 4624,
        }

        dt = datetime.utcfromtimestamp(timestamp / 1000000)
        win_event["datetime"] = dt.astimezone(timezone.utc).isoformat()

        timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        xml_string = f"""
        <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
            <System>
                <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{{54849625-5478-4994-A5BA-3E3B0328C30D}}"/>
                <EventID>4624</EventID>
                <Version>2</Version>
                <Level>0</Level>
                <Task>12544</Task>
                <Opcode>0</Opcode>
                <Keywords>0x8020000000000000</Keywords>
                <TimeCreated SystemTime="{timestamp_string}"/>
                <EventRecordID>{event_record_id}</EventRecordID>
                <Correlation ActivityID="{{BBC53E82-1C88-0000-AB3E-C5BB881CD901}}"/>
                <Execution ProcessID="540" ThreadID="2684"/>
                <Channel>Security</Channel>
                <Computer>WIN-EFPSBTQIU5K</Computer>
                <Security/>
            </System>
            <EventData>
                <Data Name="SubjectUserSid">S-1-0-0</Data>
                <Data Name="SubjectUserName">-</Data>
                <Data Name="SubjectDomainName">-</Data>
                <Data Name="SubjectLogonId">0x0000000000000000</Data>
                <Data Name="TargetUserSid">S-1-5-21-4266454899-2378428059-188620673-500</Data>
                <Data Name="TargetUserName">Administrator</Data>
                <Data Name="TargetDomainName">WIN-EFPSBTQIU5K</Data>
                <Data Name="TargetLogonId">{target_logon_id:#0{16}x}</Data>
                <Data Name="LogonType">3</Data>
                <Data Name="LogonProcessName">NtLmSsp </Data>
                <Data Name="AuthenticationPackageName">NTLM</Data>
                <Data Name="WorkstationName">kali</Data>
                <Data Name="LogonGuid">{{00000000-0000-0000-0000-000000000000}}</Data>
                <Data Name="TransmittedServices">-</Data>
                <Data Name="LmPackageName">NTLM V2</Data>
                <Data Name="KeyLength">128</Data>
                <Data Name="ProcessId">0x0000000000000000</Data>
                <Data Name="ProcessName">-</Data>
                <Data Name="IpAddress">172.16.51.224</Data>
                <Data Name="IpPort">0</Data>
                <Data Name="ImpersonationLevel">%%1833</Data>
                <Data Name="RestrictedAdminMode">-</Data>
                <Data Name="TargetOutboundUserName">-</Data>
                <Data Name="TargetOutboundDomainName">-</Data>
                <Data Name="VirtualAccount">%%1843</Data>
                <Data Name="TargetLinkedLogonId">0x0000000000000000</Data>
                <Data Name="ElevatedToken">%%1842</Data>
            </EventData>
        </Event>
        """
        win_event["xml_string"] = xml_string
        _create_eventObj(datastore, event_id, timestamp, win_event)

        event_id += 1
        timestamp += 1000000
        event_record_id += 1
        port += 1
        target_logon_id += 1

    # Logout event
    target_logon_id = 0x00000000005C338A
    for _ in range(logout_event):
        win_event = {
            "source_name": "Microsoft-Windows-Security-Auditing",
            "computer_name": computer_name,
            "event_identifier": 4634,
        }

        dt = datetime.utcfromtimestamp(timestamp / 1000000)
        win_event["datetime"] = dt.astimezone(timezone.utc).isoformat()

        timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        xml_string = f"""
        <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
            <System>
                <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{{54849625-5478-4994-A5BA-3E3B0328C30D}}"/>
                <EventID>4634</EventID>
                <Version>0</Version>
                <Level>0</Level>
                <Task>12545</Task>
                <Opcode>0</Opcode>
                <Keywords>0x8020000000000000</Keywords>
                <TimeCreated SystemTime="{timestamp_string}"/>
                <EventRecordID>{event_record_id}</EventRecordID>
                <Correlation/>
                <Execution ProcessID="540" ThreadID="2672"/>
                <Channel>Security</Channel>
                <Computer>WIN-EFPSBTQIU5K</Computer>
                <Security/>
            </System>
            <EventData>
                <Data Name="TargetUserSid">S-1-5-21-4266454899-2378428059-188620673-500</Data>
                <Data Name="TargetUserName">Administrator</Data>
                <Data Name="TargetDomainName">WIN-EFPSBTQIU5K</Data>
                <Data Name="TargetLogonId">{target_logon_id:#0{16}x}</Data>
                <Data Name="LogonType">3</Data>
            </EventData>
            </Event>
            """
        win_event["xml_string"] = xml_string
        _create_eventObj(datastore, event_id, timestamp, win_event)

        target_logon_id += 1


class TestWindowsLoginBruteForcePlugin(BaseTest):
    """Tests WindowsLoginBruteForcePlugin class."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_parse_xml_string_4624(self):
        """Test method _parse_xml_string."""
        xml_string = """
        <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
            <System>
                <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{54849625-5478-4994-A5BA-3E3B0328C30D}"/>
                <EventID>4624</EventID>
                <Version>2</Version>
                <Level>0</Level>
                <Task>12544</Task>
                <Opcode>0</Opcode>
                <Keywords>0x8020000000000000</Keywords>
                <TimeCreated SystemTime="2022-12-30T19:44:05.076327400Z"/>
                <EventRecordID>76409</EventRecordID>
                <Correlation ActivityID="{9E5D31B1-1C1E-0000-9A32-5D9E1E1CD901}"/>
                <Execution ProcessID="616" ThreadID="7176"/>
                <Channel>Security</Channel>
                <Computer>WIN-VQB2KAEFA34</Computer>
                <Security/>
            </System>
            <EventData>
                <Data Name="SubjectUserSid">S-1-0-0</Data>
                <Data Name="SubjectUserName">-</Data>
                <Data Name="SubjectDomainName">-</Data>
                <Data Name="SubjectLogonId">0x0000000000000000</Data>
                <Data Name="TargetUserSid">S-1-5-21-2217721431-990694525-1842946922-500</Data>
                <Data Name="TargetUserName">Administrator</Data>
                <Data Name="TargetDomainName">WIN-VQB2KAEFA34</Data>
                <Data Name="TargetLogonId">0x0000000001e69eb6</Data>
                <Data Name="LogonType">3</Data>
                <Data Name="LogonProcessName">NtLmSsp </Data>
                <Data Name="AuthenticationPackageName">NTLM</Data>
                <Data Name="WorkstationName">kali</Data>
                <Data Name="LogonGuid">{00000000-0000-0000-0000-000000000000}</Data>
                <Data Name="TransmittedServices">-</Data>
                <Data Name="LmPackageName">NTLM V2</Data>
                <Data Name="KeyLength">128</Data>
                <Data Name="ProcessId">0x0000000000000000</Data>
                <Data Name="ProcessName">-</Data>
                <Data Name="IpAddress">192.168.40.23</Data>
                <Data Name="IpPort">0</Data>
                <Data Name="ImpersonationLevel">%%1833</Data>
                <Data Name="RestrictedAdminMode">-</Data>
                <Data Name="TargetOutboundUserName">-</Data>
                <Data Name="TargetOutboundDomainName">-</Data>
                <Data Name="VirtualAccount">%%1843</Data>
                <Data Name="TargetLinkedLogonId">0x0000000000000000</Data>
                <Data Name="ElevatedToken">%%1842</Data>
            </EventData>
        </Event>"""
        plugin = WindowsLoginBruteForcePlugin(index_name="test_index", sketch_id=1)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        _create_mock_event(datastore)

        eventdata = plugin.parse_xml_string(xml_string)
        expected_eventdata = expected_eventdata_4624()
        self.assertDictEqual(expected_eventdata.__dict__, eventdata.__dict__)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_parse_xml_string_4625(self):
        """ "Test parsing failed logon event."""
        xml_string = """
        <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
            <System>
                <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{54849625-5478-4994-A5BA-3E3B0328C30D}"/>
                <EventID>4625</EventID>
                <Version>0</Version>
                <Level>0</Level>
                <Task>12544</Task>
                <Opcode>0</Opcode>
                <Keywords>0x8010000000000000</Keywords>
                <TimeCreated SystemTime="2022-12-26T21:38:53.000500000Z"/>
                <EventRecordID>1210417</EventRecordID>
                <Correlation/>
                <Execution ProcessID="508" ThreadID="1304"/>
                <Channel>Security</Channel>
                <Computer>WIN-FQ1I2JM28LH</Computer>
                <Security/>
            </System>
            <EventData>
                <Data Name="SubjectUserSid">S-1-0-0</Data>
                <Data Name="SubjectUserName">-</Data>
                <Data Name="SubjectDomainName">-</Data>
                <Data Name="SubjectLogonId">0x0000000000000000</Data>
                <Data Name="TargetUserSid">S-1-0-0</Data>
                <Data Name="TargetUserName">administrator</Data>
                <Data Name="TargetDomainName"/>
                <Data Name="Status">0xc000006d</Data>
                <Data Name="FailureReason">%%2313</Data>
                <Data Name="SubStatus">0xc000006a</Data>
                <Data Name="LogonType">3</Data>
                <Data Name="LogonProcessName">NtLmSsp </Data>
                <Data Name="AuthenticationPackageName">NTLM</Data>
                <Data Name="WorkstationName"/>
                <Data Name="TransmittedServices">-</Data>
                <Data Name="LmPackageName">-</Data>
                <Data Name="KeyLength">0</Data>
                <Data Name="ProcessId">0x0000000000000000</Data>
                <Data Name="ProcessName">-</Data>
                <Data Name="IpAddress">192.168.40.23</Data>
                <Data Name="IpPort">46658</Data>
            </EventData>
        </Event>"""
        plugin = WindowsLoginBruteForcePlugin(index_name="test_index", sketch_id=1)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        _create_mock_event(datastore)

        eventdata = plugin.parse_xml_string(xml_string)
        expected_eventdata = expected_eventdata_4625()
        self.assertDictEqual(expected_eventdata.__dict__, eventdata.__dict__)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_parse_xml_string_4634(self):
        """Test parsing logoff event."""
        xml_string = """
        <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
            <System>
                <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{54849625-5478-4994-A5BA-3E3B0328C30D}"/>
                <EventID>4634</EventID>
                <Version>0</Version>
                <Level>0</Level>
                <Task>12545</Task>
                <Opcode>0</Opcode>
                <Keywords>0x8020000000000000</Keywords>
                <TimeCreated SystemTime="2022-12-30T19:44:05.962634300Z"/>
                <EventRecordID>76440</EventRecordID>
                <Correlation/>
                <Execution ProcessID="616" ThreadID="2592"/>
                <Channel>Security</Channel>
                <Computer>WIN-VQB2KAEFA34</Computer>
                <Security/>
            </System>
            <EventData>
                <Data Name="TargetUserSid">S-1-5-21-2217721431-990694525-1842946922-500</Data>
                <Data Name="TargetUserName">Administrator</Data>
                <Data Name="TargetDomainName">WIN-VQB2KAEFA34</Data>
                <Data Name="TargetLogonId">0x0000000001e69eb6</Data>
                <Data Name="LogonType">3</Data>
            </EventData>
        </Event>"""
        plugin = WindowsLoginBruteForcePlugin(index_name="test_index", sketch_id=1)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        _create_mock_event(datastore)

        eventdata = plugin.parse_xml_string(xml_string)
        expected_eventdata = expected_eventdata_4634()
        self.assertDictEqual(expected_eventdata.__dict__, eventdata.__dict__)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run(self):
        """Test run method."""
        index = "test_index"
        sketch_id = 1

        plugin = WindowsLoginBruteForcePlugin(index_name=index, sketch_id=sketch_id)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        _create_mock_event(
            datastore, failed_events=25, success_events=1, logout_event=1
        )

        output = plugin.run()
        json_output = json.loads(output)

        expected_output = expected_bruteforce_output()
        json_expected_output = json.loads(expected_output)
        self.assertDictEqual(json_expected_output, json_output)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run_2(self):
        """Test run method."""
        index = "test_index"
        sketch_id = 1

        plugin = WindowsLoginBruteForcePlugin(index_name=index, sketch_id=sketch_id)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        _create_mock_event(
            datastore, failed_events=10, success_events=1, logout_event=1
        )

        output = plugin.run()
        json_output = json.loads(output)

        expected_output = expected_bruteforce_output_2()
        json_expected_output = json.loads(expected_output)
        self.assertDictEqual(json_expected_output, json_output)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run_3(self):
        """Test run method."""
        index = "test_index"
        sketch_id = 1

        plugin = WindowsLoginBruteForcePlugin(index_name=index, sketch_id=sketch_id)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        config = {
            "event_id": 0,
            "timestamp": 1672097141681987,
            "computer_name": "WIN-EFPSBTQIU5K",
            "event_record_id": 413449,
            "port": 50224,
            "target_logon_id": 0x00000000005C3380,
            "event_identifier": 4624,
        }
        _create_success_events(datastore, config, event_count=4)

        config = {
            "event_id": 4,
            "timestamp": 1672097145681987,
            "computer_name": "WIN-EFPSBTQIU5K",
            "event_record_id": 413453,
            "port": 50324,
            "event_identifier": 4625,
        }
        _create_failed_events(datastore, config, event_count=26)

        config = {
            "event_id": 30,
            "timestamp": 167209724681987,
            "computer_name": "WIN-EFPSBTQIU5K",
            "event_record_id": 413549,
            "port": 50424,
            "target_logon_id": 0x00000000005C338A,
            "event_identifier": 4624,
        }
        _create_success_events(datastore, config, event_count=1)

        config = {
            "event_id": 30,
            "timestamp": 167209734681987,
            "computer_name": "WIN-EFPSBTQIU5K",
            "event_record_id": 413649,
            "port": 50424,
            "target_logon_id": 0x00000000005C338A,
            "event_identifier": 4634,
        }
        _create_logout_events(datastore, config, event_count=4)

        output = plugin.run()
        json_output = json.loads(output)

        expected_output = expected_bruteforce_output_2()
        json_expected_output = json.loads(expected_output)
        self.assertDictEqual(json_expected_output, json_output)
