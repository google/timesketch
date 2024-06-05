"""Tests for OsshashdbLookupPlugin."""

from __future__ import unicode_literals

import copy
import logging
import json

from flask import current_app
import mock
import sqlalchemy

from timesketch.lib.analyzers import hashr_lookup
from timesketch.lib.testlib import BaseTest, MockDataStore


class TestHashRLookup(BaseTest):
    """Tests the functionality of the analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def setUp(self):
        """Setup for for running the hashr lookup analyzer tests."""
        super().setUp()
        self.analyzer = hashr_lookup.HashRLookup("test_index", 1)
        self.logger = logging.getLogger("timesketch.analyzers.hashR")

    @mock.patch.object(sqlalchemy, "create_engine", autospec=False)
    @mock.patch.object(sqlalchemy, "MetaData", autospec=True)
    @mock.patch.object(logging.Logger, "warning", autospec=True)
    @mock.patch.object(logging.Logger, "error", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    def test_connect_hashR_no_errors(
        self, mock_debug, mock_error, mock_warning, mock_meta_data, mock_create_engine
    ):
        """Test the connect_hashR function with no errors.

        Args:
            mock_debug: Mock object for the logger.debug function.
            mock_error: Mock object for the logger.error function.
            mock_warning: Mock objext for the logger.warning function.
            mock_meta_data: Mock object for the sqlalchemy meta_data function.
            mock_create_engine: Mock object for the sqlalchemy.create_engine
                                function.
        """
        current_app.config["HASHR_DB_USER"] = "hashR"
        current_app.config["HASHR_DB_PW"] = "hashR123"
        current_app.config["HASHR_DB_ADDR"] = "127.0.0.1"
        current_app.config["HASHR_DB_PORT"] = "5432"
        current_app.config["HASHR_DB_NAME"] = "hashRdb"
        current_app.config["HASHR_ADD_SOURCE_ATTRIBUTE"] = True
        current_app.config["HASHR_QUERY_BATCH_SIZE"] = 10000

        mock_create_engine().connect.return_value = True
        test_meta_data = mock.MagicMock()
        mock_meta_data.return_value = test_meta_data
        test_meta_data.tables = ["samples", "sources", "samples_sources"]

        test_conn = self.analyzer.connect_hashr()
        self.assertEqual(test_conn, True)
        mock_debug.assert_called_with(
            self.logger,
            "Successful connected to hashR postgress database: %s",
            "postgresql://hashR:***@127.0.0.1:5432/hashRdb",
        )
        mock_error.assert_not_called()
        mock_warning.assert_not_called()
        mock_create_engine.assert_called_with(
            "postgresql://hashR:hashR123@127.0.0.1:5432/hashRdb",
            connect_args={"connect_timeout": 10},
        )
        self.assertEqual(self.analyzer.query_batch_size, 10000)

    @mock.patch.object(sqlalchemy, "create_engine", autospec=True)
    @mock.patch.object(logging.Logger, "error", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    def test_connect_hashR_no_db_info(self, mock_debug, mock_error, mock_create_engine):
        """Test the connect_hashR function with missing connection information.

        Args:
            mock_debug: Mock object for the logger.debug function.
            mock_error: Mock object for the logger.error function.
            mock_create_engine: Mock object for the sqlalchemy.create_engine
                                function.
        """
        self.assertRaises(Exception, self.analyzer.connect_hashr)
        mock_debug.assert_not_called()
        mock_error.assert_not_called()
        mock_create_engine.assert_not_called()
        self.assertEqual(self.analyzer.query_batch_size, 50000)

    @mock.patch.object(sqlalchemy, "create_engine", autospec=False)
    @mock.patch.object(logging.Logger, "error", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    def test_connect_hashr_conn_error(self, mock_debug, mock_error, mock_create_engine):
        """Test the connect_hashr function simulating a connection error.

        Args:
            mock_debug: Mock object for the logger.debug function.
            mock_error: Mock object for the logger.error function.
            mock_create_engine: Mock object for the sqlalchemy.create_engine
                                function.
        """
        current_app.config["HASHR_DB_USER"] = "hashR"
        current_app.config["HASHR_DB_PW"] = "hashR123"
        current_app.config["HASHR_DB_ADDR"] = "127.0.0.2"
        current_app.config["HASHR_DB_PORT"] = "5432"
        current_app.config["HASHR_DB_NAME"] = "hashRdb"
        current_app.config["HASHR_ADD_SOURCE_ATTRIBUTE"] = True
        current_app.config["HASHR_QUERY_BATCH_SIZE"] = "50000"

        mock_create_engine().connect.side_effect = sqlalchemy.exc.OperationalError(
            statement=None, params=None, orig="Cannot connect to server!"
        )
        # self.analyzer.connect_hashr()
        self.assertRaisesRegex(
            Exception,
            "Connection to the hashR postgres database failed! "
            "-- Provided connection string:",
            self.analyzer.connect_hashr,
        )
        mock_create_engine.assert_called_with(
            "postgresql://hashR:hashR123@127.0.0.2:5432/hashRdb",
            connect_args={"connect_timeout": 10},
        )
        mock_debug.assert_not_called()
        self.assertEqual(self.analyzer.query_batch_size, 50000)
        self.assertTrue(
            (
                "Connection to the hashR postgres database failed! -- Provided "
                "connection string: \"%s\" -- Error message: %s', 'postgresql://"
                "hashR:***@127.0.0.2:5432/hashRdb', '(builtins.str) Cannot "
                "connect to server!\\n(Background on this error at:"
            )
            in str(mock_error.call_args_list)
        )

    @mock.patch.object(sqlalchemy, "select", autospec=True)
    @mock.patch.object(sqlalchemy, "MetaData", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    def test_check_against_hashr_matching_hashes_tags(
        self, mock_debug, mock_meta_data, mock_select
    ):
        """Test the check_against_hashr function with existing matches and tags only.

        Args:
            mock_debug: Mock object for the logger.debug function.
            mock_meta_data: Mock object for the sqlalchemy meta_data function.
            mock_select: Mock object for the sqlalchemy Select class.
        """
        test_input_hashes = [
            "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0",
            "ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542",
            "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d",
            "bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f",
            "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83",
            "40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651",
            "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af",
            "7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c",
            "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3",
            "2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc",
        ]

        test_db_return = [
            ("78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0",),
            ("960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d",),
            ("c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83",),
            ("7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af",),
            ("66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3",),
        ]

        expected_return = {
            "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0": {
                "TagsOnly"
            },
            "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d": {
                "TagsOnly"
            },
            "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83": {
                "TagsOnly"
            },
            "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af": {
                "TagsOnly"
            },
            "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3": {
                "TagsOnly"
            },
        }

        self.analyzer.query_batch_size = 4
        self.analyzer.add_source_attribute = False
        test_bind = mock.MagicMock()
        self.analyzer.hashr_conn = test_bind
        test_bind.connect().__enter__().execute.return_value = test_db_return
        test_meta_data = mock.MagicMock()
        mock_meta_data.return_value = test_meta_data

        test_output_hashes = self.analyzer.check_against_hashr(test_input_hashes)

        mock_meta_data.assert_called_with(bind=test_bind)
        mock_meta_data.reflect.assert_called_with(test_meta_data)
        mock_select.assert_has_calls(
            [
                mock.call([test_meta_data.tables.__getitem__().c.sha256]),
                mock.call().where(test_meta_data.tables.__getitem__().c.sha256.in_()),
                mock.call([test_meta_data.tables.__getitem__().c.sha256]),
                mock.call().where(test_meta_data.tables.__getitem__().c.sha256.in_()),
                mock.call([test_meta_data.tables.__getitem__().c.sha256]),
                mock.call().where(test_meta_data.tables.__getitem__().c.sha256.in_()),
            ]
        )
        mock_debug.assert_any_call(
            self.logger, "Found %d matching hashes in hashR DB.", 5
        )
        test_bind.dispose.assert_called_once()
        self.assertEqual(test_output_hashes, expected_return)

    @mock.patch.object(sqlalchemy, "select", autospec=True)
    @mock.patch.object(sqlalchemy, "MetaData", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    def test_check_against_hashr_matching_hashes_sources(
        self, mock_debug, mock_meta_data, mock_select
    ):
        """Test check_against_hashr function with matches + tags & attributes.

        Args:
            mock_debug: Mock object for the logger.debug function.
            mock_meta_data: Mock object for the sqlalchemy meta_data function.
            mock_select: Mock object for the sqlalchemy Select class.
        """
        test_input_hashes = [
            "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0",
            "ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542",
            "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d",
            "bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f",
            "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83",
            "40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651",
            "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af",
            "7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c",
            "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3",
            "2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc",
        ]

        expected_return = {
            "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0": {
                "Windows:Windows10Home-10.0-19041-1288sp",
                "WindowsServer:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp",
            },
            "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d": {
                "WindowsServer:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp"
            },
            "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83": {
                (
                    "WindowsPro:Windows10Home-10.0-19041-1288sp;"
                    "Windows10Pro-10.0-19041-1288sp"
                )
            },
            "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af": {
                "GCP:debian-cloud-debian-9-stretch-v20220621"
            },
            "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3": {
                "GCP:debian-cloud-debian-11-bullseye-arm64-v20220712"
            },
        }
        test_db_return = [
            (
                "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ["Windows10Home-10.0-19041-1288sp"],
                "Windows",
            ),
            (
                "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ["WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp"],
                "WindowsServer",
            ),
            (
                "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ["WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp"],
                "WindowsServer",
            ),
            (
                "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ["Windows10Home-10.0-19041-1288sp", "Windows10Pro-10.0-19041-1288sp"],
                "WindowsPro",
            ),
            (
                "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ["debian-cloud-debian-9-stretch-v20220621"],
                "GCP",
            ),
            (
                "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ["debian-cloud-debian-11-bullseye-arm64-v20220712"],
                "GCP",
            ),
        ]

        self.analyzer.query_batch_size = 4
        self.analyzer.add_source_attribute = True
        test_bind = mock.MagicMock()
        self.analyzer.hashr_conn = test_bind
        test_bind.connect().__enter__().execute.return_value = test_db_return
        test_meta_data = mock.MagicMock()
        mock_meta_data.return_value = test_meta_data

        test_output_hashes = self.analyzer.check_against_hashr(test_input_hashes)

        mock_meta_data.assert_called_with(bind=test_bind)
        mock_meta_data.reflect.assert_called_with(test_meta_data)
        mock_select.assert_has_calls(
            [
                mock.call(
                    [
                        test_meta_data.tables.__getitem__().c.sample_sha256,
                        test_meta_data.tables.__getitem__().c.source_sha256,
                        test_meta_data.tables.__getitem__().c.sourceid,
                        test_meta_data.tables.__getitem__().c.reponame,
                    ]
                ),
                mock.call().select_from(test_meta_data.tables.__getitem__().join()),
                mock.call()
                .select_from()
                .where(test_meta_data.tables.__getitem__().c.sample_sha256.in_()),
                mock.call(
                    [
                        test_meta_data.tables.__getitem__().c.sample_sha256,
                        test_meta_data.tables.__getitem__().c.source_sha256,
                        test_meta_data.tables.__getitem__().c.sourceid,
                        test_meta_data.tables.__getitem__().c.reponame,
                    ]
                ),
                mock.call().select_from(test_meta_data.tables.__getitem__().join()),
                mock.call()
                .select_from()
                .where(test_meta_data.tables.__getitem__().c.sample_sha256.in_()),
                mock.call(
                    [
                        test_meta_data.tables.__getitem__().c.sample_sha256,
                        test_meta_data.tables.__getitem__().c.source_sha256,
                        test_meta_data.tables.__getitem__().c.sourceid,
                        test_meta_data.tables.__getitem__().c.reponame,
                    ]
                ),
                mock.call().select_from(test_meta_data.tables.__getitem__().join()),
                mock.call()
                .select_from()
                .where(test_meta_data.tables.__getitem__().c.sample_sha256.in_()),
            ]
        )

        mock_debug.assert_any_call(
            self.logger, "Found %d matching hashes in hashR DB.", 5
        )
        test_bind.dispose.assert_called_once()
        self.assertEqual(test_output_hashes, expected_return)

    @mock.patch.object(sqlalchemy, "select", autospec=True)
    @mock.patch.object(sqlalchemy, "MetaData", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    def test_check_against_hashr_no_matches(
        self, mock_debug, mock_meta_data, _mock_select
    ):
        """Test the check_against_hashr function with no matching hashes.

        Args:
            mock_debug: Mock object for the logger.debug function.
            mock_meta_data: Mock object for the sqlalchemy meta_data function.
            _mock_select: Mock object for the sqlalchemy Select class.
        """
        test_input_hashes = [
            "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0",
            "ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542",
            "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d",
            "bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f",
            "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83",
            "40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651",
            "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af",
            "7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c",
            "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3",
            "2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc",
        ]

        test_db_return = []

        self.analyzer.query_batch_size = 4
        self.analyzer.add_source_attribute = True
        test_bind = mock.MagicMock()
        self.analyzer.hashr_conn = test_bind
        test_bind.connect().__enter__().execute.return_value = test_db_return
        test_meta_data = mock.MagicMock()
        mock_meta_data.return_value = test_meta_data

        test_output_hashes = self.analyzer.check_against_hashr(test_input_hashes)

        mock_debug.assert_any_call(
            self.logger, "Found %d matching hashes in hashR DB.", 0
        )
        self.assertEqual(test_output_hashes, {})

    def test_check_against_hashr_exception(self):
        """Test check_against_hashr function with wrong input."""
        self.assertRaisesRegex(
            Exception,
            "The check_against_hashR function only accepts "
            "type<list> as input. But type <class 'str'>"
            " was provided!",
            self.analyzer.check_against_hashr,
            "WrongInput",
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch.object(logging.Logger, "warning", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    @mock.patch.object(logging.Logger, "info", autospec=True)
    @mock.patch.object(hashr_lookup.HashRLookup, "connect_hashr", autospec=True)
    @mock.patch.object(hashr_lookup.HashRLookup, "check_against_hashr", autospec=True)
    def test_run_tags_only(
        self, mock_check, mock_connect, _mock_info, mock_debug, mock_warning
    ):
        """Test the run function with the flag add_source_attribute=False.

        Args:
            _mock_info: Unused mock object to catch info messages.
            mock_debug: Mock object for the logger.debug function.
            mock_warning: Mock object for the logger.warning function.
            mock_check: Mock object for the check_against_hashr function.
            mock_connect: Mock object for the connect_hashr function.
        """
        # pylint: disable=line-too-long
        test_input_hashes = [
            {
                "hash_sha256": "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0"
            },
            {
                "sha256": "ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542"
            },
            {
                "hash": "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d"
            },
            {
                "sha256_hash": "bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f"
            },
            {
                "sha256": "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83"
            },
            {
                "sha256_hash": "40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651"
            },
            {
                "hash": "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af"
            },
            {
                "hash_sha256": "7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c"
            },
            {
                "hash_sha256": "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3"
            },
            {
                "sha256": "2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc"
            },
            {"hash": "8bbd7976b2b86e1746494c98425e7830"},
            {
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
            {
                "sha265": "5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92"
            },
        ]

        expected_matching_hashes = [
            "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0",
            "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d",
            "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83",
            "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af",
            "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ]

        expected_result_message_one = json.dumps(
            {
                "platform": "timesketch",
                "analyzer_identifier": "hashr_lookup",
                "analyzer_name": "hashR lookup",
                "result_status": "SUCCESS",
                "result_priority": "NOTE",
                "result_summary": "Found a total of 13 events that contain a sha256 hash value - 6 / 11 unique hashes known in hashR - 6 events tagged - 1 entries were tagged as zerobyte files - 2 events raised an error",
                "platform_meta_data": {
                    "timesketch_instance": "https://localhost",
                    "sketch_id": 1,
                    "timeline_id": 1,
                    "created_tags": ["zerobyte-file", "known-hash"],
                },
                "result_markdown": "Found a total of 13 events that contain a sha256 hash value\n* 6 / 11 unique hashes known in hashR\n* 6 events tagged\n* 1 entries were tagged as zerobyte files\n* 2 events raised an error",
            }
        )

        expected_result_message_two = json.dumps(
            {
                "platform": "timesketch",
                "analyzer_identifier": "hashr_lookup",
                "analyzer_name": "hashR lookup",
                "result_status": "SUCCESS",
                "result_priority": "NOTE",
                "result_summary": "Found a total of 13 events that contain a sha256 hash value - 6 / 11 unique hashes known in hashR - 6 events tagged - 1 entries were tagged as zerobyte files - 2 events raised an error",
                "platform_meta_data": {
                    "timesketch_instance": "https://localhost",
                    "sketch_id": 1,
                    "timeline_id": 1,
                    "created_tags": ["known-hash", "zerobyte-file"],
                },
                "result_markdown": "Found a total of 13 events that contain a sha256 hash value\n* 6 / 11 unique hashes known in hashR\n* 6 events tagged\n* 1 entries were tagged as zerobyte files\n* 2 events raised an error",
            }
        )

        analyzer = hashr_lookup.HashRLookup("test_index", 1, 1)
        analyzer.datastore.client = mock.Mock()

        event_id = 0
        for entry in test_input_hashes:
            event = copy.deepcopy(MockDataStore.event_dict)
            event["_source"].update(entry)
            analyzer.datastore.import_event(
                "test_index", event["_source"], "{}".format(event_id)
            )
            event_id += 1

        mock_connect.return_value = True
        mock_check.return_value = expected_matching_hashes
        analyzer.add_source_attribute = False
        analyzer.unique_known_hash_counter = 5
        result_message = analyzer.run()
        self.assertIn(
            result_message, [expected_result_message_one, expected_result_message_two]
        )
        mock_warning.assert_any_call(
            self.logger,
            "The extracted hash does not match the required lenght (64) of "
            "a SHA256 hash. Skipping this event! Hash: %s - Lenght: %d",
            "8bbd7976b2b86e1746494c98425e7830",
            32,
        )
        self.assertTrue(
            "No matching field with a hash found in this event! -- Event Source:"
            in str(mock_warning.call_args_list)
            and "5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92"
            in str(mock_warning.call_args_list)
        )
        mock_debug.assert_any_call(self.logger, "Start adding tags to events.")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch.object(logging.Logger, "warning", autospec=True)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    @mock.patch.object(logging.Logger, "info", autospec=True)
    @mock.patch.object(hashr_lookup.HashRLookup, "connect_hashr", autospec=True)
    @mock.patch.object(hashr_lookup.HashRLookup, "check_against_hashr", autospec=True)
    def test_run_tags_and_sources(
        self, mock_check, mock_connect, _mock_info, mock_debug, mock_warning
    ):
        """Test the run function with the flag add_source_attribute=True.

        Args:
            _mock_info: Unused mock object to catch info messages.
            mock_debug: Mock object for the logger.debug function.
            mock_warning: Mock object for the logger.warning function.
            mock_check: Mock object for the check_against_hashr function.
            mock_connect: Mock object for the connect_hashr function.
        """
        # pylint: disable=line-too-long
        test_input_hashes = [
            {
                "hash_sha256": "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0"
            },
            {
                "sha256": "ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542"
            },
            {
                "hash": "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d"
            },
            {
                "sha256_hash": "bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f"
            },
            {
                "sha256": "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83"
            },
            {
                "sha256_hash": "40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651"
            },
            {
                "hash": "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af"
            },
            {
                "hash_sha256": "7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c"
            },
            {
                "hash_sha256": "66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3"
            },
            {
                "sha256": "2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc"
            },
            {"hash": "8bbd7976b2b86e1746494c98425e7830"},
            {
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
            {
                "sha265": "5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92"
            },
        ]

        expected_matching_hashes = {
            "78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0": [
                "Windows:Windows10Home-10.0-19041-1288sp",
                "WindowsServer:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp",
            ],
            "960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d": [
                "Windows:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp"
            ],
            "c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83": [
                "WindowsPro:Windows10Home-10.0-19041-1288sp",
                "WindowsPro:Windows10Pro-10.0-19041-1288sp",
            ],
            "7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af": [
                "GCP:debian-cloud-debian-9-stretch-v20220621"
            ],
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": [
                "GCP:debian-cloud-debian-11-bullseye-arm64-v20220712"
            ],
        }

        expected_result_message_one = json.dumps(
            {
                "platform": "timesketch",
                "analyzer_identifier": "hashr_lookup",
                "analyzer_name": "hashR lookup",
                "result_status": "SUCCESS",
                "result_priority": "NOTE",
                "result_summary": "Found a total of 13 events that contain a sha256 hash value - 5 / 11 unique hashes known in hashR - 5 events tagged - 1 entries were tagged as zerobyte files - 2 events raised an error",
                "platform_meta_data": {
                    "timesketch_instance": "https://localhost",
                    "sketch_id": 1,
                    "timeline_id": 1,
                    "created_tags": ["zerobyte-file", "known-hash"],
                    "created_attributes": ["hashR_sample_sources"],
                },
                "result_markdown": "Found a total of 13 events that contain a sha256 hash value\n* 5 / 11 unique hashes known in hashR\n* 5 events tagged\n* 1 entries were tagged as zerobyte files\n* 2 events raised an error",
            }
        )

        expected_result_message_two = json.dumps(
            {
                "platform": "timesketch",
                "analyzer_identifier": "hashr_lookup",
                "analyzer_name": "hashR lookup",
                "result_status": "SUCCESS",
                "result_priority": "NOTE",
                "result_summary": "Found a total of 13 events that contain a sha256 hash value - 5 / 11 unique hashes known in hashR - 5 events tagged - 1 entries were tagged as zerobyte files - 2 events raised an error",
                "platform_meta_data": {
                    "timesketch_instance": "https://localhost",
                    "sketch_id": 1,
                    "timeline_id": 1,
                    "created_tags": ["known-hash", "zerobyte-file"],
                    "created_attributes": ["hashR_sample_sources"],
                },
                "result_markdown": "Found a total of 13 events that contain a sha256 hash value\n* 5 / 11 unique hashes known in hashR\n* 5 events tagged\n* 1 entries were tagged as zerobyte files\n* 2 events raised an error",
            }
        )

        analyzer = hashr_lookup.HashRLookup("test_index", 1, 1)
        analyzer.datastore.client = mock.Mock()

        event_id = 0
        for entry in test_input_hashes:
            event = copy.deepcopy(MockDataStore.event_dict)
            event["_source"].update(entry)
            analyzer.datastore.import_event(
                "test_index", event["_source"], "{}".format(event_id)
            )
            event_id += 1

        mock_connect.return_value = True
        mock_check.return_value = expected_matching_hashes
        analyzer.add_source_attribute = True
        analyzer.unique_known_hash_counter = 5

        result_message = analyzer.run()
        self.assertIn(
            result_message, [expected_result_message_one, expected_result_message_two]
        )
        mock_warning.assert_any_call(
            self.logger,
            "The extracted hash does not match the required lenght (64) of "
            "a SHA256 hash. Skipping this event! Hash: %s - Lenght: %d",
            "8bbd7976b2b86e1746494c98425e7830",
            32,
        )
        self.assertTrue(
            "No matching field with a hash found in this event! -- Event Source:"
            in str(mock_warning.call_args_list)
            and "5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92"
            in str(mock_warning.call_args_list)
        )
        mock_debug.assert_any_call(
            self.logger, "Start adding tags and attributes to events."
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch.object(logging.Logger, "debug", autospec=True)
    @mock.patch.object(hashr_lookup.HashRLookup, "connect_hashr", autospec=True)
    def test_run_no_hashes(self, mock_connect, _mock_debug):
        """Test the run function with no hashes in the events.

        Args:
            _mock_debug: Unused mock object for the logger.debug function.
            mock_connect: Mock object for the connect_hashr function.
        """
        analyzer = hashr_lookup.HashRLookup("test_index", 1, 1)
        analyzer.datastore.client = mock.Mock()

        expected_result_message = json.dumps(
            {
                "platform": "timesketch",
                "analyzer_identifier": "hashr_lookup",
                "analyzer_name": "hashR lookup",
                "result_status": "SUCCESS",
                "result_priority": "NOTE",
                "result_summary": (
                    "This timeline does not contain any fields with a sha256 hash."
                ),
                "platform_meta_data": {
                    "timesketch_instance": "https://localhost",
                    "sketch_id": 1,
                    "timeline_id": 1,
                },
            }
        )

        mock_connect.return_value = True
        analyzer.add_source_attribute = True

        result_message = analyzer.run()
        self.assertEqual(result_message, expected_result_message)

    def test_process_event(self):
        """Test the process_event function with no special cases."""
        event = mock.MagicMock()
        sources = [
            "WindowsPro:Windows10Home-10.0-19041-1288sp",
            "WindowsPro:Windows10Pro-10.0-19041-1288sp",
        ]
        hash_value = "5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92"

        self.analyzer.annotate_event(hash_value, sources, event)
        self.assertEqual(self.analyzer.zerobyte_file_counter, 0)
        event.add_tags.assert_called_with(["known-hash"])
        event.add_attributes.assert_called_with(
            {
                "hashR_sample_sources": [
                    "WindowsPro:Windows10Home-10.0-19041-1288sp",
                    "WindowsPro:Windows10Pro-10.0-19041-1288sp",
                ]
            }
        )
        event.commit.assert_called_once()

    def test_process_event_zerobytefile(self):
        """Test the process_event function with a zyrobyte hash."""
        event = mock.MagicMock()
        sources = [
            "WindowsPro:Windows10Home-10.0-19041-1288sp",
            "WindowsPro:Windows10Pro-10.0-19041-1288sp",
        ]
        hash_value = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        self.analyzer.annotate_event(hash_value, sources, event)
        self.assertEqual(self.analyzer.zerobyte_file_counter, 1)
        event.add_tags.assert_called_with(["known-hash", "zerobyte-file"])
        event.add_attributes.assert_not_called()
        event.commit.assert_called_once()
