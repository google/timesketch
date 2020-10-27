from timesketch.lib.graphs.interface import BaseGraph
from timesketch.lib.graphs import manager
import json
import networkx as nx
from networkx.readwrite.json_graph import cytoscape_data


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
            query_string=query, return_fields=return_fields, indices=['7ec551b2f04f4eb09d68ad395dde2e43'])

        G = nx.DiGraph()
        for event in events:
            computer_name = event['_source'].get('computer_name')
            username = event['_source'].get('username')
            logon_type = event['_source'].get('logon_type')
            G.add_node(computer_name)
            G.add_node(username)
            G.add_edge(username, computer_name, logon_type=logon_type)

        print(json.dumps(cytoscape_data(G), indent=2))


manager.GraphManager.register_graph(WinLoginsGraph)
