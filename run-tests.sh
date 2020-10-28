#!/bin/bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

start_docker=1
keep_docker=0

while getopts "sSkKh" arg; do
	case $arg in
		h)
			echo "usage: $0 [-s|-S] [-k|-K] [-h]"
			echo "    -h         display this help message and exit"
			echo "    -s | -S    start docker containers before tests (default: yes)"
			echo "    -k | -K    stop docker containers after tests (default: yes)"
			exit 0
			;;
		s)
			start_docker=1
			;;
		S)
			start_docker=0
			;;
		k)
			keep_docker=1
			;;
		K)
			keep_docker=0
			;;
	esac
done

# start docker containers before testing, if requested
if [[ $start_docker -eq 1 ]]; then
	docker-services-cli up postgresql es redis

	exit_code=$?
	[[ $exit_code -ne 0 ]] && exit $exit_code
fi

# do the usual stuff
pydocstyle invenio_madmp tests docs && \
isort --check-only --diff --recursive invenio_madmp tests && \
check-manifest --ignore ".travis-*" && \
sphinx-build -qnNW docs docs/_build/html && \
pytest
tests_exit_code=$?

# optionally, keep docker containers running (for quicker re-run of tests)
[[ $keep_docker -eq 0 ]] && docker-services-cli down

exit $tests_exit_code
