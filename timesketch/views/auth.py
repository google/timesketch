# Copyright 2015 Google Inc. All rights reserved.
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
"""This module implements HTTP request handlers for the user views."""

from __future__ import unicode_literals

import requests

from flask import abort
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from oauthlib import oauth2

from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user

from timesketch.lib.definitions import HTTP_STATUS_CODE_UNAUTHORIZED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.forms import UsernamePasswordForm
from timesketch.lib.google_auth import get_public_key_for_jwt
from timesketch.lib.google_auth import get_oauth2_discovery_document
from timesketch.lib.google_auth import get_oauth2_authorize_url
from timesketch.lib.google_auth import get_encoded_jwt_over_https
from timesketch.lib.google_auth import decode_jwt
from timesketch.lib.google_auth import validate_jwt
from timesketch.lib.google_auth import JwtValidationError
from timesketch.lib.google_auth import JwtKeyError
from timesketch.lib.google_auth import JwtFetchError
from timesketch.lib.google_auth import DiscoveryDocumentError
from timesketch.lib.google_auth import CSRF_KEY
from timesketch.models import db_session
from timesketch.models.user import Group
from timesketch.models.user import User

# Register flask blueprint
auth_views = Blueprint("user_views", __name__)

TOKEN_URI = "https://www.googleapis.com/oauth2/v3/tokeninfo"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@auth_views.route("/login/", methods=["GET", "POST"])
def login():
    """Handler for the login page view.

    There are four ways of authentication.
    1) Google OpenID connect.
    2) Google Cloud Identity-Aware Proxy.
    3) If Single Sign On (SSO) is enabled in the configuration and the
       environment variable is present, e.g. REMOTE_USER then the system will
       get or create the user object and setup a session for the user.
    4) Local authentication is used if SSO login is not enabled. This will
       authenticate the user against the local user database

    Returns:
        Redirect if authentication is successful or template with context
        otherwise.
    """
    # Google OpenID Connect authentication.
    if current_app.config.get("GOOGLE_OIDC_ENABLED", False):
        hosted_domain = current_app.config.get("GOOGLE_OIDC_HOSTED_DOMAIN")
        # Save the next URL parameter in the session for redirect after login.
        session["next"] = request.args.get("next", "/")
        return redirect(get_oauth2_authorize_url(hosted_domain))

    # Google Identity-Aware Proxy authentication (using JSON Web Tokens)
    if current_app.config.get("GOOGLE_IAP_ENABLED", False):
        encoded_jwt = request.environ.get("HTTP_X_GOOG_IAP_JWT_ASSERTION", None)
        # pylint: disable=broad-except
        if encoded_jwt:
            expected_audience = current_app.config.get("GOOGLE_IAP_AUDIENCE")
            expected_issuer = current_app.config.get("GOOGLE_IAP_ISSUER")
            algorithm = current_app.config.get("GOOGLE_IAP_ALGORITHM")
            url = current_app.config.get("GOOGLE_IAP_PUBLIC_KEY_URL")
            try:
                public_key = get_public_key_for_jwt(encoded_jwt, url)
                decoded_jwt = decode_jwt(
                    encoded_jwt, public_key, algorithm, expected_audience
                )
                validate_jwt(decoded_jwt, expected_issuer)
                email = decoded_jwt.get("email")
                if email:
                    user = User.get_or_create(username=email, name=email)
                    login_user(user)

            except (ImportError, NameError, UnboundLocalError):
                raise

            except (
                JwtValidationError,
                JwtKeyError,
                Exception,
            ) as e:
                current_app.logger.error("{}".format(e))

    # SSO login based on environment variable, e.g. REMOTE_USER.
    if current_app.config.get("SSO_ENABLED", False):
        remote_user_env = current_app.config.get("SSO_USER_ENV_VARIABLE", "REMOTE_USER")
        sso_group_env = current_app.config.get("SSO_GROUP_ENV_VARIABLE", None)

        remote_user = request.environ.get(remote_user_env, None)
        if remote_user:
            user = User.get_or_create(username=remote_user, name=remote_user)
            login_user(user)

        # If we get groups from the SSO system create the group(s) in
        # Timesketch and add/remove the user from it.
        if sso_group_env:
            groups_string = request.environ.get(sso_group_env, "")
            separator = current_app.config.get("SSO_GROUP_SEPARATOR", ";")
            not_member_sign = current_app.config.get("SSO_GROUP_NOT_MEMBER_SIGN", None)
            for group_name in groups_string.split(separator):
                remove_group = False
                if not_member_sign:
                    remove_group = group_name.startswith(not_member_sign)
                    group_name = group_name.lstrip(not_member_sign)

                # Get or create the group in the Timesketch database.
                group = Group.get_or_create(name=group_name, display_name=group_name)

                if remove_group:
                    if group in user.groups:
                        user.groups.remove(group)
                else:
                    if group not in user.groups:
                        user.groups.append(group)
            # Commit the changes to the database.
            db_session.add(user)
            db_session.add(group)
            db_session.commit()

    # Login form POST
    # pylint: disable=using-constant-test
    form = UsernamePasswordForm()
    if form.validate_on_submit:
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.check_password(plaintext=form.password.data):
                login_user(user)

    # Log the user in and setup the session.
    if current_user.is_authenticated:
        return redirect(request.args.get("next") or "/")

    return render_template("login.html", form=form)


