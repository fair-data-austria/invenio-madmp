# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for maDMP integration."""

from datetime import datetime

from flask_babelex import gettext as _

from . import config


class InvenioMaDMP(object):
    """Invenio-maDMP extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["invenio-madmp"] = self

        if not hasattr(datetime, "fromisoformat"):
            from backports.datetime_fromisoformat import MonkeyPatch

            MonkeyPatch.patch_fromisoformat()

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("MADMP_"):
                app.config.setdefault(k, getattr(config, k))
