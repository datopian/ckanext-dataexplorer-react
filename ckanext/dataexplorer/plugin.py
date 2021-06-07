
from six import text_type
from logging import getLogger

from ckan.common import json, config
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.lib.helpers import url_for
log = getLogger(__name__)
ignore_empty = p.toolkit.get_validator('ignore_empty')
natural_number_validator = p.toolkit.get_validator('natural_number_validator')
Invalid = p.toolkit.Invalid
ckan_29_or_higher = p.toolkit.check_ckan_version(min_version='2.9.0')

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


def get_widget(view_dict, view_type, spec={}):
    '''
    Return a widges dict for a given view types.
    :param view_id: view id
    :type view_id: string
    :param view_type: datapackage view type.
    :type view_type: dict
    :param spec: datapackage view specs.
    :type spec: dict
    '''

    widgets = []
    
    for key, value in view_type:
        widgets.append({
            'name': value,
            'active': True,
            'datapackage': {
                'views': [{
                  'id': view_dict.get('id',''),
                  'specType': key, 
                  'spec': spec,
                  'view_type': view_dict.get('view_type',''),
                  }]
            }
        })
    return widgets


def valid_fields_as_options(schema, valid_field_types = [] ):
    '''
    Return a list of all datastore schema fields types for a given resource, as long as
    the field type is in valid_field_types.

    :param schema: schema dict
    :type schema: dict
    :param valid_field_types: field types to include in returned list
    :type valid_field_types: list of strings
    '''

    return [{'value': f['name'], 'text': f['name']} for f in schema
            if f['type'] in valid_field_types or valid_field_types == [] ] 


def in_list(list_possible_values):
    '''
    Validator that checks that the input value is one of the given
    possible values.

    :param list_possible_values: function that returns list of possible values
        for validated field
    :type possible_values: function
    '''
    def validate(key, data, errors, context):
        if not data[key] in list_possible_values():
            raise Invalid('"{0}" is not a valid parameter'.format(data[key]))
    return validate


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
            'ckan_29_or_higher' : ckan_29_or_higher
        }

    def view_template(self, context, data_dict):
        return 'dataexplorer.html'


