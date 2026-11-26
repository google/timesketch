import marimo

app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from timesketch_marimo import connect_to_sketch, sketch_selector

    return connect_to_sketch, mo, sketch_selector


@app.cell
def _(mo):
    mo.md(
        """
        # Timesketch Notebook
        This is a base notebook for connecting to Timesketch.

        **Remember to rename the notebook**.

        ## Select a Sketch
        Change the ID of the sketch to the one you want, and press the button.
        """
    )
    return


@app.cell
def _(sketch_selector):
    sketch_id, connect = sketch_selector()
    [sketch_id, connect]
    return connect, sketch_id


@app.cell
def _(connect, connect_to_sketch, sketch_id):
    sketch, status = connect_to_sketch(sketch_id, connect)
    status
    return (sketch,)


@app.cell
def _(mo):
    mo.md(
        """
        # Documentation

        [https://timesketch.org/developers/api-client/](https://timesketch.org/developers/api-client/)
        """
    )
    return


if __name__ == "__main__":
    app.run()
