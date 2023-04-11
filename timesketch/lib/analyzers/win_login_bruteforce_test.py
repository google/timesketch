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

from datetime import datetime

import logging
import json
import sys

import mock


from timesketch.lib.analyzers.analyzer_output import AnalyzerOutput
from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj
from timesketch.lib.analyzers.win_login_bruteforce import WindowsLoginBruteForcePlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

log = logging.getLogger("timesketch")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


def expected_successful_output() -> str:
    """Returns successful analyzer output."""
    output = AnalyzerOutput(
        analyzer_id="analyzer.bruteforce.windows",
        analyzer_name="Windows BruteForce Analyzer",
    )
    output.result_status = "Failed"
    output.result_priority = "LOW"
    output.result_summary = "Analyzer failed"
    output.result_markdown = ""

    return str(output)


def _create_mock_event(datastore):
    """Create mock brute force events."""
    fh = open("/tmp/events.xml", "w")

    event_id = 0
    timestamp = 1672097149681987
    timestamp_string = "2022-12-26T23:25:49.681986Z"
    computer_name = "WIN-EFPSBTQIU5K"
    event_identifier = 4625
    event_record_id = 413449
    port = 50224

    # Failed login events
    win_event = {
        "computer_name": computer_name,
        "event_identifier": event_identifier,
    }

    for _ in range(200):
        dt = datetime.utcfromtimestamp(timestamp / 1000000)
        timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        failed_xml_string = f"""
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

        win_event["xml_string"] = failed_xml_string

        fh.write(str(win_event) + "\n")

        _create_eventObj(datastore, event_id, timestamp, win_event)

        timestamp += 1000000
        event_id += 1
        event_record_id += 1
        port += 1

    # Successful login event
    timestamp += 2000000
    dt = datetime.utcfromtimestamp(timestamp / 1000000)
    timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    passed_xml_string = f"""
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
            <Data Name="TargetLogonId">0x00000000005c338a</Data>
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
    win_event["xml_string"] = passed_xml_string
    fh.write(passed_xml_string + "\n")
    _create_eventObj(datastore, event_id, timestamp, win_event)

    # Logout event
    timestamp += 10000000
    dt = datetime.utcfromtimestamp(timestamp / 1000000)
    timestamp_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    logout_xml_string = f"""
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
            <Data Name="TargetLogonId">0x00000000005c338a</Data>
            <Data Name="LogonType">3</Data>
        </EventData>
        </Event>
        """
    win_event["xml_string"] = logout_xml_string
    fh.write(logout_xml_string + "\n")
    _create_eventObj(datastore, event_id, timestamp, win_event)
    fh.close()


class TestWindowsLoginBruteForcePlugin(BaseTest):
    """Tests WindowsLoginBruteForcePlugin class."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run(self):
        """Test run method."""
        index = "test_index"
        sketch_id = 1

        plugin = WindowsLoginBruteForcePlugin(index_name=index, sketch_id=sketch_id)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        _create_mock_event(datastore)

        print(datastore)

        output = plugin.run()
        json_output = json.loads(output)

        print(f"\n\n\n{json_output}\n\n\n")

        expected_output = expected_successful_output()
        json_expected_output = json.loads(expected_output)
        self.assertDictEqual(json_expected_output, json_output)
