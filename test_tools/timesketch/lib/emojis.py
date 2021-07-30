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
    'WASTEBASKET': emoji('&#x1F5D1', 'Deletion activity'),
    'AC': emoji('&#x1F1E6&#x1F1E8', 'Ascension Island'),
    'AD': emoji('&#x1F1E6&#x1F1E9', 'Andorra'),
    'AE': emoji('&#x1F1E6&#x1F1EA', 'United Arab Emirates'),
    'AF': emoji('&#x1F1E6&#x1F1EB', 'Afghanistan'),
    'AG': emoji('&#x1F1E6&#x1F1EC', 'Antigua & Barbuda'),
    'AI': emoji('&#x1F1E6&#x1F1EE', 'Anguilla'),
    'AL': emoji('&#x1F1E6&#x1F1F1', 'Albania'),
    'AM': emoji('&#x1F1E6&#x1F1F2', 'Armenia'),
    'AO': emoji('&#x1F1E6&#x1F1F4', 'Angola'),
    'AQ': emoji('&#x1F1E6&#x1F1F6', 'Antarctica'),
    'AR': emoji('&#x1F1E6&#x1F1F7', 'Argentina'),
    'AS': emoji('&#x1F1E6&#x1F1F8', 'American Samoa'),
    'AT': emoji('&#x1F1E6&#x1F1F9', 'Austria'),
    'AU': emoji('&#x1F1E6&#x1F1FA', 'Australia'),
    'AW': emoji('&#x1F1E6&#x1F1FC', 'Aruba'),
    'AX': emoji('&#x1F1E6&#x1F1FD', 'Åland Islands'),
    'AZ': emoji('&#x1F1E6&#x1F1FF', 'Azerbaijan'),
    'BA': emoji('&#x1F1E7&#x1F1E6', 'Bosnia & Herzegovina'),
    'BB': emoji('&#x1F1E7&#x1F1E7', 'Barbados'),
    'BD': emoji('&#x1F1E7&#x1F1E9', 'Bangladesh'),
    'BE': emoji('&#x1F1E7&#x1F1EA', 'Belgium'),
    'BF': emoji('&#x1F1E7&#x1F1EB', 'Burkina Faso'),
    'BG': emoji('&#x1F1E7&#x1F1EC', 'Bulgaria'),
    'BH': emoji('&#x1F1E7&#x1F1ED', 'Bahrain'),
    'BI': emoji('&#x1F1E7&#x1F1EE', 'Burundi'),
    'BJ': emoji('&#x1F1E7&#x1F1EF', 'Benin'),
    'BL': emoji('&#x1F1E7&#x1F1F1', 'St. Barthélemy'),
    'BM': emoji('&#x1F1E7&#x1F1F2', 'Bermuda'),
    'BN': emoji('&#x1F1E7&#x1F1F3', 'Brunei'),
    'BO': emoji('&#x1F1E7&#x1F1F4', 'Bolivia'),
    'BQ': emoji('&#x1F1E7&#x1F1F6', 'Caribbean Netherlands'),
    'BR': emoji('&#x1F1E7&#x1F1F7', 'Brazil'),
    'BS': emoji('&#x1F1E7&#x1F1F8', 'Bahamas'),
    'BT': emoji('&#x1F1E7&#x1F1F9', 'Bhutan'),
    'BV': emoji('&#x1F1E7&#x1F1FB', 'Bouvet Island'),
    'BW': emoji('&#x1F1E7&#x1F1FC', 'Botswana'),
    'BY': emoji('&#x1F1E7&#x1F1FE', 'Belarus'),
    'BZ': emoji('&#x1F1E7&#x1F1FF', 'Belize'),
    'CA': emoji('&#x1F1E8&#x1F1E6', 'Canada'),
    'CC': emoji('&#x1F1E8&#x1F1E8', 'Cocos (Keeling) Islands'),
    'CD': emoji('&#x1F1E8&#x1F1E9', 'Congo - Kinshasa'),
    'CF': emoji('&#x1F1E8&#x1F1EB', 'Central African Republic'),
    'CG': emoji('&#x1F1E8&#x1F1EC', 'Congo - Brazzaville'),
    'CH': emoji('&#x1F1E8&#x1F1ED', 'Switzerland'),
    'CI': emoji('&#x1F1E8&#x1F1EE', 'Côte d’Ivoire'),
    'CK': emoji('&#x1F1E8&#x1F1F0', 'Cook Islands'),
    'CL': emoji('&#x1F1E8&#x1F1F1', 'Chile'),
    'CM': emoji('&#x1F1E8&#x1F1F2', 'Cameroon'),
    'CN': emoji('&#x1F1E8&#x1F1F3', 'China'),
    'CO': emoji('&#x1F1E8&#x1F1F4', 'Colombia'),
    'CP': emoji('&#x1F1E8&#x1F1F5', 'Clipperton Island'),
    'CR': emoji('&#x1F1E8&#x1F1F7', 'Costa Rica'),
    'CU': emoji('&#x1F1E8&#x1F1FA', 'Cuba'),
    'CV': emoji('&#x1F1E8&#x1F1FB', 'Cape Verde'),
    'CW': emoji('&#x1F1E8&#x1F1FC', 'Curaçao'),
    'CX': emoji('&#x1F1E8&#x1F1FD', 'Christmas Island'),
    'CY': emoji('&#x1F1E8&#x1F1FE', 'Cyprus'),
    'CZ': emoji('&#x1F1E8&#x1F1FF', 'Czechia'),
    'DE': emoji('&#x1F1E9&#x1F1EA', 'Germany'),
    'DG': emoji('&#x1F1E9&#x1F1EC', 'Diego Garcia'),
    'DJ': emoji('&#x1F1E9&#x1F1EF', 'Djibouti'),
    'DK': emoji('&#x1F1E9&#x1F1F0', 'Denmark'),
    'DM': emoji('&#x1F1E9&#x1F1F2', 'Dominica'),
    'DO': emoji('&#x1F1E9&#x1F1F4', 'Dominican Republic'),
    'DZ': emoji('&#x1F1E9&#x1F1FF', 'Algeria'),
    'EA': emoji('&#x1F1EA&#x1F1E6', 'Ceuta & Melilla'),
    'EC': emoji('&#x1F1EA&#x1F1E8', 'Ecuador'),
    'EE': emoji('&#x1F1EA&#x1F1EA', 'Estonia'),
    'EG': emoji('&#x1F1EA&#x1F1EC', 'Egypt'),
    'EH': emoji('&#x1F1EA&#x1F1ED', 'Western Sahara'),
    'ER': emoji('&#x1F1EA&#x1F1F7', 'Eritrea'),
    'ES': emoji('&#x1F1EA&#x1F1F8', 'Spain'),
    'ET': emoji('&#x1F1EA&#x1F1F9', 'Ethiopia'),
    'EU': emoji('&#x1F1EA&#x1F1FA', 'European Union'),
    'FI': emoji('&#x1F1EB&#x1F1EE', 'Finland'),
    'FJ': emoji('&#x1F1EB&#x1F1EF', 'Fiji'),
    'FK': emoji('&#x1F1EB&#x1F1F0', 'Falkland Islands'),
    'FM': emoji('&#x1F1EB&#x1F1F2', 'Micronesia'),
    'FO': emoji('&#x1F1EB&#x1F1F4', 'Faroe Islands'),
    'FR': emoji('&#x1F1EB&#x1F1F7', 'France'),
    'GA': emoji('&#x1F1EC&#x1F1E6', 'Gabon'),
    'GB': emoji('&#x1F1EC&#x1F1E7', 'United Kingdom'),
    'GD': emoji('&#x1F1EC&#x1F1E9', 'Grenada'),
    'GE': emoji('&#x1F1EC&#x1F1EA', 'Georgia'),
    'GF': emoji('&#x1F1EC&#x1F1EB', 'French Guiana'),
    'GG': emoji('&#x1F1EC&#x1F1EC', 'Guernsey'),
    'GH': emoji('&#x1F1EC&#x1F1ED', 'Ghana'),
    'GI': emoji('&#x1F1EC&#x1F1EE', 'Gibraltar'),
    'GL': emoji('&#x1F1EC&#x1F1F1', 'Greenland'),
    'GM': emoji('&#x1F1EC&#x1F1F2', 'Gambia'),
    'GN': emoji('&#x1F1EC&#x1F1F3', 'Guinea'),
    'GP': emoji('&#x1F1EC&#x1F1F5', 'Guadeloupe'),
    'GQ': emoji('&#x1F1EC&#x1F1F6', 'Equatorial Guinea'),
    'GR': emoji('&#x1F1EC&#x1F1F7', 'Greece'),
    'GS': emoji('&#x1F1EC&#x1F1F8', 'South Georgia & South Sandwich Islands'),
    'GT': emoji('&#x1F1EC&#x1F1F9', 'Guatemala'),
    'GU': emoji('&#x1F1EC&#x1F1FA', 'Guam'),
    'GW': emoji('&#x1F1EC&#x1F1FC', 'Guinea-Bissau'),
    'GY': emoji('&#x1F1EC&#x1F1FE', 'Guyana'),
    'HK': emoji('&#x1F1ED&#x1F1F0', 'Hong Kong SAR China'),
    'HM': emoji('&#x1F1ED&#x1F1F2', 'Heard & McDonald Islands'),
    'HN': emoji('&#x1F1ED&#x1F1F3', 'Honduras'),
    'HR': emoji('&#x1F1ED&#x1F1F7', 'Croatia'),
    'HT': emoji('&#x1F1ED&#x1F1F9', 'Haiti'),
    'HU': emoji('&#x1F1ED&#x1F1FA', 'Hungary'),
    'IC': emoji('&#x1F1EE&#x1F1E8', 'Canary Islands'),
    'ID': emoji('&#x1F1EE&#x1F1E9', 'Indonesia'),
    'IE': emoji('&#x1F1EE&#x1F1EA', 'Ireland'),
    'IL': emoji('&#x1F1EE&#x1F1F1', 'Israel'),
    'IM': emoji('&#x1F1EE&#x1F1F2', 'Isle of Man'),
    'IN': emoji('&#x1F1EE&#x1F1F3', 'India'),
    'IO': emoji('&#x1F1EE&#x1F1F4', 'British Indian Ocean Territory'),
    'IQ': emoji('&#x1F1EE&#x1F1F6', 'Iraq'),
    'IR': emoji('&#x1F1EE&#x1F1F7', 'Iran'),
    'IS': emoji('&#x1F1EE&#x1F1F8', 'Iceland'),
    'IT': emoji('&#x1F1EE&#x1F1F9', 'Italy'),
    'JE': emoji('&#x1F1EF&#x1F1EA', 'Jersey'),
    'JM': emoji('&#x1F1EF&#x1F1F2', 'Jamaica'),
    'JO': emoji('&#x1F1EF&#x1F1F4', 'Jordan'),
    'JP': emoji('&#x1F1EF&#x1F1F5', 'Japan'),
    'KE': emoji('&#x1F1F0&#x1F1EA', 'Kenya'),
    'KG': emoji('&#x1F1F0&#x1F1EC', 'Kyrgyzstan'),
    'KH': emoji('&#x1F1F0&#x1F1ED', 'Cambodia'),
    'KI': emoji('&#x1F1F0&#x1F1EE', 'Kiribati'),
    'KM': emoji('&#x1F1F0&#x1F1F2', 'Comoros'),
    'KN': emoji('&#x1F1F0&#x1F1F3', 'St. Kitts & Nevis'),
    'KP': emoji('&#x1F1F0&#x1F1F5', 'North Korea'),
    'KR': emoji('&#x1F1F0&#x1F1F7', 'South Korea'),
    'KW': emoji('&#x1F1F0&#x1F1FC', 'Kuwait'),
    'KY': emoji('&#x1F1F0&#x1F1FE', 'Cayman Islands'),
    'KZ': emoji('&#x1F1F0&#x1F1FF', 'Kazakhstan'),
    'LA': emoji('&#x1F1F1&#x1F1E6', 'Laos'),
    'LB': emoji('&#x1F1F1&#x1F1E7', 'Lebanon'),
    'LC': emoji('&#x1F1F1&#x1F1E8', 'St. Lucia'),
    'LI': emoji('&#x1F1F1&#x1F1EE', 'Liechtenstein'),
    'LK': emoji('&#x1F1F1&#x1F1F0', 'Sri Lanka'),
    'LR': emoji('&#x1F1F1&#x1F1F7', 'Liberia'),
    'LS': emoji('&#x1F1F1&#x1F1F8', 'Lesotho'),
    'LT': emoji('&#x1F1F1&#x1F1F9', 'Lithuania'),
    'LU': emoji('&#x1F1F1&#x1F1FA', 'Luxembourg'),
    'LV': emoji('&#x1F1F1&#x1F1FB', 'Latvia'),
    'LY': emoji('&#x1F1F1&#x1F1FE', 'Libya'),
    'MA': emoji('&#x1F1F2&#x1F1E6', 'Morocco'),
    'MC': emoji('&#x1F1F2&#x1F1E8', 'Monaco'),
    'MD': emoji('&#x1F1F2&#x1F1E9', 'Moldova'),
    'ME': emoji('&#x1F1F2&#x1F1EA', 'Montenegro'),
    'MF': emoji('&#x1F1F2&#x1F1EB', 'St. Martin'),
    'MG': emoji('&#x1F1F2&#x1F1EC', 'Madagascar'),
    'MH': emoji('&#x1F1F2&#x1F1ED', 'Marshall Islands'),
    'MK': emoji('&#x1F1F2&#x1F1F0', 'Macedonia'),
    'ML': emoji('&#x1F1F2&#x1F1F1', 'Mali'),
    'MM': emoji('&#x1F1F2&#x1F1F2', 'Myanmar (Burma)'),
    'MN': emoji('&#x1F1F2&#x1F1F3', 'Mongolia'),
    'MO': emoji('&#x1F1F2&#x1F1F4', 'Macao SAR China'),
    'MP': emoji('&#x1F1F2&#x1F1F5', 'Northern Mariana Islands'),
    'MQ': emoji('&#x1F1F2&#x1F1F6', 'Martinique'),
    'MR': emoji('&#x1F1F2&#x1F1F7', 'Mauritania'),
    'MS': emoji('&#x1F1F2&#x1F1F8', 'Montserrat'),
    'MT': emoji('&#x1F1F2&#x1F1F9', 'Malta'),
    'MU': emoji('&#x1F1F2&#x1F1FA', 'Mauritius'),
    'MV': emoji('&#x1F1F2&#x1F1FB', 'Maldives'),
    'MW': emoji('&#x1F1F2&#x1F1FC', 'Malawi'),
    'MX': emoji('&#x1F1F2&#x1F1FD', 'Mexico'),
    'MY': emoji('&#x1F1F2&#x1F1FE', 'Malaysia'),
    'MZ': emoji('&#x1F1F2&#x1F1FF', 'Mozambique'),
    'NA': emoji('&#x1F1F3&#x1F1E6', 'Namibia'),
    'NC': emoji('&#x1F1F3&#x1F1E8', 'New Caledonia'),
    'NE': emoji('&#x1F1F3&#x1F1EA', 'Niger'),
    'NF': emoji('&#x1F1F3&#x1F1EB', 'Norfolk Island'),
    'NG': emoji('&#x1F1F3&#x1F1EC', 'Nigeria'),
    'NI': emoji('&#x1F1F3&#x1F1EE', 'Nicaragua'),
    'NL': emoji('&#x1F1F3&#x1F1F1', 'Netherlands'),
    'NO': emoji('&#x1F1F3&#x1F1F4', 'Norway'),
    'NP': emoji('&#x1F1F3&#x1F1F5', 'Nepal'),
    'NR': emoji('&#x1F1F3&#x1F1F7', 'Nauru'),
    'NU': emoji('&#x1F1F3&#x1F1FA', 'Niue'),
    'NZ': emoji('&#x1F1F3&#x1F1FF', 'New Zealand'),
    'OM': emoji('&#x1F1F4&#x1F1F2', 'Oman '),
    'PA': emoji('&#x1F1F5&#x1F1E6', 'Panama'),
    'PE': emoji('&#x1F1F5&#x1F1EA', 'Peru'),
    'PF': emoji('&#x1F1F5&#x1F1EB', 'French Polynesia'),
    'PG': emoji('&#x1F1F5&#x1F1EC', 'Papua New Guinea'),
    'PH': emoji('&#x1F1F5&#x1F1ED', 'Philippines'),
    'PK': emoji('&#x1F1F5&#x1F1F0', 'Pakistan'),
    'PL': emoji('&#x1F1F5&#x1F1F1', 'Poland'),
    'PM': emoji('&#x1F1F5&#x1F1F2', 'St. Pierre & Miquelon'),
    'PN': emoji('&#x1F1F5&#x1F1F3', 'Pitcairn Islands'),
    'PR': emoji('&#x1F1F5&#x1F1F7', 'Puerto Rico'),
    'PS': emoji('&#x1F1F5&#x1F1F8', 'Palestinian Territories'),
    'PT': emoji('&#x1F1F5&#x1F1F9', 'Portugal'),
    'PW': emoji('&#x1F1F5&#x1F1FC', 'Palau'),
    'PY': emoji('&#x1F1F5&#x1F1FE', 'Paraguay'),
    'QA': emoji('&#x1F1F6&#x1F1E6', 'Qatar'),
    'RE': emoji('&#x1F1F7&#x1F1EA', 'Réunion'),
    'RO': emoji('&#x1F1F7&#x1F1F4', 'Romania'),
    'RS': emoji('&#x1F1F7&#x1F1F8', 'Serbia'),
    'RU': emoji('&#x1F1F7&#x1F1FA', 'Russia'),
    'RW': emoji('&#x1F1F7&#x1F1FC', 'Rwanda'),
    'SA': emoji('&#x1F1F8&#x1F1E6', 'Saudi Arabia'),
    'SB': emoji('&#x1F1F8&#x1F1E7', 'Solomon Islands'),
    'SC': emoji('&#x1F1F8&#x1F1E8', 'Seychelles'),
    'SD': emoji('&#x1F1F8&#x1F1E9', 'Sudan'),
    'SE': emoji('&#x1F1F8&#x1F1EA', 'Sweden'),
    'SG': emoji('&#x1F1F8&#x1F1EC', 'Singapore'),
    'SH': emoji('&#x1F1F8&#x1F1ED', 'St. Helena'),
    'SI': emoji('&#x1F1F8&#x1F1EE', 'Slovenia'),
    'SJ': emoji('&#x1F1F8&#x1F1EF', 'Svalbard & Jan Mayen'),
    'SK': emoji('&#x1F1F8&#x1F1F0', 'Slovakia'),
    'SL': emoji('&#x1F1F8&#x1F1F1', 'Sierra Leone'),
    'SM': emoji('&#x1F1F8&#x1F1F2', 'San Marino'),
    'SN': emoji('&#x1F1F8&#x1F1F3', 'Senegal'),
    'SO': emoji('&#x1F1F8&#x1F1F4', 'Somalia'),
    'SR': emoji('&#x1F1F8&#x1F1F7', 'Suriname'),
    'SS': emoji('&#x1F1F8&#x1F1F8', 'South Sudan'),
    'ST': emoji('&#x1F1F8&#x1F1F9', 'São Tomé & Príncipe'),
    'SV': emoji('&#x1F1F8&#x1F1FB', 'El Salvador'),
    'SC': emoji('&#x1F1F8&#x1F1FD', 'Sint Maarten'),
    'SY': emoji('&#x1F1F8&#x1F1FE', 'Syria'),
    'SZ': emoji('&#x1F1F8&#x1F1FF', 'Eswatini'),
    'TA': emoji('&#x1F1F9&#x1F1E6', 'Tristan da Cunha'),
    'TC': emoji('&#x1F1F9&#x1F1E8', 'Turks & Caicos Islands'),
    'TD': emoji('&#x1F1F9&#x1F1E9', 'Chad'),
    'TF': emoji('&#x1F1F9&#x1F1EB', 'French Southern Territories'),
    'TG': emoji('&#x1F1F9&#x1F1EC', 'Togo'),
    'TH': emoji('&#x1F1F9&#x1F1ED', 'Thailand'),
    'TJ': emoji('&#x1F1F9&#x1F1EF', 'Tajikistan'),
    'TK': emoji('&#x1F1F9&#x1F1F0', 'Tokelau'),
    'TL': emoji('&#x1F1F9&#x1F1F1', 'Timor-Leste'),
    'TM': emoji('&#x1F1F9&#x1F1F2', 'Turkmenistan'),
    'TN': emoji('&#x1F1F9&#x1F1F3', 'Tunisia'),
    'TO': emoji('&#x1F1F9&#x1F1F4', 'Tonga'),
    'TR': emoji('&#x1F1F9&#x1F1F7', 'Turkey'),
    'TT': emoji('&#x1F1F9&#x1F1F9', 'Trinidad & Tobago'),
    'TV': emoji('&#x1F1F9&#x1F1FB', 'Tuvalu'),
    'TW': emoji('&#x1F1F9&#x1F1FC', 'Taiwan'),
    'TZ': emoji('&#x1F1F9&#x1F1FF', 'Tanzania'),
    'UA': emoji('&#x1F1FA&#x1F1E6', 'Ukraine'),
    'UG': emoji('&#x1F1FA&#x1F1EC', 'Uganda'),
    'UM': emoji('&#x1F1FA&#x1F1F2', 'U.S. Outlying Islands'),
    'UN': emoji('&#x1F1FA&#x1F1F3', 'United Nations'),
    'US': emoji('&#x1F1FA&#x1F1F8', 'United States'),
    'UY': emoji('&#x1F1FA&#x1F1FE', 'Uruguay'),
    'UZ': emoji('&#x1F1FA&#x1F1FF', 'Uzbekistan'),
    'VA': emoji('&#x1F1FB&#x1F1E6', 'Vatican City'),
    'VC': emoji('&#x1F1FB&#x1F1E8', 'St. Vincent & Grenadines'),
    'VE': emoji('&#x1F1FB&#x1F1EA', 'Venezuela'),
    'VG': emoji('&#x1F1FB&#x1F1EC', 'British Virgin Islands'),
    'VI': emoji('&#x1F1FB&#x1F1EE', 'U.S. Virgin Islands'),
    'VN': emoji('&#x1F1FB&#x1F1F3', 'Vietnam'),
    'VU': emoji('&#x1F1FB&#x1F1FA', 'Vanuatu'),
    'WF': emoji('&#x1F1FC&#x1F1EB', 'Wallis & Futuna'),
    'WS': emoji('&#x1F1FC&#x1F1F8', 'Samoa'),
    'XK': emoji('&#x1F1FD&#x1F1F0', 'Kosovo'),
    'YE': emoji('&#x1F1FE&#x1F1EA', 'Yemen'),
    'YT': emoji('&#x1F1FE&#x1F1F9', 'Mayotte'),
    'ZA': emoji('&#x1F1FF&#x1F1E6', 'South Africa'),
    'ZM': emoji('&#x1F1FF&#x1F1F2', 'Zambia'),
    'ZW': emoji('&#x1F1FF&#x1F1FC', 'Zimbabwe'),
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
