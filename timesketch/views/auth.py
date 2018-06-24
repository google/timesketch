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

from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user

from timesketch.lib.forms import UsernamePasswordForm
from timesketch.lib.google_jwt import get_public_key_for_jwt
from timesketch.lib.google_jwt import validate_jwt
from timesketch.lib.google_jwt import JwtValidationError
from timesketch.lib.google_jwt import JwtKeyError
from timesketch.models import db_session
from timesketch.models.user import Group
from timesketch.models.user import User

# Register flask blueprint
auth_views = Blueprint(u'user_views', __name__)


@auth_views.route(u'/login/', methods=[u'GET', u'POST'])
def login():
    """Handler for the login page view.

    There are three ways of authentication.
    1) Google Cloud Identity-Aware Proxy.
    2) If Single Sign On (SSO) is enabled in the configuration and the
       environment variable is present, e.g. REMOTE_USER then the system will
       get or create the user object and setup a session for the user.
    3) Local authentication is used if SSO login is not enabled. This will
       authenticate the user against the local user database.

    Returns:
        Redirect if authentication is successful or template with context
        otherwise.
    """

    # Google Identity-Aware Proxy authentication (using JSON Web Tokens)
    if current_app.config.get(u'GOOGLE_IAP_ENABLED', False):
        encoded_jwt = request.environ.get(
            u'HTTP_X_GOOG_IAP_JWT_ASSERTION', None)
        if encoded_jwt:
            expected_audience = current_app.config.get(u'GOOGLE_IAP_AUDIENCE')
            expected_issuer = current_app.config.get(u'GOOGLE_IAP_ISSUER')
            algorithm = current_app.config.get(u'GOOGLE_IAP_ALGORITHM')
            url = current_app.config.get(u'GOOGLE_IAP_PUBLIC_KEY_URL')
            try:
                public_key = get_public_key_for_jwt(encoded_jwt, url)
                validated_jwt = validate_jwt(
                    encoded_jwt, public_key, algorithm, expected_audience,
                    expected_issuer)
                email = validated_jwt.get(u'email')
                if email:
                    user = User.get_or_create(username=email, name=email)
                    login_user(user)
            except (JwtValidationError, JwtKeyError, Exception) as e:
                current_app.logger.error('{}'.format(e))

    # SSO login based on environment variable, e.g. REMOTE_USER.
    if current_app.config.get(u'SSO_ENABLED', False):
        remote_user_env = current_app.config.get(u'SSO_USER_ENV_VARIABLE',
                                                 u'REMOTE_USER')
        sso_group_env = current_app.config.get(u'SSO_GROUP_ENV_VARIABLE', None)

        remote_user = request.environ.get(remote_user_env, None)
        if remote_user:
            user = User.get_or_create(username=remote_user, name=remote_user)
            login_user(user)

        # If we get groups from the SSO system create the group(s) in
        # Timesketch and add/remove the user from it.
        if sso_group_env:
            groups_string = request.environ.get(sso_group_env, u'')
            separator = current_app.config.get(u'SSO_GROUP_SEPARATOR', u';')
            not_member_sign = current_app.config.get(
                u'SSO_GROUP_NOT_MEMBER_SIGN', None)
            for group_name in groups_string.split(separator):
                remove_group = False
                if not_member_sign:
                    remove_group = group_name.startswith(not_member_sign)
                    group_name = group_name.lstrip(not_member_sign)

                # Get or create the group in the Timesketch database.
                group = Group.get_or_create(name=group_name)

                if remove_group:
                    if group in user.groups:
                        user.groups.remove(group)
                else:
                    if group not in user.groups:
                        user.groups.append(group)
            # Commit the changes to the database.
            db_session.commit()

    # Login form POST
    form = UsernamePasswordForm()
    if form.validate_on_submit:
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.check_password(plaintext=form.password.data):
                login_user(user)

    # Log the user in and setup the session.
    if current_user.is_authenticated:
        return redirect(request.args.get(u'next') or u'/')

    return render_template(u'user/login.html', form=form)


@auth_views.route(u'/logout/', methods=[u'GET'])
def logout():
    """Handler for the logout page view.

    Returns:
        Redirect response.
    """
    logout_user()
    return redirect(url_for(u'user_views.login'))
