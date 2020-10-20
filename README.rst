..
    Copyright (C) 2020 FAIR Data Austria.

    Invenio-maDMP is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

===============
 Invenio-maDMP
===============

.. image:: https://img.shields.io/travis/fair-data-austria/invenio-madmp.svg
        :target: https://travis-ci.org/fair-data-austria/invenio-madmp

.. image:: https://img.shields.io/coveralls/fair-data-austria/invenio-madmp.svg
        :target: https://coveralls.io/r/fair-data-austria/invenio-madmp

.. image:: https://img.shields.io/github/tag/fair-data-austria/invenio-madmp.svg
        :target: https://github.com/fair-data-austria/invenio-madmp/releases

.. image:: https://img.shields.io/github/license/fair-data-austria/invenio-madmp.svg
        :target: https://github.com/fair-data-austria/invenio-madmp/blob/master/LICENSE

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


Invenio module for integrating machine-actionable data management plans (maDMPs)
according to the `Research Data Alliance Common Standard <https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard>`_.


The aim of this module is to support researchers in depositing their research data
in accordance with their data management plans (DMPs) by exchanging maDMPs
with external DMP tools.


Since some of the information that is relevant as metadata for records is already
defined in the DMPs for their research projects, it is only natural to use DMPs
as a source for partially pre-filled metadata.



Features:

* Workflows for parsing maDMPs and creating new record drafts with pre-filled metadata
  from the parsed information, or updating the metadata of already existing records
  (respectively, drafts)
* Generic RecordConverter class for translating between maDMP datasets (respectively,
  distributions) and records (and drafts) in Invenio, intended to be subclassed to
  match custom metadata models
* REST endpoints for communication with external DMP tools



Further documentation is available on
https://invenio-madmp.readthedocs.io/
