# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for maDMP integration."""

from datetime import datetime

from flask_httpauth import HTTPTokenAuth

from . import config


class InvenioMaDMP(object):
    """Invenio-maDMP extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        self.auth = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["invenio-madmp"] = self
        self.auth = HTTPTokenAuth(scheme="Bearer", header="Authorization")
        self.set_up_rest_auth(app)
        self.register_signal_handlers(app)

        if not hasattr(datetime, "fromisoformat"):
            from backports.datetime_fromisoformat import MonkeyPatch

            MonkeyPatch.patch_fromisoformat()

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("MADMP_"):
                app.config.setdefault(k, getattr(config, k))

    def set_up_rest_auth(self, app):
        """Set up the token verification for the REST endpoints."""

        @self.auth.verify_token
        def verify_token(token):
            expected_token = app.config["MADMP_COMMUNICATION_TOKEN"]
            if expected_token is None:
                return True
            elif token == expected_token:
                return True

            return False

    def register_signal_handlers(self, app):
        """Connect the signals to their configured handlers."""
        for signal, handler in app.config["MADMP_SIGNAL_HANDLERS"]:
            signal.connect(handler)
