# Copyright 2017 Google Inc. All rights reserved.
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
"""Timesketch API client."""
from __future__ import unicode_literals

import os
import logging
import uuid

# pylint: disable=wrong-import-order
import bs4
import requests
# pylint: disable=redefined-builtin
from requests.exceptions import ConnectionError
import webbrowser

# pylint: disable-msg=import-error
from google_auth_oauthlib import flow as googleauth_flow
import google.auth.transport.requests
import pandas

from . import credentials
from . import definitions
from . import error
from . import index
from . import sketch
from . import user
from . import version
from . import sigma


logger = logging.getLogger('timesketch_api.client')


class TimesketchApi:
    """Timesketch API object

    Attributes:
        api_root: The full URL to the server API endpoint.
        session: Authenticated HTTP session.
    """

    DEFAULT_OAUTH_SCOPE = [
        'https://www.googleapis.com/auth/userinfo.email',
        'openid',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]

    DEFAULT_OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    DEFAULT_OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    DEFAULT_OAUTH_PROVIDER_URL = 'https://www.googleapis.com/oauth2/v1/certs'
    DEFAULT_OAUTH_OOB_URL = 'urn:ietf:wg:oauth:2.0:oob'
    DEFAULT_OAUTH_API_CALLBACK = '/login/api_callback/'

    def __init__(self,
                 host_uri,
                 username,
                 password='',
                 verify=True,
                 client_id='',
                 client_secret='',
                 auth_mode='userpass',
                 create_session=True):
        """Initializes the TimesketchApi object.

        Args:
            host_uri: URI to the Timesketch server (https://<server>/).
            username: User username.
            password: User password.
            verify: Verify server SSL certificate.
            client_id: The client ID if OAUTH auth is used.
            client_secret: The OAUTH client secret if OAUTH is used.
            auth_mode: The authentication mode to use. Defaults to 'userpass'
                Supported values are 'userpass' (username/password combo),
                'http-basic' (HTTP Basic authentication) and oauth.
            create_session: Boolean indicating whether the client object
                should create a session object. If set to False the
                function "set_session" needs to be called before proceeding.

        Raises:
            ConnectionError: If the Timesketch server is unreachable.
            RuntimeError: If the client is unable to authenticate to the
                backend.
        """
        self._host_uri = host_uri
        self.api_root = '{0:s}/api/v1'.format(host_uri)
        self.credentials = None
        self._flow = None

        if not create_session:
            self.session = None
            return

        try:
            self.session = self._create_session(
                username, password, verify=verify, client_id=client_id,
                client_secret=client_secret, auth_mode=auth_mode)
        except ConnectionError as exc:
            raise ConnectionError('Timesketch server unreachable') from exc
        except RuntimeError as e:
            raise RuntimeError(
                'Unable to connect to server, error: {0!s}'.format(e)) from e

    @property
    def current_user(self):
        """Property that returns the user object of the logged in user."""
        return user.User(self)

    @property
    def version(self):
        """Property that returns back the API client version."""
        version_dict = self.fetch_resource_data('version/')
        ts_version = None
        if version_dict:
            ts_version = version_dict.get('meta', {}).get('version')

        if ts_version:
            return 'API Client: {0:s}\nTS Backend: {1:s}'.format(
                version.get_version(), ts_version)

        return 'API Client: {0:s}'.format(version.get_version())

    def set_credentials(self, credential_object):
        """Sets the credential object."""
        self.credentials = credential_object

    def set_session(self, session_object):
        """Sets the session object."""
        self.session = session_object

    def _authenticate_session(self, session, username, password):
        """Post username/password to authenticate the HTTP seesion.

        Args:
            session: Instance of requests.Session.
            username: User username.
            password: User password.
        """
        # Do a POST to the login handler to set up the session cookies
        data = {'username': username, 'password': password}
        session.post('{0:s}/login/'.format(self._host_uri), data=data)

    def _set_csrf_token(self, session):
        """Retrieve CSRF token from the server and append to HTTP headers.

        Args:
            session: Instance of requests.Session.
        """
        # Scrape the CSRF token from the response
        response = session.get(self._host_uri)
        soup = bs4.BeautifulSoup(response.text, features='html.parser')

        tag = soup.find(id='csrf_token')
        csrf_token = None
        if tag:
            csrf_token = tag.get('value')
        else:
            tag = soup.find('meta', attrs={'name': 'csrf-token'})
            if tag:
                csrf_token = tag.attrs.get('content')

        if not csrf_token:
            return

        session.headers.update({
            'x-csrftoken': csrf_token,
            'referer': self._host_uri
        })

    def _create_oauth_session(
            self, client_id='', client_secret='', client_secrets_file=None,
            run_server=True, skip_open=False):
        """Return an OAuth session.

        Args:
            client_id: The client ID if OAUTH auth is used.
            client_secret: The OAUTH client secret if OAUTH is used.
            client_secrets_file: Path to the JSON file that contains the client
                secrets, in the client_secrets format.
            run_server: A boolean, if set to true (default) a web server is
                run to catch the OAUTH request and response.
            skip_open: A booelan, if set to True (defaults to False) an
                authorization URL is printed on the screen to visit. This is
                only valid if run_server is set to False.

        Return:
            session: Instance of requests.Session.

        Raises:
            RuntimeError: if unable to log in to the application.
        """
        if client_secrets_file:
            if not os.path.isfile(client_secrets_file):
                raise RuntimeError(
                    'Unable to log in, client secret files does not exist.')
            flow = googleauth_flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes=self.DEFAULT_OAUTH_SCOPE,
                autogenerate_code_verifier=True)
        else:
            provider_url = self.DEFAULT_OAUTH_PROVIDER_URL
            client_config = {
                'installed': {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'auth_uri': self.DEFAULT_OAUTH_AUTH_URL,
                    'token_uri': self.DEFAULT_OAUTH_TOKEN_URL,
                    'auth_provider_x509_cert_url': provider_url,
                    'redirect_uris': [self.DEFAULT_OAUTH_OOB_URL],
                },
            }

            flow = googleauth_flow.InstalledAppFlow.from_client_config(
                client_config, self.DEFAULT_OAUTH_SCOPE,
                autogenerate_code_verifier=True)

            flow.redirect_uri = self.DEFAULT_OAUTH_OOB_URL

        if run_server:
            _ = flow.run_local_server()
        else:
            auth_url, _ = flow.authorization_url(prompt='select_account')

            if skip_open:
                print('Visit the following URL to authenticate: {0:s}'.format(
                    auth_url))
            else:
                open_browser = input('Open the URL in a browser window? [y/N] ')
                if open_browser.lower() == 'y' or open_browser.lower() == 'yes':
                    webbrowser.open(auth_url)
                else:
                    print(
                        'Need to manually visit URL to authenticate: '
                        '{0:s}'.format(auth_url))

            code = input('Enter the token code: ')
            _ = flow.fetch_token(code=code)

        session = flow.authorized_session()
        self._flow = flow
        self.credentials = credentials.TimesketchOAuthCredentials()
        self.credentials.credential = flow.credentials
        return self.authenticate_oauth_session(session)

    def authenticate_oauth_session(self, session):
        """Authenticate an OAUTH session.

        Args:
            session: Authorized session object.
        """
        # Authenticate to the Timesketch backend.
        login_callback_url = '{0:s}{1:s}'.format(
            self._host_uri, self.DEFAULT_OAUTH_API_CALLBACK)
        params = {
            'id_token': session.credentials.id_token,
        }
        response = session.get(login_callback_url, params=params)
        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response, message='Unable to authenticate', error=RuntimeError)

        self._set_csrf_token(session)
        return session

    def _create_session(
            self, username, password, verify, client_id, client_secret,
            auth_mode):
        """Create authenticated HTTP session for server communication.

        Args:
            username: User to authenticate as.
            password: User password.
            verify: Verify server SSL certificate.
            client_id: The client ID if OAUTH auth is used.
            client_secret: The OAUTH client secret if OAUTH is used.
            auth_mode: The authentication mode to use. Supported values are
                'userpass' (username/password combo), 'http-basic'
                (HTTP Basic authentication) and oauth.

        Returns:
            Instance of requests.Session.
        """
        if auth_mode == 'oauth':
            return self._create_oauth_session(client_id, client_secret)

        if auth_mode == 'oauth_local':
            return self._create_oauth_session(
                client_id=client_id, client_secret=client_secret,
                run_server=False, skip_open=True)

        session = requests.Session()

        # If using HTTP Basic auth, add the user/pass to the session
        if auth_mode == 'http-basic':
            session.auth = (username, password)

        # SSL Cert verification is turned on by default.
        if not verify:
            session.verify = False

        # Get and set CSRF token and authenticate the session if appropriate.
        self._set_csrf_token(session)
        if auth_mode == 'userpass':
            self._authenticate_session(session, username, password)

        return session

    def fetch_resource_data(self, resource_uri, params=None):
        """Make a HTTP GET request.

        Args:
            resource_uri: The URI to the resource to be fetched.
            params: Dict of URL parameters to send in the GET request.

        Returns:
            Dictionary with the response data.
        """
        resource_url = '{0:s}/{1:s}'.format(self.api_root, resource_uri)
        response = self.session.get(resource_url, params=params)
        return error.get_response_json(response, logger)

    def create_sketch(self, name, description=None):
        """Create a new sketch.

        Args:
            name: Name of the sketch.
            description: Description of the sketch.

        Returns:
            Instance of a Sketch object.
        """
        if not description:
            description = name

        resource_url = '{0:s}/sketches/'.format(self.api_root)
        form_data = {'name': name, 'description': description}
        response = self.session.post(resource_url, json=form_data)
        response_dict = error.get_response_json(response, logger)
        sketch_id = response_dict['objects'][0]['id']
        return self.get_sketch(sketch_id)

    def get_oauth_token_status(self):
        """Return a dict with OAuth token status, if one exists."""
        if not self.credentials:
            return {
                'status': 'No stored credentials.'}
        return {
            'expired': self.credentials.credential.expired,
            'expiry_time': self.credentials.credential.expiry.isoformat(),
        }

    def get_sketch(self, sketch_id):
        """Get a sketch.

        Args:
            sketch_id: Primary key ID of the sketch.

        Returns:
            Instance of a Sketch object.
        """
        return sketch.Sketch(sketch_id, api=self)

    def get_aggregator_info(self, name='', as_pandas=False):
        """Returns information about available aggregators.

        Args:
            name: String with the name of an aggregator. If the name is not
                provided, a list with all aggregators is returned.
            as_pandas: Boolean indicating that the results will be returned
                as a Pandas DataFrame instead of a list of dicts.

        Returns:
            A list with dict objects with the information about aggregators,
            unless as_pandas is set, then the function returns a DataFrame
            object.
        """
        resource_uri = 'aggregation/info/'

        if name:
            data = {'aggregator': name}
            resource_url = '{0:s}/{1:s}'.format(self.api_root, resource_uri)
            response = self.session.post(resource_url, json=data)
            response_json = error.get_response_json(response, logger)
        else:
            response_json = self.fetch_resource_data(resource_uri)

        if not as_pandas:
            return response_json

        lines = []
        if isinstance(response_json, dict):
            response_json = [response_json]

        for line in response_json:
            line_dict = {
                'name': line.get('name', 'N/A'),
                'description': line.get('description', 'N/A'),
            }
            for field_index, field in enumerate(line.get('fields', [])):
                line_dict['field_{0:d}_name'.format(
                    field_index + 1)] = field.get('name')
                line_dict['field_{0:d}_description'.format(
                    field_index + 1)] = field.get('description')
            lines.append(line_dict)

        return pandas.DataFrame(lines)

    def list_sketches(self, per_page=50, scope='user', include_archived=True):
        """Get a list of all open sketches that the user has access to.

        Args:
            per_page: Number of items per page when paginating. Default is 50.
            scope: What scope to get sketches as. Default to user.
            include_archived: If archived sketches should be returned.

        Yields:
            Sketch objects instances.
        """
        url_params = {
            'per_page': per_page,
            'scope': scope,
            'include_archived': include_archived
        }
        # Start with the first page
        page = 1
        has_next_page = True

        while has_next_page:
            url_params['page'] = page
            response = self.fetch_resource_data('sketches/', params=url_params)
            meta = response.get('meta', {})

            page = meta.get('next_page')
            if not page:
                has_next_page = False

            for sketch_dict in response.get('objects', []):
                sketch_id = sketch_dict['id']
                sketch_name = sketch_dict['name']
                sketch_obj = sketch.Sketch(
                    sketch_id=sketch_id, api=self, sketch_name=sketch_name)
                yield sketch_obj

    def get_searchindex(self, searchindex_id):
        """Get a searchindex.

        Args:
            searchindex_id: Primary key ID of the searchindex.

        Returns:
            Instance of a SearchIndex object.
        """
        return index.SearchIndex(searchindex_id, api=self)

    def get_or_create_searchindex(self,
                                  searchindex_name,
                                  es_index_name=None,
                                  public=False):
        """Create a new searchindex.

        Args:
            searchindex_name: Name of the searchindex in Timesketch.
            es_index_name: Name of the index in Elasticsearch.
            public: Boolean indicating if the searchindex should be public.

        Returns:
            Instance of a SearchIndex object and a boolean indicating if the
            object was created.
        """
        if not es_index_name:
            es_index_name = uuid.uuid4().hex

        resource_url = '{0:s}/searchindices/'.format(self.api_root)
        form_data = {
            'searchindex_name': searchindex_name,
            'es_index_name': es_index_name,
            'public': public
        }
        response = self.session.post(resource_url, json=form_data)

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response, message='Error creating searchindex',
                error=RuntimeError)

        response_dict = error.get_response_json(response, logger)
        metadata_dict = response_dict['meta']
        created = metadata_dict.get('created', False)
        searchindex_id = response_dict['objects'][0]['id']
        return self.get_searchindex(searchindex_id), created

    def list_searchindices(self):
        """Get list of all searchindices that the user has access to.

        Returns:
            List of SearchIndex object instances.
        """
        indices = []
        response = self.fetch_resource_data('searchindices/')
        response_objects = response.get('objects')
        if not response_objects:
            return indices

        for index_dict in response_objects[0]:
            index_id = index_dict['id']
            index_name = index_dict['name']
            index_obj = index.SearchIndex(
                searchindex_id=index_id, api=self, searchindex_name=index_name)
            indices.append(index_obj)
        return indices

    def refresh_oauth_token(self):
        """Refresh an OAUTH token if one is defined."""
        if not self.credentials:
            return
        request = google.auth.transport.requests.Request()
        self.credentials.credential.refresh(request)

    def list_sigma_rules(self, as_pandas=False):
        """Get a list of sigma objects.

        Args:
            as_pandas: Boolean indicating that the results will be returned
                as a Pandas DataFrame instead of a list of dicts.

        Returns:
            List of Sigme rule object instances or a pandas Dataframe with all
            rules if as_pandas is True.

        Raises:
            ValueError: If no rules are found.
        """
        rules = []
        response = self.fetch_resource_data('sigma/')

        if not response:
            raise ValueError('No rules found.')

        if as_pandas:
            return pandas.DataFrame.from_records(response.get('objects'))

        for rule_dict in response['objects']:
            rule_uuid = rule_dict.get('id')
            title = rule_dict.get('title')
            es_query = rule_dict.get('es_query')
            file_name = rule_dict.get('file_name')
            description = rule_dict.get('description')
            file_relpath = rule_dict.get('file_relpath')
            index_obj = sigma.Sigma(
                rule_uuid, api=self, es_query=es_query, file_name=file_name,
                title=title, description=description,
                file_relpath=file_relpath)
            rules.append(index_obj)
        return rules


    def get_sigma_rule(self, rule_uuid):
        """Get a sigma rule.

        Args:
            rule_uuid: UUID of the Sigma rule.

        Returns:
            Instance of a Sigma object.
        """
        return sigma.Sigma(rule_uuid, api=self)