@auth_views.route("/logout/", methods=["GET"])
def logout():
    """Handler for the logout page view.

    Returns:
        Redirect response.
    """
    logout_user()
    return redirect(url_for("user_views.login"))


@auth_views.route("/login/api_callback/", methods=["GET"])
def validate_api_token():
    """Handler for logging in using an authenticated session for the API.

    Returns:
        A simple page indicating the user is authenticated.
    """
    ALLOWED_CLIENT_IDS = []

    try:
        token = oauth2.rfc6749.tokens.get_token_from_header(request)
    except AttributeError:
        token = None

    if not token:
        return abort(HTTP_STATUS_CODE_UNAUTHORIZED, "Request not authenticated.")

    id_token = request.args.get("id_token")
    if not id_token:
        return abort(HTTP_STATUS_CODE_UNAUTHORIZED, "No ID token supplied.")

    client_ids = set()
    primary_client_id = current_app.config.get("GOOGLE_OIDC_CLIENT_ID")
    legacy_api_client_id = current_app.config.get("GOOGLE_OIDC_API_CLIENT_ID")
    api_client_ids = current_app.config.get("GOOGLE_OIDC_API_CLIENT_IDS", [])

    if primary_client_id:
        client_ids.add(primary_client_id)

    if legacy_api_client_id:
        client_ids.add(legacy_api_client_id)

    if api_client_ids:
        client_ids.update(api_client_ids)

    ALLOWED_CLIENT_IDS = list(client_ids)

    if not ALLOWED_CLIENT_IDS:
        return abort(
            HTTP_STATUS_CODE_BAD_REQUEST,
            "No OIDC client IDs defined in the configuration file.",
        )

    # Authenticating session, see more details here:
    # https://www.oauth.com/oauth2-servers/signing-in-with-google/\
    #     verifying-the-user-info/
    # Sending a request to Google to verify that the access token
    # is valid, to be able to validate the session.
    data = {"access_token": token}
    bearer_token_response = requests.post(TOKEN_URI, data=data)
    if bearer_token_response.status_code != HTTP_STATUS_CODE_OK:
        return abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate access token.")
    bearer_token_json = bearer_token_response.json()

    data = {"id_token": id_token}
    token_response = requests.post(TOKEN_URI, data=data)
    token_json = token_response.json()

    verified = token_json.get("email_verified", False)
    if not verified:
        return abort(
            HTTP_STATUS_CODE_UNAUTHORIZED,
            "Session not authenticated or account not verified",
        )

    if bearer_token_json.get("azp", "a") != token_json.get("azp", "x"):
        return abort(
            HTTP_STATUS_CODE_UNAUTHORIZED,
            "Auth token and client tokens don't match, azp differs.",
        )

    if bearer_token_json.get("email", "a") != token_json.get("email", "b"):
        return abort(
            HTTP_STATUS_CODE_UNAUTHORIZED,
            "Auth token and client tokens don't match, email differs.",
        )

    try:
        discovery_document = get_oauth2_discovery_document()
    except DiscoveryDocumentError as e:
        return abort(
            HTTP_STATUS_CODE_BAD_REQUEST,
            "Unable to discover document, with error: {0!s}".format(e),
        )

    expected_issuer = discovery_document["issuer"]
    # pylint: disable=broad-except
    try:
        validate_jwt(token_json, expected_issuer)
    except (ImportError, NameError, UnboundLocalError):
        raise
    except (
        JwtValidationError,
        JwtKeyError,
        Exception,
    ) as e:
        return abort(
            HTTP_STATUS_CODE_UNAUTHORIZED,
            "Unable to validate the JWT token, with error: {0!s}.".format(e),
        )

    read_client_id = token_json.get("aud", "")
    if read_client_id not in ALLOWED_CLIENT_IDS:
        return abort(
            HTTP_STATUS_CODE_UNAUTHORIZED,
            "Client ID {0:s} does not match server configuration for "
            "client".format(read_client_id),
        )

    read_scopes = bearer_token_json.get("scope", "").split()
    if not set(read_scopes) == set(SCOPES):
        return abort(
            HTTP_STATUS_CODE_UNAUTHORIZED,
            "Client scopes differ from what they should be (email, openid, "
            "profile) = {} VS {}".format(SCOPES, read_scopes),
        )

    validated_email = token_json.get("email")

    # Check if the authenticating user is part of the allowed domains.
    allowed_domains = set()
    hosted_domains = current_app.config.get("GOOGLE_OIDC_HOSTED_DOMAIN")
    api_allowed_domains = current_app.config.get("GOOGLE_OIDC_API_ALLOWED_DOMAINS", [])
    if hosted_domains:
        allowed_domains.add(hosted_domains)
    if api_allowed_domains:
        allowed_domains.update(api_allowed_domains)
    # A list of allowed domains in lower case.
    ALLOWED_DOMAINS = [domain.lower() for domain in allowed_domains]

    if ALLOWED_DOMAINS:
        _, _, domain = validated_email.partition("@")
        if domain.lower() not in ALLOWED_DOMAINS:
            return abort(
                HTTP_STATUS_CODE_UNAUTHORIZED,
                "Domain {0:s} is not allowed to authenticate against this "
                "instance.".format(domain),
            )

    allowed_users = current_app.config.get("GOOGLE_OIDC_ALLOWED_USERS")
    # TODO: Remove that after a 6 months, this following check is to ensure
    # compatibility of config file
    if not allowed_users:
        current_app.logger.warning(
            "Warning, GOOGLE_OIDC_USER_WHITELIST has "
            "been deprecated. Please update "
            "timesketch.conf."
        )
        allowed_users = current_app.config.get("GOOGLE_OIDC_USER_WHITELIST", [])

    # Check if the authenticating user is on the allow list.
    if allowed_users:
        if validated_email not in allowed_users:
            return abort(
                HTTP_STATUS_CODE_UNAUTHORIZED, "Unauthorized request, user not allowed"
            )

    user = User.get_or_create(username=validated_email, name=validated_email)
    login_user(user, remember=True)

    # Log the user in and setup the session.
    if current_user.is_authenticated:
        return """
<h1>Authenticated</h1>
        """

    return abort(HTTP_STATUS_CODE_BAD_REQUEST, "User is not authenticated.")


