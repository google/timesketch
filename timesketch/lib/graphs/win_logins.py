from timesketch.lib.graphs.interface import BaseGraphPlugin
from timesketch.lib.graphs import manager


class WinLoginsGraph(BaseGraphPlugin):

    NAME = 'WinLogins'
    DISPLAY_NAME = 'Windows logins'

    GRAPH_TYPE = 'DiGraph'

    def generate(self):
        query = 'tag:logon-event'
        return_fields = [
            'computer_name', 'event_identifier', 'logon_type', 'logon_process',
            'username'
        ]

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields, indices=['_all'])

        for event in events:
            computer_name = event['_source'].get('computer_name')
            username = event['_source'].get('username')
            logon_type = event['_source'].get('logon_type')

            computer = self.graph.add_node(computer_name, {'type': 'computer'})
            user = self.graph.add_node(username, {'type': 'username'})
            self.graph.add_edge(user, computer, logon_type, event)

        self.graph.commit()

        return self.graph


manager.GraphManager.register_graph(WinLoginsGraph)
