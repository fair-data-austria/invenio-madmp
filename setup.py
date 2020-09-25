# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for maDMP integration."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'pytest-invenio>=1.3.2',
    'invenio-config>=1.0.3',
    'invenio-rdm-records>=0.18.0,<0.19',  # TODO 0.19 starts having issues with other pacakges
    'invenio-records-permissions>=0.9.0,<0.10',  # TODO >= 0.10.0
    'flask-resources>=0.2.1,<=0.3.1',  # TODO >=0.3.2
    'SQLAlchemy-Utils>=0.33.1,<0.36', # FIXME without this: ContextualVersionConflict {invenio-files-rest}
    'invenio-search[elasticsearch7]>=1.3.1',
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'mysql': [
        'invenio-db[mysql]>=1.0.0',
    ],
    'postgresql': [
        'invenio-db[postgresql]>=1.0.0',
    ],
    'sqlite': [
        'invenio-db>=1.0.0',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask-BabelEx>=0.9.4',
    'invenio-records>=1.3.2,<2.0.0',
    'invenio-pidstore>=1.2.1',
    'invenio-records>=1.3.2',
    'invenio-db>=1.0.0',
    'invenio-accounts>=1.3.0',
    'backports-datetime-fromisoformat>=1.0 ; python_version<"3.7"',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_madmp', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-madmp',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio TODO',
    license='MIT',
    author='FAIR Data Austria',
    author_email='maximilian.moser@tuwien.ac.at',
    url='https://github.com/fair-data-austria/invenio-madmp',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'madmp = invenio_madmp.cli:madmp'
        ],
        'invenio_base.apps': [
            'invenio_madmp = invenio_madmp:InvenioMaDMP',
        ],
        'invenio_base.blueprints': [
            'invenio_madmp = invenio_madmp.views:rest_blueprint'
        ],
        'invenio_i18n.translations': [
            'messages = invenio_madmp',
        ],
        'invenio_db.models': [
            'invenio_madmp = invenio_madmp.models'
        ]
        # TODO: Edit these entry points to fit your needs.
        # 'invenio_access.actions': [],
        # 'invenio_admin.actions': [],
        # 'invenio_assets.bundles': [],
        # 'invenio_base.api_apps': [],
        # 'invenio_base.api_blueprints': [],
        # 'invenio_base.blueprints': [],
        # 'invenio_celery.tasks': [],
        # 'invenio_db.models': [],
        # 'invenio_pidstore.minters': [],
        # 'invenio_records.jsonresolver': [],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Development Status :: 3 - Alpha',
    ],
)