@auth_views.route("/login/google_openid_connect/", methods=["GET"])
def google_openid_connect():
    """Handler for the Google OpenID Connect callback.

    Reference:
    https://developers.google.com/identity/protocols/OpenIDConnect

    Returns:
        Redirect response.
    """
    error = request.args.get("error", None)

    if error:
        current_app.logger.error("OAuth2 flow error: {}".format(error))
        return abort(
            HTTP_STATUS_CODE_BAD_REQUEST, "OAuth2 flow error: {0!s}".format(error)
        )

    try:
        code = request.args["code"]
        client_csrf_token = request.args.get("state")
        server_csrf_token = session[CSRF_KEY]
    except KeyError as e:
        return abort(
            HTTP_STATUS_CODE_BAD_REQUEST, "Client CSRF error, no CSRF key stored"
        )

    if client_csrf_token != server_csrf_token:
        return abort(HTTP_STATUS_CODE_BAD_REQUEST, "Invalid CSRF token")

    try:
        encoded_jwt = get_encoded_jwt_over_https(code)
    except JwtFetchError as e:
        return abort(HTTP_STATUS_CODE_BAD_REQUEST, "Jwt Fetch error, {0!s}".format(e))

    try:
        discovery_document = get_oauth2_discovery_document()
    except DiscoveryDocumentError as e:
        return abort(
            HTTP_STATUS_CODE_BAD_REQUEST,
            "Unable to discover document, with error: {0!s}".format(e),
        )

    algorithm = discovery_document["id_token_signing_alg_values_supported"][0]
    expected_audience = current_app.config.get("GOOGLE_OIDC_CLIENT_ID")
    expected_domain = current_app.config.get("GOOGLE_OIDC_HOSTED_DOMAIN")
    expected_issuer = discovery_document["issuer"]

    # Fetch the public key and try to validate the JWT.
    try:
        public_key = get_public_key_for_jwt(encoded_jwt, discovery_document["jwks_uri"])
        decoded_jwt = decode_jwt(encoded_jwt, public_key, algorithm, expected_audience)
        validate_jwt(decoded_jwt, expected_issuer, expected_domain)
    except (JwtValidationError, JwtKeyError) as e:
        current_app.logger.error("{}".format(e))
        return abort(
            HTTP_STATUS_CODE_UNAUTHORIZED,
            "Unable to validate request, with error: {0!s}".format(e),
        )

    validated_email = decoded_jwt.get("email")
    allowed_users = current_app.config.get("GOOGLE_OIDC_ALLOWED_USERS")

    # Check if the authenticating user is allowed.
    if allowed_users:
        if validated_email not in allowed_users:
            return abort(
                HTTP_STATUS_CODE_UNAUTHORIZED, "Unauthorized request, user not allowed"
            )

    user = User.get_or_create(username=validated_email, name=validated_email)
    login_user(user)

    # Log the user in and setup the session.
    if current_user.is_authenticated:
        return redirect(session.get("next", "/"))

    return abort(HTTP_STATUS_CODE_BAD_REQUEST, "User is not authenticated.")
