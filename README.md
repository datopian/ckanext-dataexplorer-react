[![CKAN](https://img.shields.io/badge/ckan-2.8.7-orange.svg?style=flat-square)](https://github.com/ckan/ckan)

A Data Explorer app for CKAN built in React:

* Preview data from DataStore in a table
* Filter data using SQL-like query builder which calls `datastore_search_sql` API
* Build charts and maps similar to classic Data Explorer

The React repository is here - https://github.com/datopian/data-explorer

### Installation

To install ckanext-dataexplorer-react:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-dataexplorer-react Python package into your virtual environment::
   `pip install -e git+https://github.com/datopian/ckanext-dataexplorer-react.git#egg=ckanext-dataexplorer-react`

3. Add ``dataexplorer-view`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``)
    * Also, you can add `dataexplorer-view`for multiview visualization table, chart and map.
    * Add `dataexplorer-table-view` for table view.
    * Add `dataexplorer-chart-view` for table view.
    * Add `dataexplorer-map-view` for table view.

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


### Development Installation


To install ckanext-dataexplorer-react for development, activate your CKAN virtualenv and
do::

    git clone https://github.com//ckanext-dataexplorer-react.git
    cd ckanext-dataexplorer-react
    python setup.py develop
    pip install -r dev-requirements.txt


### Running the Tests

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.dataexplorer-react --cover-inclusive --cover-erase --cover-tests
