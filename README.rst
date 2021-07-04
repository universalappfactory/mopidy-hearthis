****************************
Mopidy-Hearthis
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Hearthis
    :target: https://pypi.org/project/Mopidy-Hearthis/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/github/workflow/status/universalappfactory/mopidy-hearthis/CI
    :target: https://github.com/universalappfactory/mopidy-hearthis/actions
    :alt: CI build status

.. image:: https://img.shields.io/codecov/c/gh/universalappfactory/mopidy-hearthis
    :target: https://codecov.io/gh/universalappfactory/mopidy-hearthis
    :alt: Test coverage

A mopidy backend to stream music from hearthis.at.

Still at an early state but already working.
Results from hearthis.at are not paged yet so results are limited to 20 Tracks at the moment.



Installation
============

Install by running::

    python3 -m pip install Mopidy-Hearthis


Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Hearthis to your Mopidy configuration file::

    [hearthis]
    enabled: True
    username: your_hearthis_username
    password: your_hearthis_password

You can obtain a login here Hearthis_.

At the moment you need to have an email and password as login, the other login methods provided by HearThis_ are not yet supported.


Project resources
=================

- `Source code <https://github.com/universalappfactory/mopidy-hearthis>`_
- `Issue tracker <https://github.com/universalappfactory/mopidy-hearthis/issues>`_
- `Changelog <https://github.com/universalappfactory/mopidy-hearthis/blob/master/CHANGELOG.rst>`_


Credits
=======

- Original author: `universalappfactory <https://github.com/universalappfactory>`__
- Current maintainer: `universalappfactory <https://github.com/universalappfactory>`__
- `Contributors <https://github.com/universalappfactory/mopidy-hearthis/graphs/contributors>`_

.. _HearThis: https://hearthis.at/