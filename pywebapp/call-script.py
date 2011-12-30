"""Incomplete support file for calling scripts.

The motivation is in part to create a clean environment for calling a script.
"""

import sys
import os

pywebapp_location = os.environ['PYWEBAPP_LOCATION']
if pywebapp_location not in sys.path:
    sys.path.insert(0, pywebapp_location)
    ## Doesn't also pick up yaml and maybe other modules, but at least
    ## a try?
del os.environ['PYWEBAPP_LOCATION']

import pywebapp


def main():
    appdir = sys.argv[1]
    script_path = sys.argv[2]
    rest = sys.argv[3:]
    app = pywebapp.PyWebApp.from_path(appdir)
    app.setup_settings()
    setup_services(app)
    app.activate_path()
    sys.argv[0] = script_path
    sys.argv[1:] = rest
    ns = dict(__name__='__main__', __file__=script_path)
    execfile(script_path, ns)


## FIXME: this is where I started confused, because we have to call
## back into the container at this point.
def setup_services(app):
    service_setup = os.environ['PYWEBAPP_SERVICE_SETUP']
    mod, callable = service_setup.split(':', 1)
    __import__(mod)
    mod = sys.modules[mod]
    callable = getattr(mod, callable)
    callable(app)


if __name__ == '__main__':
    main()
