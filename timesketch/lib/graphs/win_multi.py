from timesketch.lib.graphs.interface import BaseGraph
from timesketch.lib.graphs import manager
import networkx as nx


class WinMultiGraph(BaseGraph):

    NAME = 'WinMulti'

    def generate(self):

        graph1 = manager.GraphManager.get_graph('winlogins')().generate()
        graph2 = manager.GraphManager.get_graph('winservice')().generate()
        multi_graph = nx.compose(graph1, graph2)
        cytoscape_json = nx.readwrite.json_graph.cytoscape_data(multi_graph)
        return cytoscape_json.get('elements', [])


manager.GraphManager.register_graph(WinMultiGraph)
