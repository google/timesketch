from timesketch.lib.graphs.interface import BaseGraph
from timesketch.lib.graphs import manager
import networkx as nx


class WinServiceGraph(BaseGraph):

    NAME = 'WinService'

    def generate(self):
        query = 'event_identifier:7045'

        return_fields = ['computer_name', 'username', 'strings']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields, indices=['_all'])

        graph = nx.DiGraph()
        for event in events:
            computer_name = event['_source'].get('computer_name')
            username = event['_source'].get('username')
            event_strings = event['_source'].get('strings')
            service_name = event_strings[0]
            image_path = event_strings[1]
            service_type = event_strings[2]
            start_type = event_strings[3]
            graph.add_node(computer_name, label=computer_name, type='computer')
            graph.add_node(username, label=username, type='username')
            graph.add_node(service_name, label=service_name, type='win_service')

            graph.add_edge(username, service_name, label=start_type)
            graph.add_edge(service_name, computer_name, label=service_type)

        cytoscape_json = nx.readwrite.json_graph.cytoscape_data(graph)
        return cytoscape_json.get('elements', [])


manager.GraphManager.register_graph(WinServiceGraph)
