
from logging import getLogger

from ckan.common import json, config
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.lib.helpers import url_for
log = getLogger(__name__)
ignore_empty = p.toolkit.get_validator('ignore_empty')
natural_number_validator = p.toolkit.get_validator('natural_number_validator')
Invalid = p.toolkit.Invalid


def each_datastore_field_to_schema_type(dstore_type):
    # Adopted from https://github.com/frictionlessdata/datapackage-pipelines-ckan-driver/blob/master/tableschema_ckan_datastore/mapper.py
    '''
    For a given datastore type, return the corresponding schema type.
    datastore int and float may have a trailing digit, which is stripped.
    datastore arrays begin with an '_'.
    '''
    dstore_type = dstore_type.rstrip('0123456789')
    if dstore_type.startswith('_'):
        dstore_type = 'array'
    DATASTORE_TYPE_MAPPING = {
        'int': ('integer', None),
        'float': ('number', None),
        'smallint': ('integer', None),
        'bigint': ('integer', None),
        'integer': ('integer', None),
        'numeric': ('number', None),
        'money': ('number', None),
        'timestamp': ('datetime', 'any'),
        'date': ('date', 'any'),
        'time': ('time', 'any'),
        'interval': ('duration', None),
        'text': ('string', None),
        'varchar': ('string', None),
        'char': ('string', None),
        'uuid': ('string', 'uuid'),
        'boolean': ('boolean', None),
        'bool': ('boolean', None),
        'json': ('object', None),
        'jsonb': ('object', None),
        'array': ('array', None)
    }
    try:
        return DATASTORE_TYPE_MAPPING[dstore_type]
    except KeyError:
        log.warn('Unsupported DataStore type \'{}\'. Using \'string\'.'
                 .format(dstore_type))
        return ('string', None)


def datastore_fields_to_schema(resource):
    '''
    Return a table schema from a DataStore field types.
    :param resource: resource dict
    :type resource: dict
    '''
    data = {'resource_id': resource['id'], 'limit': 0}

    fields = toolkit.get_action('datastore_search')({}, data)['fields']
    ts_fields = []
    for f in fields:
        if f['id'] == '_id':
            continue
        datastore_type = f['type']
        datastore_id = f['id']
        ts_type, ts_format = each_datastore_field_to_schema_type(
            datastore_type)
        ts_field = {
            'name': datastore_id,
            'type': ts_type
        }
        if ts_format is not None:
            ts_field['format'] = ts_format
        ts_fields.append(ts_field)
    return ts_fields


def get_widget(view_id,  view_type):
  widgets = []
  ordering = dict((k, v) for v, k in enumerate(
      ['table', 'simple', 'tabularmap']))

  view_type = sorted(view_type.items(), key=lambda (k, v): ordering[k])
  for key, value in view_type:
      widgets.append({
          'name': value,
          'active': True,
          'datapackage': {
              'views': [{'id': view_id, 'specType': key}]
          }
      })
  return widgets


class DataExplorerViewBase(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IResourceView, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'dataexplorer')

    def can_view(self, data_dict):
        resource = data_dict['resource']
        return (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', ''))

    def get_helpers(self):
        return {

        }

    def view_template(self, context, data_dict):
        return 'dataexplorer.html'

class DataExplorerView(DataExplorerViewBase):
    '''
        This extension resources views using a v2 dataexplorer.
    '''

    def info(self):
        return {'name': 'dataexlorer',
                'title': 'Data Explorer',
                'filterable': True,
                'icon': 'table',
                'requires_datastore': False,
                'default_title': p.toolkit._('Data Explorer'),
                }

    def setup_template_variables(self, context, data_dict):
        view_type = {
            'table': 'Table',
            'simple': 'Chart',
            'tabularmap': 'Map'
        }
        log.warn(data_dict['resource_view'])
        widgets = get_widget(data_dict['resource_view'].get('id', ''),  view_type)
        schema = datastore_fields_to_schema(data_dict['resource'])

        data_dict['resource'].update({
            'schema': {'fields': schema},
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
            'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'],  _external=True),
        })

        datapackage = {'resources': [data_dict['resource']]}

        # TODO: Add view filter
        return {
            'resource': data_dict['resource'],
            'widgets': widgets,
            'datapackage':  datapackage
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']

        if (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', '')):
            return True
        resource_format = resource.get('format', None)
        if resource_format:
            return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
        else:
            return False

class DataExplorerTableView(DataExplorerViewBase):
    '''
        This extension provides table views using a v2 dataexplorer.
    '''

    def info(self):
        return {
            'name': 'dataexlorer_table',
                'title': 'Table',
                'filterable': False,
                'icon': 'table',
                'requires_datastore': False,
                'default_title': p.toolkit._('Table'),
                }

    def setup_template_variables(self, context, data_dict):

        view_type = {
            'table': 'Table',
        }

        widgets = get_widget(data_dict['resource_view'].get('id', ''),  view_type)
        schema = datastore_fields_to_schema(data_dict['resource'])

        data_dict['resource'].update({
            'schema': {'fields': schema},
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
            'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'],  _external=True),
        })

        datapackage = {'resources': [data_dict['resource']]}

        # TODO: Add view filter
        return {
            'resource': data_dict['resource'],
            'widgets': widgets,
            'datapackage':  datapackage
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']

        if (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', '')):
            return True
        resource_format = resource.get('format', None)
        if resource_format:
            return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
        else:
            return False

class DataExplorerChartView(DataExplorerViewBase):
    '''
    This extension provides chart views using a v2 dataexplorer.
    '''

    def info(self):
        return {
            'name': 'dataexlorer_chart',
            'title': 'Chart',
            'filterable': False,
            'icon': 'bar-chart-o',
            'requires_datastore': False,
            'default_title': p.toolkit._('Chart'),
        }

    def setup_template_variables(self, context, data_dict):

        view_type = {
            'simple': 'Chart',
        }

        widgets = get_widget(data_dict['resource_view'].get('id', ''),  view_type)
        schema = datastore_fields_to_schema(data_dict['resource'])

        data_dict['resource'].update({
            'schema': {'fields': schema},
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
            'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'],  _external=True),
        })

        datapackage = {'resources': [data_dict['resource']]}

        # TODO: Add view filter
        return {
            'resource': data_dict['resource'],
            'widgets': widgets,
            'datapackage':  datapackage
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']

        if (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', '')):
            return True
        resource_format = resource.get('format', None)
        if resource_format:
            return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
        else:
            return False

class DataExplorerMapView(DataExplorerViewBase):
    '''
        This extension provides Map views using a v2 dataexplorer.
    '''

    def info(self):
        return {
            'name': 'dataexlorer_map',
            'title': 'Map',
            'filterable': False,
            'icon': 'map-marker',
            'requires_datastore': False,
            'default_title': p.toolkit._('Map'),
        }

    def setup_template_variables(self, context, data_dict):

        view_type = {
            'tabularmap': 'Map'
        }

        widgets = get_widget(data_dict['resource_view'].get('id', ''),  view_type)
        schema = datastore_fields_to_schema(data_dict['resource'])

        data_dict['resource'].update({
            'schema': {'fields': schema},
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
            'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'],  _external=True),
        })

        datapackage = {'resources': [data_dict['resource']]}

        # TODO: Add view filter
        return {
            'resource': data_dict['resource'],
            'widgets': widgets,
            'datapackage':  datapackage
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']

        if (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', '')):
            return True
        resource_format = resource.get('format', None)
        if resource_format:
            return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
        else:
            return False


