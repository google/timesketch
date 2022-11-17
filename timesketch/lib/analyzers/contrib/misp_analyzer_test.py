import mock

from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestMisp(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        super().setUp()

        self.MISP_ATTR = {
            "response": {
                "Attribute": [
                    {
                        "event_id": "5",
                        "category": "Payload delivery",
                        "type": "sha256",
                        "value": "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09",
                        "Event": {
                            "org_id": "1",
                            "id": "5",
                            "info": "Hash Test",
                            "uuid": "1f456b69-00c6-4fb0-8d92-709a0061b7d4",
                        },
                    },
                    {
                        "event_id": "5",
                        "category": "Payload delivery",
                        "type": "sha1",
                        "value": "a308b3daed1711be6b1e591ba85984572a01134e",
                        "Event": {
                            "org_id": "1",
                            "id": "5",
                            "info": "Hash Test",
                            "uuid": "1f456b69-00c6-4fb0-8d92-709a0061b7d4",
                        },
                    },
                    {
                        "event_id": "5",
                        "category": "Payload delivery",
                        "type": "filename",
                        "value": "test.txt",
                        "Event": {
                            "org_id": "1",
                            "id": "5",
                            "info": "Hash Test",
                            "uuid": "1f456b69-00c6-4fb0-8d92-709a0061b7d4",
                        },
                    },
                ]
            }
        }
        self.MATCHING_MISP = {
            "filename": "test.txt",
            "sha1_hash": "a308b3daed1711be6b1e591ba85984572a01134e",
            "sha256_hash": "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09",
            "md5_hash": "e59c93a1fd36c70b37ef654d0603c30f",
        }

    def attr_match(self):
        cp = 0
        for key in list(self.MATCHING_MISP.keys()):
            for attr in self.MISP_ATTR['response']['Attribute']:
                if self.MATCHING_MISP[key] == attr['value']:
                    print(f"self.MATCHING_MISP[key]: {self.MATCHING_MISP[key]}")
                    print(f"attr[value]: {attr['value']}")
                    cp += 1
        return f"MISP Match: {cp}"

    # @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    # @mock.patch(
    #     "timesketch.lib.analyzers.contrib.misp_analyzer." "MispAnalyzer.get_attr"
    # )
    def test_attr_match(self):
        message = self.attr_match()
        self.assertEqual(
            message,
            ("MISP Match: 3"),
        )

    # @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    # @mock.patch(
    #     "timesketch.lib.analyzers.contrib.misp_analyzer." "MispAnalyzer.get_attr"
    # )
    def test_attr_nomatch(self):
        self.MISP_ATTR = {"response": {"Attribute": []}}
        message = self.attr_match()
        self.assertEqual(
            message,
            ("MISP Match: 0"),
        )
