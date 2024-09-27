# Configuration file for jupyter-server.

c = get_config()  # noqa

c.ServerApp.ip = "0.0.0.0"
c.ServerApp.port = 8080
c.ServerApp.allow_origin = "*"
c.ServerApp.root_dir = "/home/jovyan/work"

# Authentication should be done with an authentication system.
c.ServerApp.allow_unauthenticated_access = True
c.ServerApp.disable_check_xsrf = True
c.ServerApp.token = ""
