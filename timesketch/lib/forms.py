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

from __future__ import unicode_literals

from flask_wtf import FlaskForm
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
        form_dict["csrf_token"] = request.headers.get("X-CSRFToken")
        return cls(form_dict)


class MultiCheckboxField(SelectMultipleField):
    """Multiple checkbox form widget."""

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class AddTimelineForm(BaseForm):
    """Form using multiple checkbox fields to add timelines to a sketch."""

    timelines = MultiCheckboxField("Timelines", coerce=int)


class AddTimelineSimpleForm(BaseForm):
    """Form to add timelines to a sketch."""

    timeline = IntegerField("Timeline", validators=[DataRequired()])


class UsernamePasswordForm(BaseForm):
    """Form with username and password fields. Use in the login form."""

    username = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class NameDescriptionForm(BaseForm):
    """Generic form for name and description forms. Used in multiple places."""

    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(
                max=255,
                message="Name must be less than 255 characters.",
            ),
        ],
    )
    description = StringField("Description", widget=widgets.TextArea())


class HiddenNameDescriptionForm(BaseForm):
    """
    Form for name and description fields, but as hidden values. Used when
    creating a new sketch.
    """

    name = HiddenField("Name", default="Untitled sketch", validators=[DataRequired()])
    description = HiddenField("Description")


class CreateTimelineForm(BaseForm):
    """Form to handle ad-hoc timeline creation."""

    name = StringField("Timeline name", validators=[Optional()])
    sketch_id = IntegerField("Sketch ID", validators=[Optional()])


class TimelineForm(NameDescriptionForm):
    """Form to edit a timeline."""

    labels = StringField("Labels", validators=[Optional()])
    label_action = StringField("LabelAction", validators=[Optional()])
    color = StringField(
        "Color", validators=[DataRequired(), Regexp("^[0-9a-fA-F]{6}$"), Length(6, 6)]
    )


class TogglePublic(BaseForm):
    """Form to toggle the public ACL permission."""

    permission = RadioField(
        "Permission",
        choices=[("public", "Public"), ("private", "Private")],
        validators=[DataRequired()],
    )
    username = StringField("User")
    groups = SelectField("Groups", choices=[], coerce=int, validators=[Optional()])
    remove_groups = MultiCheckboxField(
        "Remove groups", coerce=int, validators=[Optional()]
    )
    remove_users = MultiCheckboxField(
        "Remove users", coerce=int, validators=[Optional()]
    )


class SaveViewForm(BaseForm):
    """Form used to save a view."""

    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(
                max=255,
                message="Name must be less than 255 characters.",
            ),
        ],
    )
    description = StringField("Description", validators=[Optional()])
    query = StringField("Query")
    filter = StringField("Filter")
    dsl = StringField("DSL")
    new_searchtemplate = BooleanField(
        "Create search template", false_values={False, "false", ""}, default=False
    )
    from_searchtemplate_id = IntegerField("Create from search template")


class ExploreForm(BaseForm):
    """Form used to search the datastore."""

    query = StringField("Query")
    filter = StringField("Filter")
    dsl = StringField("DSL")
    fields = StringField("Fields", default="")
    count = BooleanField(
        "Only Count Events", false_values={False, "false", ""}, default=False
    )
    enable_scroll = BooleanField(
        "Enable scroll", false_values={False, "false", ""}, default=False
    )
    scroll_id = StringField("Scroll ID", default="")
    file_name = StringField("Export to File")


class GraphExploreForm(BaseForm):
    """Form used to search the graph datastore."""

    graph_view_id = IntegerField("Query ID")
    parameters = StringField("Parameters")
    output_format = StringField("Output format")


class AggregationExploreForm(BaseForm):
    """Form used to send aggregation requests to the datastore."""

    aggregation_dsl = StringField("Aggregation DSL", validators=[Optional()])
    aggregator_name = StringField("Aggregator Name", validators=[Optional()])
    aggregator_parameters = StringField(
        "Aggregator Parameters", validators=[Optional()]
    )


class AggregationLegacyForm(ExploreForm):
    """Form used to search the datastore."""

    aggtype = StringField("Aggregation type")


class StatusForm(BaseForm):
    """Form to handle status annotation."""

    status = SelectField(
        "Status",
        choices=[("new", "New"), ("open", "Open"), ("closed", "Closed")],
        validators=[DataRequired()],
    )


class TrashForm(BaseForm):
    """Form to handle thrash confirmation."""

    confirm = BooleanField("Trash", validators=[DataRequired()])


class TrashViewForm(BaseForm):
    """Form to handle thrash view confirmation."""

    view_id = IntegerField("View ID", validators=[DataRequired()])


class EventAnnotationForm(BaseForm):
    """Generic form to handle event annotation. E.g. comment and labels."""

    annotation = StringField("Annotation", validators=[DataRequired()])
    annotation_type = StringField("Type", validators=[DataRequired()])
    events = StringField("Events", validators=[DataRequired()])
    remove = BooleanField("Remove", false_values={False, "false", ""}, default=False)


class StoryForm(BaseForm):
    """Form to handle stories."""

    title = StringField("Title", validators=[])
    content = StringField("Content", validators=[], widget=widgets.TextArea())


class SearchIndexForm(BaseForm):
    """Form to create a searchindex."""

    searchindex_name = StringField("name", validators=[DataRequired()])
    es_index_name = StringField("Index", validators=[DataRequired()])
    public = BooleanField("Public", false_values={False, "false", ""}, default=False)
