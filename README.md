[![CKAN](https://img.shields.io/badge/ckan-2.10-orange.svg?style=flat-square)](https://github.com/ckan/ckan/tree/2.8) [![CKAN](https://img.shields.io/badge/ckan-2.9-orange.svg?style=flat-square)](https://github.com/ckan/ckan/tree/2.9)

Note that it should work on earlier CKAN versions but it hasn't been tested.

### Features

A Data Explorer app for CKAN built in React:

* Preview data from DataStore in a table.
  * Set predefined filters.
  * Set suggested filters.
* Filter data using SQL-like query builder which calls `datastore_search_sql` API.
* Build charts and maps similar to classic Data Explorer but with improved UI/UX.

![ezgif-3-2c8e3c18ac8e](https://user-images.githubusercontent.com/17809581/121645171-b33ddf80-cab5-11eb-8680-b98ddea353b3.gif)

### Installation

**:warning: For CKAN v2.8, please use branch `2.8`.**

**Important notice:** if you're using CKAN >v2.8.6 or >v2.9.1 you need to make sure that `over` function of Postgresql is enabled via `datastore_search_sql` endpoint. To do so you may need to add it into your allow list here - https://github.com/ckan/ckan/blob/master/ckanext/datastore/allowed_functions.txt

The React code repository is here - https://github.com/datopian/data-explorer.

To install ckanext-dataexplorer-react:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-dataexplorer-react Python package into your virtual environment::
   `pip install -e git+https://github.com/datopian/ckanext-dataexplorer-react.git#egg=ckanext-dataexplorer-react`

3. Add ``dataexplorer_view`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``)
    * `dataexplorer_view`for multiview visualization table, chart and map.
    * Add `dataexplorer_table_view` for table view.
    * Add `dataexplorer_chart_view` for chart view.
    * Add `dataexplorer_map_view` for map view.
    * Add `dataexplorer_web_view` for external web view.

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


### Development Installation


To install ckanext-dataexplorer-react for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/datopian/ckanext-dataexplorer-react.git
    cd ckanext-dataexplorer-react
    python setup.py develop
    pip install -r dev-requirements.txt

