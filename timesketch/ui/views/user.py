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
from flask import redirect
from flask import render_template
from flask import url_for
from flask_login import login_user
from flask_login import logout_user

from timesketch.lib.forms import UsernamePasswordForm
from timesketch.models.user import User


# Register flask blueprint
user_views = Blueprint('user_views', __name__)


@user_views.route('/login/', methods=['GET', 'POST'])
def login():
    """Handler for the login page view.

    Returns:
        Template with context.
    """
    form = UsernamePasswordForm()

    # Login form POST
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.check_password(plaintext=form.password.data):
                login_user(user)
                return redirect(url_for('home_views.home'))
        else:
            return redirect(url_for('user_views.login'))
    return render_template('user/login.html', form=form)


@user_views.route('/logout/', methods=['GET'])
def logout():
    """Handler for the logout page view.

    Returns:
        Redirect response.
    """
    logout_user()
    return redirect(url_for('user_views.login'))
