========
Unchartd
========

Unchartd is an experiment to explore Untappd checkins with Elasticsearch
and d3.js.



Requirements
============

Unchartd requires:

* pyelasticsearch
* python-dateutil
* requests


Installation
============

Do::

    $ git clone git://github.com/robhudson/unchartd.git
    $ cd unchartd

Create your Python virtualenv and install the required packages::

    $ mkvirtualenv unchartd
    $ pip install -r requirements.txt

Install and run Elasticsearch. Docs for this can be found here:
http://www.elasticsearch.org/guide/reference/setup/installation/

Untappd API Credentials
=======================

You'll need Untappd API credentials, which can be obtained here:
https://untappd.com/api/dashboard

When you have credentials export them to your environment via::

    $ export UNTAPPD_CLIENT_ID='<client_id>'
    $ export UNTAPPD_CLIENT_SECRET='<client_secret>'

Importing checkins
==================

To import all your checkins run the following command from the git
checkout directory::

    $ python process.py

This will create the index named 'unchartd' with doctype 'checkins'. When
it finishes it will report the number of checkins imported. Once finished
explore your checkins with Elasticsearch.

TODO
====

* Implement various charts using d3.js

  * Punchcard chart for checkins by date/time
  * Map of brewery location checkins
  * Beers by %ABV
  * Beers by day of week
  * Other ideas?
