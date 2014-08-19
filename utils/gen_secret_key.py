# Copyright 2014 Google Inc. All rights reserved.
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
"""Generate a random string for the SECRET_KEY setting"""

from django.utils.crypto import get_random_string
import string


def generate_secret_key():
    allowed_chars = string.letters + string.digits + string.punctuation
    return get_random_string(length=50, allowed_chars=allowed_chars)

if __name__ == "__main__":
    print generate_secret_key()
