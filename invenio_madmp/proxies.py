"""Helper proxies for Invenio-MaDMP."""

from flask import current_app
from werkzeug.local import LocalProxy

current_madmp = LocalProxy(lambda: current_app.extensions["invenio-madmp"])
