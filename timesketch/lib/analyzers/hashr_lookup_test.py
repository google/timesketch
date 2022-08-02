"""Tests for OsshashdbLookupPlugin."""
from __future__ import unicode_literals

import copy
import logging

from flask import current_app
import mock
import sqlalchemy

from timesketch.lib.analyzers import hashr_lookup
from timesketch.lib.testlib import BaseTest, MockDataStore


class TestHashRLookupPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        """Setup for for running the hashr lookup analyzer tests."""
        super().setUp()
        self.analyzer = hashr_lookup.HashRLookupSketchPlugin('test_index', 1)
        self.logger = logging.getLogger('timesketch.analyzers.hashR')

    @mock.patch.object(sqlalchemy, 'create_engine', autospec=True)
    @mock.patch.object(logging.Logger, 'error', autospec=True)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    def test_connect_hashR_no_errors(self, mock_info, mock_error,
                                     mock_create_engine):
        """Test the connect_hashR function with no introduced errors.

        Args:
            mock_info: Mock object for the logger.info function.
            mock_error: Mock object for the logger.error function.
            mock_create_engine: Mock object for the sqlalchemy.create_engine
                                function.
        """
        current_app.config['HASHR_DB_USER'] = 'hashR'
        current_app.config['HASHR_DB_PW'] = 'hashR123'
        current_app.config['HASHR_DB_ADDR'] = '127.0.0.1'
        current_app.config['HASHR_DB_PORT'] = '5432'
        current_app.config['HASHR_DB_NAME'] = 'hashRdb'
        current_app.config['HASHR_ADD_SOURCE_ATTRIBUTE'] = True

        mock_create_engine().connect.return_value = True
        test_conn = self.analyzer.connect_hashR()
        self.assertEqual(test_conn, True)
        mock_info.assert_called_with(
            self.logger, 'Successful connected to hashR postgress database:'
            ' postgresql://hashR:***@127.0.0.1:5432/hashRdb')
        mock_error.assert_not_called()
        mock_create_engine.assert_called_with(
            'postgresql://hashR:hashR123@127.0.0.1:5432/hashRdb',
            connect_args={'connect_timeout': 10})

    @mock.patch.object(sqlalchemy, 'create_engine', autospec=True)
    @mock.patch.object(logging.Logger, 'error', autospec=True)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    def test_connect_hashR_no_db_info(self, mock_info, mock_error,
                                      mock_create_engine):
        """Test the connect_hashR function with missing connection information.

        Args:
            mock_info: Mock object for the logger.info function.
            mock_error: Mock object for the logger.error function.
            mock_create_engine: Mock object for the sqlalchemy.create_engine
                                function.
        """
        self.assertRaises(Exception, self.analyzer.connect_hashR)
        mock_info.assert_not_called()
        mock_error.assert_not_called()
        mock_create_engine.assert_not_called()

    @mock.patch.object(sqlalchemy, 'create_engine', autospec=True)
    @mock.patch.object(logging.Logger, 'error', autospec=True)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    def test_connect_hashr_conn_error(self, mock_info, mock_error,
                                      mock_create_engine):
        """Test the connect_hashR function simulating a connection error.

        Args:
            mock_info: Mock object for the logger.info function.
            mock_error: Mock object for the logger.error function.
            mock_create_engine: Mock object for the sqlalchemy.create_engine
                                function.
        """
        current_app.config['HASHR_DB_USER'] = 'hashR'
        current_app.config['HASHR_DB_PW'] = 'hashR123'
        current_app.config['HASHR_DB_ADDR'] = '127.0.0.2'
        current_app.config['HASHR_DB_PORT'] = '5432'
        current_app.config['HASHR_DB_NAME'] = 'hashRdb'
        current_app.config['HASHR_ADD_SOURCE_ATTRIBUTE'] = True

        mock_create_engine(
        ).connect.side_effect = sqlalchemy.exc.OperationalError(
            statement=None, params=None, orig='Cannot connect to server!')
        test_conn = self.analyzer.connect_hashR()
        expected_return = ('Connection to the database FAILED. Please check the'
                           ' celery logs and make sure you have provided the '
                           'correct database information in the analyzer file!')
        self.assertEqual(test_conn, expected_return)
        mock_create_engine.assert_called_with(
            'postgresql://hashR:hashR123@127.0.0.2:5432/hashRdb',
            connect_args={'connect_timeout': 10})
        mock_info.assert_not_called()
        mock_error.assert_called_with(
            self.logger, '!!! Connection to the hashR postgres database not '
            'possible! -- Provided connection string: "postgresql://'
            'hashR:***@127.0.0.2:5432/hashRdb -- Error message: (builtins.str)'
            ' Cannot connect to server!\n(Background on this error at: '
            'http://sqlalche.me/e/e3q8)'
        )

    # pylint: disable=no-method-argument
    def mock_custom_side_effect(*args):
        """This function is a custom side_effect to return results based on args.

        Args:
            *args: Anything
        """
        if args[1] == 'insert_statement':
            return True
        # pylint: disable=protected-access
        if isinstance(args[1], mock.MagicMock) and args[1]._extract_mock_name(
        ) == 'MetaData().tables.__getitem__().join().join()':
            return 'select_statement_sources'
        if isinstance(args[1], mock.MagicMock) and args[1]._extract_mock_name(
        ) == 'Table().join()':
            return 'select_statement_tags'
        # pylint: enable=protected-access
        if args[1] == 'select_statement_sources':
            result_hashes = [
                ('78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0',
                 'randomSourceHash', 'Windows10Home-10.0-19041-1288sp',
                 'Windows'),
                ('78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0',
                 'randomSourceHash',
                 'WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp',
                 'WindowsServer'),
                ('960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d',
                 'randomSourceHash',
                 'WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp', 'Windows'),
                ('c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83',
                 'randomSourceHash', 'Windows10Home-10.0-19041-1288sp',
                 'WindowsPro'),
                ('c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83',
                 'randomSourceHash', 'Windows10Pro-10.0-19041-1288sp',
                 'WindowsPro'),
                ('7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af',
                 'randomSourceHash', 'debian-cloud-debian-9-stretch-v20220621',
                 'GCP'),
                ('66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3',
                 'randomSourceHash',
                 'debian-cloud-debian-11-bullseye-arm64-v20220712', 'GCP')
            ]
            return result_hashes
        if args[1] == 'select_statement_tags':
            result_hashes = [
                ('78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0',),
                ('960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d',),
                ('c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83',),
                ('7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af',),
                ('66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3',)
            ]
            return result_hashes
        return 'ERROR'
    # pylint: enable=no-method-argument

    @mock.patch.object(sqlalchemy, 'select', autospec=True)
    @mock.patch.object(sqlalchemy, 'String', autospec=True)
    @mock.patch.object(sqlalchemy, 'Column', autospec=True)
    @mock.patch.object(sqlalchemy, 'Table', autospec=True)
    @mock.patch.object(sqlalchemy, 'MetaData', autospec=True)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    def test_check_against_hashR_matching_hashes_no_sources(
            self, mock_info, mock_meta_data, mock_table, _mock_column,
            _mock_string, mock_select):
        """Test the check_against_hashR function with existing matches and tags only.

        Args:
            mock_info: Mock object for the logger.info function.
            mock_meta_data: Mock object for the sqlalchemy meta_data function.
            mock_table: Mock object for the sqlalchemy Table class.
            mock_select: Mock object for the sqlalchemy Select class.
            _mock_column: Unused mock object for the sqlalchemy Column class.
            _mock_string: Unused mock object for the sqlalchemy String class.
        """
        test_input_hashes = [
            '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0',
            'ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542',
            '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d',
            'bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f',
            'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83',
            '40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651',
            '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af',
            '7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c',
            '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3',
            '2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc'
        ]
        expected_insert_hash_entries = [{
            'sha256':
                '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0'
        }, {
            'sha256':
                'ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542'
        }, {
            'sha256':
                '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d'
        }, {
            'sha256':
                'bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f'
        }, {
            'sha256':
                'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83'
        }, {
            'sha256':
                '40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651'
        }, {
            'sha256':
                '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af'
        }, {
            'sha256':
                '7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c'
        }, {
            'sha256':
                '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3'
        }, {
            'sha256':
                '2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc'
        }]
        expected_return = [
            '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0',
            '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d',
            'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83',
            '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af',
            '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3',
        ]

        test_bind = mock.MagicMock()
        self.analyzer.hashr_conn = test_bind
        test_meta_data = mock.MagicMock()
        mock_meta_data.return_value = test_meta_data
        test_table = mock.MagicMock()
        test_insert_stmt = 'insert_statement'
        test_table.insert().return_value = test_insert_stmt
        mock_table.return_value = test_table
        test_conn = mock.MagicMock()
        test_conn.execute.side_effect = self.mock_custom_side_effect
        test_conn.__enter__().execute.side_effect = self.mock_custom_side_effect
        self.analyzer.hashr_conn.connect.return_value = test_conn
        mock_select().select_from.side_effect = self.mock_custom_side_effect
        self.analyzer.add_source_attribute = False

        test_output_hashes = self.analyzer.check_against_hashR(
            test_input_hashes)

        mock_meta_data.assert_called_with(bind=test_bind)
        mock_meta_data.reflect.assert_called_with(test_meta_data)
        test_table.insert.assert_called_with(expected_insert_hash_entries)
        mock_info.assert_any_call(
            self.logger, 'ADD_SOURCE_ATTRIBUTE=False => adding tags only!')
        mock_info.assert_any_call(
            self.logger, 'Found 5 unique hashes in hashR DB.')
        test_bind.dispose.assert_called_once()
        self.assertEqual(test_output_hashes, expected_return)

    @mock.patch.object(sqlalchemy, 'select', autospec=True)
    @mock.patch.object(sqlalchemy, 'String', autospec=True)
    @mock.patch.object(sqlalchemy, 'Column', autospec=True)
    @mock.patch.object(sqlalchemy, 'Table', autospec=True)
    @mock.patch.object(sqlalchemy, 'MetaData', autospec=True)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    def test_check_against_hashR_matching_hashes_sources(self, mock_info,
                                                         mock_meta_data,
                                                         mock_table,
                                                         _mock_column,
                                                         _mock_string,
                                                         mock_select):
        """Test check_against_hashR function with matches + tags & attributes.

        Args:
            mock_info: Mock object for the logger.info function.
            mock_meta_data: Mock object for the sqlalchemy meta_data function.
            mock_table: Mock object for the sqlalchemy Table class.
            mock_select: Mock object for the sqlalchemy Select class.
            _mock_column: Unused mock object for the sqlalchemy Column class.
            _mock_string: Unused mock object for the sqlalchemy String class.
        """
        test_input_hashes = [
            '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0',
            'ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542',
            '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d',
            'bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f',
            'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83',
            '40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651',
            '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af',
            '7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c',
            '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3',
            '2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc'
        ]
        expected_insert_hash_entries = [{
            'sha256':
                '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0'
        }, {
            'sha256':
                'ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542'
        }, {
            'sha256':
                '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d'
        }, {
            'sha256':
                'bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f'
        }, {
            'sha256':
                'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83'
        }, {
            'sha256':
                '40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651'
        }, {
            'sha256':
                '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af'
        }, {
            'sha256':
                '7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c'
        }, {
            'sha256':
                '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3'
        }, {
            'sha256':
                '2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc'
        }]
        expected_return = {
            '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0': [
                'Windows:Windows10Home-10.0-19041-1288sp',
                'WindowsServer:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp'
            ],
            '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d': [
                'Windows:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp'
            ],
            'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83': [
                'WindowsPro:Windows10Home-10.0-19041-1288sp',
                'WindowsPro:Windows10Pro-10.0-19041-1288sp'
            ],
            '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af': [
                'GCP:debian-cloud-debian-9-stretch-v20220621'
            ],
            '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3': [
                'GCP:debian-cloud-debian-11-bullseye-arm64-v20220712'
            ]
        }

        test_bind = mock.MagicMock()
        self.analyzer.hashr_conn = test_bind
        test_meta_data = mock.MagicMock()
        mock_meta_data.return_value = test_meta_data
        test_table = mock.MagicMock()
        test_insert_stmt = 'insert_statement'
        test_table.insert().return_value = test_insert_stmt
        mock_table.return_value = test_table
        test_conn = mock.MagicMock()
        test_conn.execute.side_effect = self.mock_custom_side_effect
        test_conn.__enter__().execute.side_effect = self.mock_custom_side_effect
        self.analyzer.hashr_conn.connect.return_value = test_conn
        mock_select().select_from.side_effect = self.mock_custom_side_effect
        self.analyzer.add_source_attribute = True

        test_output_hashes = self.analyzer.check_against_hashR(
            test_input_hashes)

        mock_meta_data.assert_called_with(bind=test_bind)
        mock_meta_data.reflect.assert_called_with(test_meta_data)
        test_table.insert.assert_called_with(expected_insert_hash_entries)
        mock_info.assert_any_call(
            self.logger,
            'ADD_SOURCE_ATTRIBUTE=True => going to add tags and attributes!')
        mock_info.assert_any_call(
            self.logger, 'Found 5 unique hashes in hashR DB.')
        test_bind.dispose.assert_called_once()
        self.assertEqual(test_output_hashes, expected_return)

    @mock.patch(u'timesketch.lib.analyzers.interface.OpenSearchDataStore',
                MockDataStore)
    @mock.patch.object(logging.Logger, 'warning', autospec=True)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    @mock.patch.object(
        hashr_lookup.HashRLookupSketchPlugin, 'connect_hashR', autospec=True)
    @mock.patch.object(
        hashr_lookup.HashRLookupSketchPlugin,
        'check_against_hashR',
        autospec=True)
    def test_run_no_sources(self, mock_check, mock_connect, mock_info,
                            mock_warning):
        """Test the run function which with the flag add_source_attribute=False.

        Args:
            mock_info: Mock object for the logger.info function.
            mock_warning: Mock object for the logger.warning function.
            mock_check: Mock object for the check_against_hashR function.
            mock_connect: Mock object for the connect_hashR function.
        """
        test_input_hashes = [
            {
                'hash_sha256':
                    '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0'
            },
            {
                'sha256':
                    'ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542'
            },
            {
                'hash':
                    '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d'
            },
            {
                'sha256_hash':
                    'bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f'
            },
            {
                'sha256':
                    'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83'
            },
            {
                'sha256_hash':
                    '40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651'
            },
            {
                'hash':
                    '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af'
            },
            {
                'hash_sha256':
                    '7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c'
            },
            {
                'hash_sha256':
                    '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3'
            },
            {
                'sha256':
                    '2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc'
            },
            {
                'hash': '8bbd7976b2b86e1746494c98425e7830'
            },
            {
                'sha256':
                    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
            },
            {
                'sha265':
                    '5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92'
            },
        ]

        expected_matching_hashes = [
            '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0',
            '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d',
            'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83',
            '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af',
            '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3',
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        ]

        analyzer = hashr_lookup.HashRLookupSketchPlugin('test_index', 1)
        analyzer.datastore.client = mock.Mock()

        event_id = 0
        for entry in test_input_hashes:
            event = copy.deepcopy(MockDataStore.event_dict)
            event['_source'].update(entry)
            analyzer.datastore.import_event('test_index', event['_type'],
                                            event['_source'],
                                            '{}'.format(event_id))
            event_id += 1

        mock_connect.return_value = True
        mock_check.return_value = expected_matching_hashes
        analyzer.add_source_attribute = False
        analyzer.unique_known_hash_counter = 5

        result_message = analyzer.run()
        self.assertEqual(
            result_message,
            'Found a total of 13 events with a sha256 hash value - 11 unique '
            'hashes queried against hashR - 5 hashes were known in hashR - 6 '
            'hashes were unknown in hashR - 6 events tagged - 1 entries were '
            'tagged as zerobyte files - 2 events raisend an error')
        mock_warning.assert_any_call(
            self.logger,
            'The extracted hash does not match the required lenght (64) of '
            'a SHA256 hash. Skipping this event! Hash: '
            '8bbd7976b2b86e1746494c98425e7830 - Lenght: 32')
        self.assertTrue(
            'No matching field with a hash found in this event! -- Event Source:'
            in str(mock_warning.call_args_list) and
            '5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92'
            in str(mock_warning.call_args_list))
        mock_info.assert_any_call(self.logger, 'Start adding tags to events.')

    @mock.patch(u'timesketch.lib.analyzers.interface.OpenSearchDataStore',
                MockDataStore)
    @mock.patch.object(logging.Logger, 'warning', autospec=True)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    @mock.patch.object(
        hashr_lookup.HashRLookupSketchPlugin, 'connect_hashR', autospec=True)
    @mock.patch.object(
        hashr_lookup.HashRLookupSketchPlugin,
        'check_against_hashR',
        autospec=True)
    def test_run_sources(self, mock_check, mock_connect, mock_info, mock_warning):
        """Test the run function which with the flag add_source_attribute=True.

        Args:
            mock_info: Mock object for the logger.info function.
            mock_warning: Mock object for the logger.warning function.
            mock_check: Mock object for the check_against_hashR function.
            mock_connect: Mock object for the connect_hashR function.
        """
        test_input_hashes = [
            {
                'hash_sha256':
                    '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0'
            },
            {
                'sha256':
                    'ff0e11660290f8a412ce4903b8936ae16737a6b3e3ec516e7a3e5d20c7fab542'
            },
            {
                'hash':
                    '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d'
            },
            {
                'sha256_hash':
                    'bb5dbb52b436d4283379d30da8f44d068d3b788fab7e9fbd9f1e89306800726f'
            },
            {
                'sha256':
                    'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83'
            },
            {
                'sha256_hash':
                    '40db7cc1d23ff00cc3c5bfc0c24622ad9aafb749b574560a2ef61de5ec2c8651'
            },
            {
                'hash':
                    '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af'
            },
            {
                'hash_sha256':
                    '7f7764af3c8cb71c248efc4390dc0a19485f4b540b7d3aec8d3a4aeb0cabf94c'
            },
            {
                'hash_sha256':
                    '66fd756e1c8dc4c7bb334c8d327c306d9006838b8bbc953e3acfeace48d3f7a3'
            },
            {
                'sha256':
                    '2aa72d5284dbe2a38d92cef68d084d4f689f9928db0cd1fe0a207ada2d10f5fc'
            },
            {
                'hash': '8bbd7976b2b86e1746494c98425e7830'
            },
            {
                'sha256':
                    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
            },
            {
                'sha265':
                    '5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92'
            },
        ]

        expected_matching_hashes = {
            '78a249b6e0f74979d2d2a230abbe5f3c9b558fcc01e61c7c09950304cf95c7c0': [
                'Windows:Windows10Home-10.0-19041-1288sp',
                'WindowsServer:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp'
            ],
            '960c90b949f327f1eb7537489ea9688040da4ddcbc1551dc58a24e4555d0da0d': [
                'Windows:WindowsServer2019SERVERSTANDARDCORE-10.0-17763-2114sp'
            ],
            'c9082f8a24908bd6cc2ddeb14ba2c320ad4d3c0f7aac9257564e10299c790f83': [
                'WindowsPro:Windows10Home-10.0-19041-1288sp',
                'WindowsPro:Windows10Pro-10.0-19041-1288sp'
            ],
            '7af6a6e336fb128163d60ab424a9b2e9e682462dd669f611b550785c1d3d14af': [
                'GCP:debian-cloud-debian-9-stretch-v20220621'
            ],
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855': [
                'GCP:debian-cloud-debian-11-bullseye-arm64-v20220712'
            ]
        }

        analyzer = hashr_lookup.HashRLookupSketchPlugin('test_index', 1)
        analyzer.datastore.client = mock.Mock()

        event_id = 0
        for entry in test_input_hashes:
            event = copy.deepcopy(MockDataStore.event_dict)
            event['_source'].update(entry)
            analyzer.datastore.import_event('test_index', event['_type'],
                                            event['_source'],
                                            '{}'.format(event_id))
            event_id += 1

        mock_connect.return_value = True
        mock_check.return_value = expected_matching_hashes
        analyzer.add_source_attribute = True
        analyzer.unique_known_hash_counter = 5

        result_message = analyzer.run()
        self.assertEqual(
            result_message,
            'Found a total of 13 events with a sha256 hash value - 11 unique '
            'hashes queried against hashR - 5 hashes were known in hashR - 6 '
            'hashes were unknown in hashR - 5 events tagged - 1 entries were '
            'tagged as zerobyte files - 2 events raisend an error')
        mock_warning.assert_any_call(
            self.logger,
            'The extracted hash does not match the required lenght (64) of '
            'a SHA256 hash. Skipping this event! Hash: '
            '8bbd7976b2b86e1746494c98425e7830 - Lenght: 32')
        self.assertTrue(
            'No matching field with a hash found in this event! -- Event Source:'
            in str(mock_warning.call_args_list) and
            '5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92'
            in str(mock_warning.call_args_list))
        mock_info.assert_any_call(self.logger,
                                  'Start adding tags and attributes to events.')

    @mock.patch(u'timesketch.lib.analyzers.interface.OpenSearchDataStore',
                MockDataStore)
    @mock.patch.object(logging.Logger, 'info', autospec=True)
    @mock.patch.object(
        hashr_lookup.HashRLookupSketchPlugin, 'connect_hashR', autospec=True)
    def test_run_no_hashes(self, mock_connect, _mock_info):
        """Test the run function with no hashes in the events.

        Args:
            _mock_info: Unused mock object for the logger.info function.
            mock_connect: Mock object for the connect_hashR function.
        """
        analyzer = hashr_lookup.HashRLookupSketchPlugin('test_index', 1)
        analyzer.datastore.client = mock.Mock()

        mock_connect.return_value = True
        analyzer.add_source_attribute = True

        result_message = analyzer.run()
        self.assertEqual(
            result_message,
            'The selected timeline "" does not contain any fields with a '
            'sha256 hash.')

    def test_process_event(self):
        """Test the process_event function with no special cases."""
        event = mock.MagicMock()
        sources = [
            'WindowsPro:Windows10Home-10.0-19041-1288sp',
            'WindowsPro:Windows10Pro-10.0-19041-1288sp'
        ]
        hash_value = '5302a61849d2722551832734c5d246db90c41a7ffdad36b5558992227edc2e92'

        self.analyzer.process_event(hash_value, sources, event)
        self.assertEqual(self.analyzer.zerobyte_file_counter, 0)
        event.add_tags.assert_called_with(['hashR'])
        event.add_attributes.assert_called_with({
            'hashR_sample_sources': [
                'WindowsPro:Windows10Home-10.0-19041-1288sp',
                'WindowsPro:Windows10Pro-10.0-19041-1288sp'
            ]
        })
        event.commit.assert_called_once()

    def test_process_event_zerobytefile(self):
        """Test the process_event function with a zyrobyte hash."""
        event = mock.MagicMock()
        sources = [
            'WindowsPro:Windows10Home-10.0-19041-1288sp',
            'WindowsPro:Windows10Pro-10.0-19041-1288sp'
        ]
        hash_value = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

        self.analyzer.process_event(hash_value, sources, event)
        self.assertEqual(self.analyzer.zerobyte_file_counter, 1)
        event.add_tags.assert_called_with(['hashR', 'zerobyte file'])
        event.add_attributes.assert_not_called()
        event.commit.assert_called_once()
