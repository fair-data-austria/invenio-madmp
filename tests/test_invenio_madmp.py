# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from flask import Flask

from invenio_madmp import InveniomaDMP


def test_version():
    """Test version import."""
    from invenio_madmp import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InveniomaDMP(app)
    assert 'invenio-madmp' in app.extensions

    app = Flask('testapp')
    ext = InveniomaDMP()
    assert 'invenio-madmp' not in app.extensions
    ext.init_app(app)
    assert 'invenio-madmp' in app.extensions
