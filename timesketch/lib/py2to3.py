# -*- coding: utf-8 -*-
"""The Python 2 and 3 compatible type definitions.

File copied from the plaso project.
"""
import sys

# pylint: disable=invalid-name,undefined-variable
if sys.version_info[0] < 3:
    PY_2 = True
    PY_3 = False
    BYTES_TYPE = str
    INTEGER_TYPES = (int, long)
    LONG_TYPE = long
    STRING_TYPES = (basestring, )
    UNICHR = unichr
    UNICODE_TYPE = unicode
else:
    PY_2 = False
    PY_3 = True
    BYTES_TYPE = bytes
    INTEGER_TYPES = (int, )
    LONG_TYPE = int
    STRING_TYPES = (str, )
    UNICHR = chr
    UNICODE_TYPE = str

PY_3_5_AND_LATER = bool(tuple(sys.version_info[0:2]) >= (3, 5))
