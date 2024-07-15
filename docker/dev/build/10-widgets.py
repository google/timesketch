from picatrix.lib import utils
import ipywidgets as widgets
from IPython.display import Markdown
from timesketch_api_client import search, config
from picatrix.lib import state as state_lib

import altair as alt
import numpy as np
import pandas as pd

state = state_lib.state()


def generate_connect_button(click_function=None):
    """Creates a button and an int form to connect to timesketch."""
    button = widgets.Button(description="Connect to sketch")
    output = widgets.Output()

    sketch_field = widgets.IntText(value=1, description="Sketch ID:", disabled=False)

    display(Markdown("## Connect to a sketch"))
    display(Markdown("Select a sketch to connect to."))
    display(sketch_field, button, output)

    def _click_function(_):
        with output:
            id = str(sketch_field.value)
            ts_client = config.get_client()
            sketch = ts_client.get_sketch(id)
            try:
                display(
                    Markdown(f"Connected to sketch: {sketch.id}: **{sketch.name}**")
                )
                valid = widgets.Valid(value=True, description="Connected")
                display(valid)
                utils.ipython_bind_global("sketch", sketch)
                display(Markdown("Sketch object saved to **sketch**"))
            except KeyError:
                display(Markdown("**Unable to connect to sketch.**"))
                invalid = widgets.Valid(value=False, description="Connected")
                display(invalid)

    if click_function:
        button.on_click(click_function)
    else:
        button.on_click(_click_function)
