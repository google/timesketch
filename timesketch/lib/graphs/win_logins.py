from timesketch.lib.graphs.interface import BaseGraph
from timesketch.lib.graphs import manager
import networkx as nx
import hashlib


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
            computer_name_id = hashlib.md5(computer_name.encode('utf-8')).hexdigest()
            username_id = hashlib.md5(username.encode('utf-8')).hexdigest()

            graph.add_node(computer_name_id, label=computer_name, type='computer')
            graph.add_node(username_id, label=username, type='username')

            graph.add_edge(username_id, computer_name_id, label=logon_type, es_index=event['_index'], es_doc_id=event['_id'])

        cytoscape_json = nx.readwrite.json_graph.cytoscape_data(graph)
        return cytoscape_json.get('elements', [])


manager.GraphManager.register_graph(WinLoginsGraph)
