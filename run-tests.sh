#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

docker-services-cli up postgresql es redis && \
pydocstyle invenio_madmp tests docs && \
isort --check-only --diff --recursive invenio_madmp tests && \
check-manifest --ignore ".travis-*" && \
sphinx-build -qnNW docs docs/_build/html && \
pytest

tests_exit_code=$?
docker-services-cli down
exit "$tests_exit_code"
