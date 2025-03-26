// Code cell snippets

define([
    'base/js/namespace',
], function(
    Jupyter,
) {
    "use strict";

    // will be called when the nbextension is loaded
    function load_extension() {
        var ncells = Jupyter.notebook.ncells();
        if (ncells > 1) {
          return true;
        }

        var new_cell = Jupyter.notebook.insert_cell_above('markdown', 0);
        new_cell.set_text('# Timesketch Notebook\nThis is a base notebook for connecting to a dev instance of Timesketch.\n**Remember to rename the notebook**.');
        new_cell.render();
        new_cell.focus_cell();

        var new_cell = Jupyter.notebook.insert_cell_below('markdown');
        new_cell.set_text('*If you want to query data you can use the snippets menu, or create a search obj, and to display a table use `display_table(search_obj.table)` or `display_table(data_frame)`*\n\nTo see a list of available helper functions run `%picatrixhelpers` in a cell, or to see a list of functions/magics use `%picatrixmagics`.');
        new_cell.render();

        var select_cell = Jupyter.notebook.insert_cell_below('code');
        select_cell.set_text('generate_connect_button()');

        var text_cell = Jupyter.notebook.insert_cell_below('markdown');
        text_cell.set_text('## Select a Sketch.\nNow it is time to select a sketch to use, first execute the cell and then change the ID of the sketch to the one you want, and press the button.');
        text_cell.render();

        var import_cell = Jupyter.notebook.insert_cell_below('code');
        import_cell.set_text('from timesketch_api_client import search\nfrom picatrix.lib import state as state_lib\n\nimport altair as alt\nimport numpy as np\nimport pandas as pd\n\nstate = state_lib.state()');

        var new_cell = Jupyter.notebook.insert_cell_below('markdown');
        new_cell.set_text('## Import\nTo start a notebook we import few base libraries.\nExecute the cell below by pressing the play button or using "shift + enter"');
        new_cell.render();
        import_cell.focus_cell();
    };

    // return public methods
    return {
        load_ipython_extension : load_extension
    };
});
