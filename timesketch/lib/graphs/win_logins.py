from timesketch.lib.graphs.interface import BaseGraph
from timesketch.lib.graphs import manager
import networkx as nx


class WinLoginsGraph(BaseGraph):

    NAME = 'WinLogins'

    def generate(self):
        query = 'tag:logon-event'

        return_fields = [
            'computer_name', 'event_identifier', 'logon_type', 'logon_process',
            'username'
        ]

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields, indices=['_all'])

        graph = nx.DiGraph()
        for event in events:
            computer_name = event['_source'].get('computer_name')
            username = event['_source'].get('username')
            logon_type = event['_source'].get('logon_type')
            graph.add_node(computer_name, label=computer_name, type='computer')
            graph.add_node(username, label=username, type='username')
            graph.add_edge(username, computer_name, label=logon_type)

        cytoscape_json = nx.readwrite.json_graph.cytoscape_data(graph)
        #return cytoscape_json.get('elements', [])
        return graph


manager.GraphManager.register_graph(WinLoginsGraph)
