# Copyright 2018 Google Inc. All rights reserved.
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
"""Emoji codepoint definitions.

See https://emojipedia.org for list of available unicode emojis.
"""

from __future__ import unicode_literals

import collections


emoji = collections.namedtuple('emoji', 'code help')


EMOJI_MAP = {
    'CAMERA': emoji('&#x1F4F7', 'Screenshot activity'),
    'FISHING_POLE': emoji('&#x1F3A3', 'Phishing'),
    'ID_BUTTON': emoji('&#x1F194', 'Account ID'),
    'LINK': emoji('&#x1F517', 'Events Linked'),
    'LOCK': emoji('&#x1F512', 'Logon activity'),
    'LOCOMOTIVE': emoji('&#x1F682', 'Execution activity'),
    'MAGNIFYING_GLASS': emoji('&#x1F50E', 'Search related activity'),
    'SATELLITE': emoji('&#x1F4E1', 'Domain activity'),
    'SCREEN': emoji('&#x1F5B5', 'Screensaver activity'),
    'SKULL': emoji('&#x1F480;', 'Threat intel match'),
    'SKULL_CROSSBONE': emoji('&#x2620', 'Suspicious entry'),
    'SLEEPING_FACE': emoji('&#x1F634', 'Activity outside of regular hours'),
    'UNLOCK': emoji('&#x1F513', 'Logoff activity'),
    'WASTEBASKET': emoji('&#x1F5D1', 'Deletion activity')
}


def get_emoji(name):
    """Returns a Unicode for an emoji given the name or blank if not saved.

    Args:
        name: string with the emoji name.

    Returns:
        Unicode string for the emoji if it exists or a blank string otherwise.
    """
    name_upper = name.upper()
    emoji_object = EMOJI_MAP.get(name_upper)
    if emoji_object:
        return emoji_object.code
    return ''


def get_helper_from_unicode(code):
    """Returns a helper string from an emoji Unicode code point.

    Args:
        code: a Unicode code point for an emoji.

    Returns:
        Helper text as a string or an empty string if emoji is not configured.
    """
    code_upper = code.upper()
    for emoji_object in iter(EMOJI_MAP.values()):
        if code_upper == emoji_object.code.upper():
            return emoji_object.help
    return ''


def get_emojis_as_dict():
    """Returns a dictionary with emoji codes and helper texts.

    Returns:
        Dict with emoji unicode code points as key and helper text as value.
    """
    return {e.code: e.help for e in iter(EMOJI_MAP.values())}
