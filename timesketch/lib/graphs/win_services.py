from timesketch.lib.graphs.interface import BaseGraphPlugin
from timesketch.lib.graphs import manager


class WinServiceGraph(BaseGraphPlugin):

    NAME = 'WinService'
    DISPLAY_NAME = 'Windows services'

    def generate(self):
        query = 'event_identifier:7045'

        return_fields = ['computer_name', 'username', 'strings']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields, indices=['_all'])

        for event in events:
            computer_name = event['_source'].get('computer_name')
            username = event['_source'].get('username')
            event_strings = event['_source'].get('strings')
            service_name = event_strings[0]
            image_path = event_strings[1]
            service_type = event_strings[2]
            start_type = event_strings[3]

            computer = self.graph.add_node(computer_name, {'type': 'computer'})
            user = self.graph.add_node(username, {'type': 'username'})
            service = self.graph.add_node(service_name, {'type': 'winservice'})

            self.graph.add_edge(user, service, start_type, event)
            self.graph.add_edge(service, computer, service_type, event)

        self.graph.commit()

        return self.graph


manager.GraphManager.register_graph(WinServiceGraph)
