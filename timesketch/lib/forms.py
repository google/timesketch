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

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_wtf.file import FileField
from flask_wtf.file import FileRequired
from wtforms import widgets
from wtforms.fields import BooleanField
from wtforms.fields import HiddenField
from wtforms.fields import IntegerField
from wtforms.fields import PasswordField
from wtforms.fields import RadioField
from wtforms.fields import SelectField
from wtforms.fields import SelectMultipleField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import Regexp


class MultiDict(dict):
    """Implements a MultiDict that can hold keys with the same name."""

    # WTForms expects the form data to be a MultiDict, i.e. a dictionary that
    # can hold multiple keys with the same name.
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


class BaseForm(FlaskForm):
    """Base class for forms."""

    @classmethod
    def build(cls, request):
        """Build a WTForm from request data and add CSRF token.

        Args:
            request: Flask request object as a werkzeug request proxy.

        Returns:
            A filled out WTForm form. Instance of timesketch.lib.forms.
        """
        form_dict = MultiDict(request.json)
        form_dict[u'csrf_token'] = request.headers.get(u'X-CSRFToken')
        return cls(form_dict)


class MultiCheckboxField(SelectMultipleField):
    """Multiple checkbox form widget."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class AddTimelineForm(BaseForm):
    """Form using multiple checkbox fields to add timelines to a sketch."""
    timelines = MultiCheckboxField(u'Timelines', coerce=int)


class AddTimelineSimpleForm(BaseForm):
    """Form to add timelines to a sketch."""
    timeline = IntegerField(u'Timeline', validators=[DataRequired()])


class UsernamePasswordForm(BaseForm):
    """Form with username and password fields. Use in the login form."""
    username = StringField(u'Email', validators=[DataRequired()])
    password = PasswordField(u'Password', validators=[DataRequired()])


class NameDescriptionForm(BaseForm):
    """Generic form for name and description forms. Used in multiple places."""
    name = StringField(u'Name', validators=[DataRequired()])
    description = StringField(u'Description', widget=widgets.TextArea())


class HiddenNameDescriptionForm(BaseForm):
    """
    Form for name and description fields, but as hidden values. Used when
    creating a new sketch.
    """
    name = HiddenField(
        u'Name', default=u'Untitled sketch', validators=[DataRequired()])
    description = HiddenField(u'Description')


class CreateTimelineForm(BaseForm):
    """Form to handle ad-hoc timeline creation."""
    name = StringField(u'Timeline name', validators=[Optional()])
    sketch_id = IntegerField(u'Sketch ID', validators=[Optional()])


class TimelineForm(NameDescriptionForm):
    """Form to edit a timeline."""
    color = StringField(
        u'Color',
        validators=[DataRequired(),
                    Regexp(u'^[0-9a-fA-F]{6}$'),
                    Length(6, 6)])


class TogglePublic(BaseForm):
    """Form to toggle the public ACL permission."""
    permission = RadioField(
        u'Permission',
        choices=[(u'public', u'Public'), (u'private', u'Private')],
        validators=[DataRequired()])
    username = StringField(u'User')
    groups = SelectField(
        u'Groups', choices=[], coerce=int, validators=[Optional()])
    remove_groups = MultiCheckboxField(
        u'Remove groups', coerce=int, validators=[Optional()])
    remove_users = MultiCheckboxField(
        u'Remove users', coerce=int, validators=[Optional()])


class SaveViewForm(BaseForm):
    """Form used to save a view."""
    name = StringField(u'Name')
    query = StringField(u'Query')
    filter = StringField(u'Filter')
    dsl = StringField(u'DSL')
    new_searchtemplate = BooleanField(
        u'Create search template',
        false_values={False, u'false', u''},
        default=False)
    from_searchtemplate_id = IntegerField(u'Create from search template')


class ExploreForm(BaseForm):
    """Form used to search the datastore."""
    query = StringField(u'Query')
    filter = StringField(u'Filter')
    dsl = StringField(u'DSL')


class GraphExploreForm(BaseForm):
    """Form used to search the graph datastore."""
    query = StringField(u'Query')
    output_format = StringField(u'Output format')


class AggregationForm(ExploreForm):
    """Form used to search the datastore."""
    aggtype = StringField(u'Aggregation type')


class StatusForm(BaseForm):
    """Form to handle status annotation."""
    status = SelectField(
        u'Status',
        choices=[(u'new', u'New'), (u'open', u'Open'), (u'closed', u'Closed')],
        validators=[DataRequired()])


class TrashForm(BaseForm):
    """Form to handle thrash confirmation."""
    confirm = BooleanField(u'Trash', validators=[DataRequired()])


class TrashViewForm(BaseForm):
    """Form to handle thrash view confirmation."""
    view_id = IntegerField(u'View ID', validators=[DataRequired()])


class EventCreateForm(BaseForm):
    """Generic form to handle event addition. E.g. message and timestamp."""
    timestamp = StringField(u'timestamp', validators=[DataRequired()])
    timestamp_desc = StringField(u'timestamp_desc', validators=[DataRequired()])
    message = StringField(u'message', validators=[DataRequired()])


class EventAnnotationForm(BaseForm):
    """Generic form to handle event annotation. E.g. comment and labels."""
    annotation = StringField(u'Annotation', validators=[DataRequired()])
    annotation_type = StringField(u'Type', validators=[DataRequired()])
    events = StringField(u'Events', validators=[DataRequired()])


class UploadFileForm(BaseForm):
    """Form to handle file uploads."""
    file = FileField(
        u'file',
        validators=[
            FileRequired(),
            FileAllowed([u'plaso', u'csv', u'jsonl'],
                        u'Allowed file extensions: .plaso, .csv, or .jsonl')
        ])
    name = StringField(u'Timeline name', validators=[Optional()])
    sketch_id = IntegerField(u'Sketch ID', validators=[Optional()])


class StoryForm(BaseForm):
    """Form to handle stories."""
    title = StringField(u'Title', validators=[])
    content = StringField(u'Content', validators=[], widget=widgets.TextArea())


class SearchIndexForm(BaseForm):
    """Form to create a searchindex."""
    searchindex_name = StringField(u'name', validators=[DataRequired()])
    es_index_name = StringField(u'Index', validators=[DataRequired()])
    public = BooleanField(
        u'Public', false_values={False, u'false', u''}, default=False)
