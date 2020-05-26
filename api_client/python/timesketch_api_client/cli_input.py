# Copyright 2020 Google Inc. All rights reserved.
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
"""CLI assistance for importer tools."""

import click

def ask_question(question, input_type, default=None, hide_input=False):
    """Presents the user with a prompt with a default return value and a type.

    Args:
        question (str): the text that the user will be prompted.
        input_type (type): the type of the input data.
        default (object): default value for the question, optional.
        hide_input (bool): whether the input should be hidden, eg. when asking
            for a password.

    Returns:
        object: The value (type of input_type) that is ready by the user.
    """
    if default:
        return click.prompt(
            question, type=input_type, default=default, hide_input=hide_input)
    return click.prompt(question, type=input_type, hide_input=hide_input)


def confirm_choice(choice, default=True, abort=True):
    """Returns a bool from a yes/no question presented to the end user.

    Args:
        choice (str): the question presented to the end user.
        default (bool): the default for the confirmation answer. If True the
            default is Y(es), if False the default is N(o)
        abort (bool): if the program should abort if the user answer to the
            confirm prompt is no. The default is an abort.

    Returns:
        bool: False if the user entered no, True if the user entered yes
    """
    return click.confirm(choice, abort=abort, default=default)
