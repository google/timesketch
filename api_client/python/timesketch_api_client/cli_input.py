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

from typing import Any
from typing import Callable
from typing import Optional
from typing import Text

import getpass


def ask_question(
        question: Text, input_type: Callable[[Text], Any],
        default: Optional[Any] = None,
        hide_input: Optional[bool] = False) -> Any:
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
    if hide_input:
        if default:
            hint = '**'
        else:
            hint = ''

        return getpass.getpass(f'{question} [{hint}] ')

    if default:
        ask = f'{question} [{default}]'
    else:
        ask = question

    answer = input(f'{ask}: ')
    return input_type(answer)


def confirm_choice(
        choice: Text, default: Optional[bool] = True,
        abort: Optional[bool] = True) -> bool:
    """Returns a bool from a yes/no question presented to the end user.

    Args:
        choice (str): the question presented to the end user.
        default (bool): the default for the confirmation answer. If True the
            default is Y(es), if False the default is N(o)
        abort (bool): if the program should abort if the user answer to the
            confirm prompt is no. The default is an abort.

    Raises:
        RuntimeError: If abort is set to True and the choice is no.

    Returns:
        bool: False if the user entered no, True if the user entered yes
    """
    if default:
        hint = 'Y/n'
    else:
        hint = 'y/N'
    answer = input(f'{choice} [{hint}]: ')

    value = None
    if answer.lower() in ['y', 'yes']:
        value = True

    if answer.lower() in ['n', 'no']:
        value = False

    if not answer:
        value = default

    if value is None:
        print('Invalid answer')
        return confirm_choice(choice=choice, default=default, abort=abort)

    if abort and not value:
        raise RuntimeError('Aborting')

    return value
