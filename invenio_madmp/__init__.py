# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for maDMP integration."""

from .ext import InvenioMaDMP
from .proxies import current_madmp
from .version import __version__

__all__ = ("__version__", "current_madmp", "InvenioMaDMP")
