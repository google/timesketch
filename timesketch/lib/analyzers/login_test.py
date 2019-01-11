"""Tests for LoginPlugin."""
from __future__ import unicode_literals

from timesketch.lib.analyzers import login
from timesketch.lib.testlib import BaseTest


class MockEvent(object):
    """Implements a mock Event object."""

    def __init__(self):
        """Initialize."""
        self.attributes = {}
        self.emojis = []
        self.tags = []

    def add_emojis(self, emojis):
        """Add emojis to event."""
        self.emojis.extend(emojis)

    def add_attributes(self, attribute_dict):
        """Add attributes to event."""
        for key, value in attribute_dict.iteritems():
            if key in self.attributes:
                raise KeyError('key already defined.')
            self.attributes[key] = value

    def add_tags(self, tags):
        """Add tags to the event."""
        self.tags.extend(tags)


class TestLoginPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def test_parse_evtx_logon(self):
        """Test EVTX logon parsing."""
        event = MockEvent()
        string_list = []
        string_parsed = {}
        emoji = 'brosmildur'

        count = login.parse_evtx_logon_event(
            event, string_list, string_parsed, emoji)

        self.assertEquals(count, 0)

        string_list = [
            'S-1-5', '1', '2', '0x0034', 'S-1-5-5-4-54', 'secret_santa', '6',
            '7', '2', '9', '10', '11', '12', '13', '14', '15', '16', '17',
            '18', '19', '20', '21', '22']
        string_parsed = {
            'target_user_id': 'S-1-5-5-4-54',
            'target_user_name': 'secret_santa',
            'target_machine_name': 'rudolph'}
        emoji = 'brosmildur'

        count = login.parse_evtx_logon_event(
            event, string_list, string_parsed, emoji)

        self.assertEquals(count, 1)

        self.assertEquals(event.emojis, ['brosmildur'])
        self.assertEquals(event.tags, ['logon-event'])

        hostname = event.attributes.get('hostname', 'N/A')
        self.assertEquals(hostname, 'rudolph')

        session = event.attributes.get('session_id', 'N/A')
        self.assertEquals(session, string_list[3])

        logoff_type = event.attributes.get('logon_type', 'N/A')
        self.assertEquals(logoff_type, 'Interactive')

    def test_parse_evtx_logoff(self):
        """Test EVTX logoff parsing."""
        event = MockEvent()
        string_list = ['0', 'giljagaur', 'esja', '0x000342', '2']
        emoji = 'brosmildur'

        count = login.parse_evtx_logoff_event(
            event, string_list, emoji)

        self.assertEquals(count, 1)
        self.assertEquals(event.tags, ['logoff-event'])
        self.assertEquals(event.emojis, ['brosmildur'])

        username = event.attributes.get('username', 'N/A')
        self.assertEquals(username, string_list[1])

        session = event.attributes.get('session_id', 'N/A')
        self.assertEquals(session, string_list[3])

        logoff_type = event.attributes.get('logon_type', 'N/A')
        self.assertEquals(logoff_type, 'Interactive')
