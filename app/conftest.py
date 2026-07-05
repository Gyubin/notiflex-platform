# Empty on purpose: its presence makes pytest add app/ (this file's
# directory) to sys.path, so tests can do `from main import app`
# without installing the app as a package.
