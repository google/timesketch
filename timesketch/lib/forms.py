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
"""Form definitions and validators for the forms used in the application."""


from flask_wtf import Form
from wtforms import widgets
from wtforms.fields import StringField
from wtforms.fields import PasswordField
from wtforms.fields import SelectMultipleField
from wtforms.fields import RadioField
from wtforms.fields import HiddenField
from wtforms.fields import SelectField
from wtforms.fields import BooleanField
from wtforms.validators import DataRequired
from wtforms.validators import Regexp
from wtforms.validators import Length


def build_form(request, form):
    """WTForms need this in order to initialize the form."""
    # TODO: Add link to why this is needed.
    form_dict = MultiDict(request.json)
    form_dict['csrf_token'] = request.headers.get('X-CSRFToken')
    return form(form_dict)


class MultiDict(dict):
    """WTForms need this."""
    # TODO: Add link to why this is needed.
    def getlist(self, key):
        """Make sure value is a list.

        Args:
            key: key in dict

        Returns:
            Value for the key in the dict as a list
        """
        val = self[key]
        if not isinstance(val, list):
            val = [val]
        return val

    def getall(self, key):
        """Get value for key as list.

        Args:
            key: key in dict

        Returns:
            Value for the key in the dict as a list
        """
        return [self[key]]


class MultiCheckboxField(SelectMultipleField):
    """Multiple checkbox form widget."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class AddTimelineForm(Form):
    """Form using multiple checkbox fields to add timelines to a sketch."""
    timelines = MultiCheckboxField('Timelines', coerce=int)


class UsernamePasswordForm(Form):
    """Form with username and password fields. Use in the login form."""
    username = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class NameDescriptionForm(Form):
    """Generic form for name and description forms. Used in multiple places."""
    name = StringField('Name', validators=[DataRequired()])
    description = StringField(
        'Description', validators=[DataRequired()], widget=widgets.TextArea())


class HiddenNameDescriptionForm(Form):
    """
    Form for name and description fields, but as hidden values. Used when
    creating a new sketch.
    """
    name = HiddenField(
        'Name', default='Untitled sketch', validators=[DataRequired()])
    description = HiddenField(
        'Description', default='No description', validators=[DataRequired()])


class TimelineForm(NameDescriptionForm):
    """Form to edit a timeline."""
    color = StringField(
        'Color', validators=[
            DataRequired(),
            Regexp('^[0-9a-fA-F]{6}$'),
            Length(6, 6)])


class TogglePublic(Form):
    """Form to toggle the public ACL permission."""
    permission = RadioField(
        'Permission', choices=[('public', 'Public'), ('private', 'Private')],
        validators=[DataRequired()])


class SaveViewForm(Form):
    """Form used to save a view."""
    name = StringField('Name', validators=[DataRequired()])
    query = StringField('Query')
    filter = StringField('Filter', validators=[DataRequired()])


class StatusForm(Form):
    """Form to handle status annotation."""
    status = SelectField(
        'Status',
        choices=[('new', 'New'), ('open', 'Open'), ('closed', 'Closed')],
        validators=[DataRequired()])


class TrashForm(Form):
    """Form to handle thrash confirmation."""
    confirm = BooleanField('Trash', validators=[DataRequired()])


class EventAnnotationForm(Form):
    """Generic form to handle event annotation. E.g. comment and labels."""
    annotation = StringField('Annotation', validators=[DataRequired()])
    annotation_type = StringField('Type', validators=[DataRequired()])
    searchindex_id = StringField('Searchindex', validators=[DataRequired()])
    event_id = StringField('Event', validators=[DataRequired()])
