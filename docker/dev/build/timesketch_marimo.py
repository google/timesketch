"""Helpers for using the Timesketch API client from marimo notebooks."""

import marimo as mo
from timesketch_api_client import config


def sketch_selector():
    """Returns a number input and a run button used to pick a sketch."""
    sketch_id = mo.ui.number(start=1, step=1, value=1, label="Sketch ID")
    connect = mo.ui.run_button(label="Connect to sketch")
    return sketch_id, connect


def connect_to_sketch(sketch_id, connect):
    """Connects to the sketch once the button is pressed.

    Returns (sketch, message); sketch is None if not connected.
    """
    mo.stop(not connect.value, mo.md("Select a sketch and press connect."))
    ts_client = config.get_client()
    try:
        sketch = ts_client.get_sketch(int(sketch_id.value))
        return sketch, mo.md(f"Connected to sketch: {sketch.id}: **{sketch.name}**")
    except KeyError:
        return None, mo.md("**Unable to connect to sketch.**")
