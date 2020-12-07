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
"""Few functions that take advantage of ipywidgets for jupyter.

These are temporary functions until they have been generalized
and implemented in picatrix.
"""
import ipywidgets as widgets


# TODO: Generalize and move to picatrix.
def generate_connect_button(click_function = None):
  """Creates a button and an int form to connect to timesketch."""
  button = widgets.Button(description='Connect to sketch')
  output = widgets.Output()

  sketch_field = widgets.IntText(
      value=1,
      description='Sketch ID:',
      disabled=False
  )

  display(sketch_field, button, output)

  def _click_function(b):
      with output:
          timesketch_set_active_sketch_func(str(sketch_field.value))
          sketch = %timesketch_get_sketch
          print(f'Connected to sketch: {sketch.id}:{sketch.name}')

  if click_function:
    button.on_click(click_function)
  else:
    button.on_click(_click_function)

