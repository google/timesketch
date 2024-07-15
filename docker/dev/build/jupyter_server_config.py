# Configuration file for jupyter-server.

c = get_config()  # noqa

c.ServerApp.port = 8080
c.ServerApp.root_dir = "/home/jovyan/work"
c.ServerApp.allow_unauthenticated_access = True
c.ServerApp.token = ""