class DataExplorerView(DataExplorerViewBase):
    '''
        This extension resources views using a v2 dataexplorer.
    '''

    def info(self):
        return {'name': 'dataexplorer_view',
                'title': 'Data Explorer',
                'icon': 'table',
                'requires_datastore': True,
                'default_title': p.toolkit._('Data Explorer'),
                }

    def setup_template_variables(self, context, data_dict):
        view_type = [('table', 'Table'), ('simple', 'Chart'),
                     ('tabularmap', 'Map')]

        widgets = get_widget(data_dict['resource_view'], view_type)

        data_dict['resource'].update({
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
        })
        
        if data_dict['resource'].get('datastore_active'):
            schema = datastore_fields_to_schema(data_dict['resource'])
            data_dict['resource'].update({
              'schema': {'fields': schema},
              'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'], _external=True),
            })

        datapackage = {'resources': [data_dict['resource']]}

        # TODO: Add view filter
        return {
            'resource_view': data_dict['resource_view'],
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
            'name': 'dataexplorer_table_view',
            'title': 'Table',
            'filterable': False,
            'icon': 'table',
            'requires_datastore': True,
            'default_title': p.toolkit._('Table'),
        }

    def setup_template_variables(self, context, data_dict):

        view_type = view_type = [('table', 'Table')]

        widgets = get_widget(data_dict['resource_view'], view_type)
        schema = datastore_fields_to_schema(data_dict['resource'])
        filters = data_dict['resource_view'].get('filters', {})

        data_dict['resource'].update({
            'schema': {'fields': schema},
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
            'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'], filters=json.dumps(filters), _external=True),
        })

        datapackage = {'resources': [data_dict['resource']]}

        return {
            'resource_view': data_dict['resource_view'],
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
    chart_types = [{'value': 'bar', 'text': 'Bar'},
                   {'value': 'line', 'text': 'Line'}]

    datastore_schema = []
    datastore_field_types = ['number', 'integer', 'datetime', 'date', 'time']

    def list_chart_types(self):
        return [t['value'] for t in self.chart_types]

    def list_schema_fields(self):
        return [t['name'] for t in self.datastore_schema]

    def info(self):
        schema = {
            'offset': [ignore_empty, natural_number_validator],
            'limit': [ignore_empty, natural_number_validator],
            'chart_type': [ignore_empty, in_list(self.list_chart_types)],
            'group': [ignore_empty, in_list(self.list_schema_fields)],
            'chart_series': [ignore_empty]
        }

        return {
            'name': 'dataexplorer_chart_view',
            'title': 'Chart',
            'filterable': False,
            'icon': 'bar-chart-o',
            'requires_datastore': True,
            'schema': schema,
            'default_title': p.toolkit._('Chart'),
        }

    def setup_template_variables(self, context, data_dict):

        view_type = view_type = [('simple', 'Chart')]

        spec = {}
        chart_type = data_dict['resource_view'].get('chart_type', False)
        group = data_dict['resource_view'].get('group', False)
        chart_series = data_dict['resource_view'].get('chart_series', False)
        if chart_type:
            spec.update({'type': chart_type})
        if group:
            spec.update({'group': group})
        if chart_series:
            spec.update({'series': chart_series if isinstance(
                chart_series, list) else [chart_series]})

        widgets = get_widget(data_dict['resource_view'], view_type, spec)

        filters = data_dict['resource_view'].get('filters', {})
        limit = data_dict['resource_view'].get('limit', 100)
        offset = data_dict['resource_view'].get('offset', 0)

        self.datastore_schema = datastore_fields_to_schema(
            data_dict['resource'])

        data_dict['resource'].update({
            'schema': {'fields': self.datastore_schema},
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
            'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'],
                           filters=json.dumps(filters), limit=limit, offset=offset, _external=True),
        })

        datapackage = {'resources': [data_dict['resource']]}
        groups = valid_fields_as_options(
            self.datastore_schema)
        chart_series = valid_fields_as_options(
            self.datastore_schema, self.datastore_field_types)

        return {
            'resource_view': data_dict['resource_view'],
            'widgets': widgets,
            'datapackage':  datapackage,
            'chart_types':  self.chart_types,
            'chart_series': chart_series,
            'groups': groups,
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

    def form_template(self, context, data_dict):
        return 'chart_form.html'


class DataExplorerMapView(DataExplorerViewBase):
    '''
        This extension provides Map views using a v2 dataexplorer.
    '''
    map_field_types = [{'value': 'lat_long',
                        'text': 'Latitude / Longitude fields'},
                       {'value': 'geometry', 'text': 'Geometry'}]

    datastore_schema = []
    datastore_field_latlon_types = ['number']

    datastore_field_geojson_types = ['string']

    def list_map_field_types(self):
        return [t['value'] for t in self.map_field_types]

    def list_schema_fields(self):
        return [t['name'] for t in self.datastore_schema]

    def info(self):
        schema = {
            'offset': [ignore_empty, natural_number_validator],
            'limit': [ignore_empty, natural_number_validator],
            'map_field_type': [ignore_empty,
                               in_list(self.list_map_field_types)],
            'latitude_field': [ignore_empty,
                               in_list(self.list_schema_fields)],
            'longitude_field': [ignore_empty,
                                in_list(self.list_schema_fields)],
            'geometry_field': [ignore_empty,
                               in_list(self.list_schema_fields)],
            'info_box': [ignore_empty]
        }

        return {
            'name': 'dataexplorer_map_view',
            'title': 'Map',
            'filterable': False,
            'icon': 'map-marker',
            'requires_datastore': True,
            'default_title': p.toolkit._('Map'),
            'schema': schema
        }

    def setup_template_variables(self, context, data_dict):

        view_type = [('tabularmap', 'Map')]
        spec = {}

        limit = data_dict['resource_view'].get('limit', 100)
        offset = data_dict['resource_view'].get('offset', 0)
        filters = data_dict['resource_view'].get('filters', {})
        map_type = data_dict['resource_view'].get('map_field_type', False)
        lon_field = data_dict['resource_view'].get('longitude_field', False)
        lat_field = data_dict['resource_view'].get('latitude_field', False)
        geom_field = data_dict['resource_view'].get('geojson_field', False)
        infobox = data_dict['resource_view'].get('info_box', False)

        if map_type == 'lat_long':
            spec.update({'lonField': lon_field, 'latField': lat_field})

        if map_type == 'geojson':
            spec.update({'geomField': geom_field})

        if infobox:
            spec.update({'infobox': infobox})

        widgets = get_widget(data_dict['resource_view'], view_type, spec)

        self.datastore_schema = datastore_fields_to_schema(
            data_dict['resource'])

        data_dict['resource'].update({
            'schema': {'fields': self.datastore_schema},
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
            'api': url_for('api.action', ver=3, logic_function='datastore_search', resource_id=data_dict['resource']['id'], filters=json.dumps(filters), limit=limit, offset=offset, _external=True),
        })

        datapackage = {'resources': [data_dict['resource']]}
        map_latlon_fields = valid_fields_as_options(
            self.datastore_schema, self.datastore_field_latlon_types)
        map_geojson_fields = valid_fields_as_options(
            self.datastore_schema, self.datastore_field_geojson_types)

        return {
            'resource_view': data_dict['resource_view'],
            'widgets': widgets,
            'datapackage':  datapackage,
            'map_field_types': self.map_field_types,
            'map_latlon_fields': map_latlon_fields,
            'map_geometry_fields': map_geojson_fields
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

    def form_template(self, context, data_dict):
        return 'map_form.html'


class DataExplorerWebView(DataExplorerViewBase):
    '''
        This extension provides external web views using a v2 dataexplorer.
    '''

    def info(self):
        return {
            'name': 'dataexplorer_web_view',
            'title': 'Web View',
            'icon': 'link',
            'schema': {'page_url': [ignore_empty, text_type]},
            'always_available': True,
            'default_title': p.toolkit._('Web'),
        }

    def setup_template_variables(self, context, data_dict):
        view_type = [('web', 'Web')]

        page_url = data_dict['resource_view'].get('page_url', False)

        widgets = get_widget(data_dict['resource_view'], view_type)

        if page_url:
            widgets[0]['datapackage']['views'][0].update(
                {'page_url': page_url})

        data_dict['resource'].update({
            'title': data_dict['resource']['name'],
            'path': data_dict['resource']['url'],
        })

        datapackage = {'resources': [data_dict['resource']]}

        return {
            'resource': data_dict['resource'],
            'widgets': widgets,
            'datapackage':  datapackage
        }

    def form_template(self, context, data_dict):
        return 'webpage_form.html'
