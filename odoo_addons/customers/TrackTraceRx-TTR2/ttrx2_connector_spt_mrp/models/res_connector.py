import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from ..connector import TrackTraceApi2
from ..connector.service import get_last_param, get_list_param
from ..tools import CleanDataDict, DictAppendNewKeys
from gevent.testing import params


# TTRX_PROD_ENDPOINT = 'https://api.tracktraceweb.com/2.0'
# TTRX_TEST_ENDPOINT = 'https://api.test.tracktraceweb.com/2.0'
_logger = logging.getLogger(__name__)



READ_STATE={'draft': [('readonly', False)]}



class CustomConnectorSpt(models.AbstractModel):
    _name = 'custom.connector.spt'
    _description = 'Connector in models TrackTrace V2'
    _OdooToTTRx = {}
    _TTRxToOdoo = {}
    _TTRxKey = False

    def _connector_default(self):
        return self.env['connector.spt'].search([('company_id','=',self.env.user.company_id.id)],limit=1)

    connector_id = fields.Many2one('connector.spt', 'Connector', default=_connector_default)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    send_to_ttr2 = fields.Boolean('Send to TTRx', default=True)

    def _GetList(self, connector, resource, **kwargs):
        #TODO: Paginação
        # self.ensure_one()
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='LIST', message='try list request in %s' % resource)
        TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
        params = TTRx.ParamsToDict(resource, **kwargs)
        queries = TTRx.QueriesToDict(**kwargs)
        put_return = TTRx.make_request('LIST', resource, params=params, queries=queries)
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='LIST', message='\n'.join(put_return['message']))
        data_list = []
        if put_return.get('sucess') != None:
            if put_return['sucess']:
                data_list = put_return['json']
                if isinstance(data_list, dict):
                    data_list = data_list.get('data',[])
            else:
                data_list.append({'error': put_return.get('message')})
        return data_list

    def _GetRecord(self, connector, resource, **kwargs):
        # self.ensure_one()
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='GET', message='try get request in %s' % resource) 
        TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
        params = TTRx.ParamsToDict(resource, **kwargs)
        get_return = TTRx.make_request('GET', resource, params=params)
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='GET', message=resource+'\n'+'\n'.join(get_return['message']))
        data = {}
        if get_return.get('sucess') != None:
            if get_return['sucess']:
                data = get_return['json']
                while isinstance(data, list):
                    data = data[0]
            else:
                data = {'error': get_return.get('message')}
        return data

    def _PostRecord(self, connector, resource, **kwargs):
        # self.ensure_one()
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='POST', message='try port request in %s' % resource)
        TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
        params = TTRx.ParamsToDict(resource, **kwargs)
        data = kwargs.get('data')
        post_return = TTRx.make_request('POST', resource, params=params, data=data)
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='POST', message='\n'.join(post_return['message']))
        res = False
        if post_return.get('sucess') != None:
            res = post_return['json']
            if post_return['sucess']:
                res = self._ConvertRespFromTTRx(post_return['json'])
            else:
                res = {'erro': post_return.get('message')}
        return res

    def _PutRecord(self, connector, resource, **kwargs):
        # self.ensure_one()
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='PUT', message='try put request in %s' % resource)
        TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
        params = TTRx.ParamsToDict(resource, **kwargs)
        put_return = TTRx.make_request('PUT', resource, params=params, data=kwargs.get('data'))
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='PUT', message='\n'.join(put_return['message']))
        res = False
        if put_return.get('sucess') != None:
            res = put_return['json']
            if put_return['sucess']:
                res = self._ConvertRespFromTTRx(put_return['json'])
            else:
                res = {'erro': put_return.get('message')}
        return res

    def _DeleteRecord(self, connector, resource, **kwargs):
        # self.ensure_one()
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='DELETE', message='try delete request in %s' % resource)
        TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
        params = TTRx.ParamsToDict(resource, **kwargs)
        delete_return = TTRx.make_request('DELETE', resource, params=params)
        self.env['tracktrace.log.spt'].addLog(connector.id, model=resource, method='DELETE', message='\n'.join(delete_return['message']))
        res = False
        if delete_return.get('sucess') != None:
            res = delete_return['json']
            if delete_return['sucess']:
                res = self._ConvertRespFromTTRx(delete_return['json'])
            else:
                res = {'erro': delete_return.get('message')}
        return res

    def _ConvertRespFromTTRx(self,values):
        res = {}
        for key, value in values.items():
            odoo_key = self._TTRxToOdoo.get(key)
            if bool(odoo_key):
                res[odoo_key] = value
        return res

    def _TTRxPrimaryKeysToList(self):
        ttrxkey = self._TTRxKey or self._order
        return ttrxkey.split(',') if bool(ttrxkey) else []
    
    def _OdooToTTRxToList(self, primary_model=None):
        if not bool(primary_model):
            res = list(self._OdooToTTRx.keys())
        else:
            #TODO: erro do submodal
            res = list(self._OdooToTTRx[primary_model].keys())
        return res
    
    def _GetValueKey(self, key):
        res = getattr(self, key, None)
        return res

    def _GetParamURItoTTRx(self, resource):
        UrlKeys = get_list_param(resource)
        res = {}
        for UrlKey in UrlKeys:
            res[UrlKey] = None
        return res

    def _GetParamsTTRxToURI(self, resource, values):
        res = self._GetParamURItoTTRx(resource)
        for key in list(res.keys()):
            res[key] = values.get(key)
        CleanDataDict(res)
        return res

    def _ParamTTRxToOdoo(self, param):
        res = None
        itemsList = self._OdooToTTRx.items()
        for item in itemsList:
            if item[1] == param:
                res = item[0]
                break
        return res
    
    def _getUriParamsInSelf(self, resource): 
        res = {}
        params = self._GetParamURItoTTRx(resource)
        for ttr_uri in params:
            odoo_uri = self._ParamTTRxToOdoo(ttr_uri)
            res[ttr_uri] = self._GetValueKey(odoo_uri) if bool(self) else None
        return res
 
    def _GetUriParams(self, resource, primary_model=None, values=None):
        res = {}
        listPrimaryKeys = self._OdooToTTRxToList(primary_model)
        listParamsKeys = get_list_param(resource)
        for odookey in listPrimaryKeys:
            ttrkey = self._OdooToTTRx[primary_model][odookey] if bool(primary_model) else self._OdooToTTRx[odookey]
            if ttrkey in listParamsKeys:
                res[ttrkey] = None
                if bool(values):
                    res[ttrkey] = values.get(odookey)
                if res[ttrkey] == None and bool(self):
                    res[ttrkey] = self._GetValueKey(key=odookey) 
        return res

    def _GetTTRxDomainToSearch(self, data):
        params = self._TTRxPrimaryKeysToList()
        res = []
        for param in params:
            value = data[param]
            item = (param,'=',value)
            res.append(item)
        return res
    
    def _TTRxKeyValue(self, resource):
        return get_list_param(resource)

    def FromOdooToTTRx(self, values={}):
        # self.ensure_one()
        var = {}
        return var
    
    def FromTTRxToOdoo(self, values):
        # self.ensure_one()
        var = {}
        return var

    def BeforeCreateFromTTRx(self, connector, response, data):
        pass

    def AfterCreateFromTTRx(self, connector, response, data):
        pass

    def DeleteDependencies(self, connector, **params):
        pass

    def BeforeCreateInOdoo(self, **params):
        return True

    def AfterCreateInOdoo(self, **params):
        pass

    def BeforeWriteInOdoo(self, **params):
        return True

    def AfterWriteInOdoo(self, **params):
        pass

    def BeforeUnlinkInOdoo(self, **params):
        return True

    def AfterUnlinkInOdoo(self, **params):
        pass

    def TTRxSearch(self, connector, **params):
        # self.ensure_one()
        primary_model = params.get('primary_model')
        resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
        uri_params = self._GetParamURItoTTRx(resource)
        exist = self.env[self._name]
        if len(uri_params) > 0:
            values = self._ConvertRespFromTTRx(values=params) 
            domain = self._GetTTRxDomainToSearch(values)
            exist = self.search(domain, limit=1)
        return exist
        

    def SyncFromTTRx(self, connector, **params):
        res = self.env[self._name]
        primary_model = params.get('primary_model') if bool(params.get('primary_model')) else self.primary_model \
                        if hasattr(self, 'primary_model') else None
        resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
        if bool(params.get('myown')):
            if bool(primary_model):
                params['primary_model'] = primary_model
            params.update(self._GetUriParams(resource,primary_model=primary_model))
            res += self._CreateUpdateFromTTRx(connector, **params)
        else:
            last_param = get_last_param(resource)
            if bool(last_param) and last_param in params:
                register = self.TTRxSearch(connector,**params)
                if not bool(register) or bool(params.get('forceUpdate',False)):
                    res += register._CreateUpdateFromTTRx(connector, **params)
                else:
                    res += register
            else:
                data_list = self._GetList(connector, resource, **params) or []
                for data in data_list:
                    for key in params.keys():
                        if not bool(params.get(key,False)):
                            params[key] = data.get(key,params[key])
                    params.update(data)
                    params.update(self._GetParamsTTRxToURI(resource, params))
                    CleanDataDict(params)
                    res += self._CreateUpdateFromTTRx(connector, **params)
        return res
    
    def _CreateUpdateFromTTRx(self, connector, **params):
        """
            submodal
            primarykey
        """
        response, data = self.GetValuesInTTRx(connector, **params)
        exist = self.env[self._name]
        if bool(response) and not bool(response.get('error')):
            exist.BeforeCreateFromTTRx(connector, response, data)
            domain = self._GetTTRxDomainToSearch(data)
            exist = self.search(domain, limit=1)
            if bool(exist):
                if params.get('update') in [True,None]:
                    context = dict(self.env.context or {})
                    context['no_rewrite'] = True
                    exist.with_context(context).write(data)
            else:
                exist = self.create(data)
            exist.AfterCreateFromTTRx(connector,response,data)
            # exist._cr.commit()
        return exist

    def GetValuesInTTRx(self, connector, **params):
        primary_model = params.get('primary_model')
        resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
        uri_params = self._GetParamURItoTTRx(resource)
        if len(uri_params) > 0:
            if len(self.ids) == 1:
                get_params = self._getUriParamsInSelf(resource)
            else:
                get_params = params
            response = self._GetRecord(connector, resource, **get_params)
        else:
            response = params
        data = {}
        if bool(response):
            if not bool(response.get('error')):
                DictAppendNewKeys(params,response)
                data.update(self.FromTTRxToOdoo(response))
                data['connector_id'] = connector.id
        return response, data

    @api.model
    def create(self, values):
        created = super(CustomConnectorSpt, self).create(values)
        for reg in created:
            if reg.send_to_ttr2:
                reg.CreateInTTRx(values=values)
        return created

    def CreateInTTRx(self, **params):
        # self.ensure_one()
        primary_model = self.primary_model if hasattr(self, 'primary_model') else None
        params = {}
        listPKey = self._OdooToTTRxToList(primary_model)
        create_response = False
        if bool(listPKey) and not bool(self._GetValueKey(listPKey[-1])):
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            params['data'] = self.FromOdooToTTRx()
            params.update(self._GetUriParams(resource,primary_model=primary_model))
            if bool(self.BeforeCreateInOdoo(**params)):
                create_response = self._PostRecord(self.connector_id, resource, **params) 
                if bool(create_response) and not bool(create_response.get('erro')):
                    context = dict(self.env.context or {})
                    context['no_rewrite'] = True
                    self.with_context(context).write(create_response)
                self.AfterCreateInOdoo(**params)
        return create_response

    def write(self, vals):
        toWrite = self.env[self._name]
        if not self.env.context.get('no_rewrite', False):
            for reg in self:
                if reg.send_to_ttr2:
                    response = reg.WriteInTTRx(**vals)
                    if not bool(response) or not bool(response.get('erro')):
                        toWrite = toWrite + reg
                else:
                    toWrite = toWrite + self
        else:
            toWrite = toWrite + self
        return super(CustomConnectorSpt, toWrite).write(vals)
        
    def WriteInTTRx(self, **params):
        # self.ensure_one()
        primary_model = self.primary_model if hasattr(self, 'primary_model') else None
        listPKey = self._OdooToTTRxToList(primary_model)
        params['data'] = self.FromOdooToTTRx()
        write_response = None
        if len(params['data']) > 0 and bool(listPKey) and bool(self._GetValueKey(listPKey[-1])):
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            params ={'data': self.FromOdooToTTRx(params)}
            params.update(self._GetUriParams(resource,primary_model=primary_model))            
            if bool(self.BeforeWriteInOdoo(**params)):
                write_response = self._PutRecord(self.connector_id, resource, **params)
                params['response'] = write_response 
                self.AfterWriteInOdoo(**params)
            else:
                write_response = False
        return write_response

    def unlink(self):
        toUnlink = self.env[self._name]
        for record in self:
            response = record.DeleteInTTRx()
            if not bool(response) or not bool(response.get('erro')):
                toUnlink = toUnlink + record
        return super(CustomConnectorSpt, toUnlink).unlink()

    def DeleteInTTRx(self, **params):
        # self.ensure_one()
        primary_model = self.primary_model if hasattr(self, 'primary_model') else None
        listPKey = self._OdooToTTRxToList(primary_model)
        if bool(listPKey) and bool(self._GetValueKey(listPKey[-1])) and self.connector_id.auto_delete:
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            params ={'data': self.FromOdooToTTRx(params)}
            params.update(self._GetUriParams(resource,primary_model=primary_model))            
            if bool(self.BeforeUnlinkInOdoo(**params)):
                delete_response = self._PutRecord(self.connector_id, resource, **params) 
                params['response'] = delete_response 
                self.AfterUnlinkInOdoo(**params)
                return delete_response
        return False
        
        
class ConnectorSpt(models.Model):
    _name = 'connector.spt'
    _description = 'Connector TrackTrace V2'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'name'
    

    name = fields.Char('Name', required=1, copy=False, readonly=True, states=READ_STATE)
    
    company_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.user.company_id, copy=False, 
                                 readonly=True, states=READ_STATE)

    api_environment = fields.Selection([('test', 'Testing'), ('production', 'Production')], string='Environment', default='test', 
                                       related="company_id.api_environment", store=True, copy=False, readonly=True, states=READ_STATE)
    
    api_key = fields.Char('API Key', related="company_id.api_key", store=True, copy=False, readonly=True, states=READ_STATE)
    portal_url = fields.Char('Portal Url', readonly=True, states=READ_STATE)

    api_url = fields.Char('TTrx2 API Url',  compute="_compute_api_url", store=False)
    
    auto_delete = fields.Boolean('Auto Delete', default=False, required=True)

    
    auto_vacuum = fields.Boolean('Auto Vacuumm', default=True, required=True)

    state = fields.Selection(selection=[('draft', 'Not Confirmed'),('done', 'Confirmed')], string='Status', required=True, 
                             readonly=True, copy=False, tracking=True, default='draft')
    auto_create_new_partner = fields.Boolean("Auto Create New Trading Partner?", default=False)
    
    last_update_date = fields.Date('Last Update in', default='2020-01-01')
    
    log_ids = fields.One2many('tracktrace.log.spt','connector_id', string="Logs", readonly=True)
    
    active = fields.Boolean("Active", default=True)
    

    # Compute the api url
    @api.depends("api_environment")
    def _compute_api_url(self):
        configParameter = self.env["ir.config_parameter"]
        for connector in self:
            if connector.api_environment == 'production':
                connector.api_url = configParameter.sudo().get_param("default_tracktracerx_endpoint_prod",
                                                                        "https://api.tracktraceweb.com/2.0")
                # company.ttrx_api_url = TTRX_PROD_ENDPOINT
            else:
                connector.api_url = configParameter.sudo().get_param("default_tracktracerx_endpoint_test",
                                                                        "https://api.test.tracktraceweb.com/2.0")
                # company.ttrx_api_url = TTRX_TEST_ENDPOINT

    @api.onchange("api_environment", "api_key", "name")
    def onchange_api_environment_key(self):
        self.state = "draft"
        

    def action_confirm(self):
        for reg in self:
            resp = reg.test_connection()

    def action_test(self):
        for reg in self:
            queries = {'status': 'AVAILABLE'}
            resp = reg.GetList('products', queries=queries)
            if bool(resp):
                title = "Connected!"
                message = "The connection with TTr2 is OK!"
                    
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': title,
                        'message': message,
                        'sticky': False,
                    }
                }
                     
            else:               
                raise UserError('Error in connection with TTr2')

    def action_invalidate(self):
        for reg in self:
            reg.state = 'draft'

    @api.model
    def GetRecord(self, resource, **params):
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='GET', message='try get request in %s' % resource)
        req = TrackTraceApi2(self.api_url, self.api_key).GetRecord(resource, **params)
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='GET', message='\n'.join(req['message']))
        if req['sucess']:
            return req['json']
        else:
            return False

    @api.model
    def GetList(self, resource, **params):
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='LIST', message='try list request in %s' % resource)
        req = TrackTraceApi2(self.api_url, self.api_key).GetList(resource, **params)
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='GET', message='\n'.join(req['message']))
        if req['sucess']:
            return req['json']
        else:
            return False

    @api.model
    def PostRecord(self, resource, **params):
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='POST', message='try port request in %s' % resource)
        req = TrackTraceApi2(self.api_url, self.api_key).PostRequest(resource, **params)
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='GET', message='\n'.join(req['message']))
        if req['sucess']:
            return req['json']
        else:
            return False

    @api.model
    def PutRecord(self, resource, **params):
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='PUT', message='try put request in %s' % resource)
        req = TrackTraceApi2(self.api_url, self.api_key).PutRecord(resource, **params)
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='GET', message='\n'.join(req['message']))
        if req['sucess']:
            return req['json']
        else:
            return False

    @api.model
    def DeleteRecord(self, resource, **params):
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='DELETE', message='try delete request in %s' % resource)
        req = TrackTraceApi2(self.api_url, self.api_key).GetRequest(resource, **params)
        self.env['tracktrace.log.spt'].addLog(self.id, model=resource, method='GET', message='\n'.join(req['message']))
        if req['sucess']:
            return req['json']
        else:
            return False

    def action_impexp_partner(self):
        """ Function to import and export as select
        
        ..todo:: Find more information about it
        
        :return: None
        
        """
        # self.ensure_one()
        
        try:
            form_view = self.env.ref('tracktrace_odoo_connector_spt.sync_partner')
        
        except ValueError:
            form_view = False
        
        return {
            'name': 'Sync Partner',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.partner.spt.wizard',
            'view_id': form_view,
            'views': [(form_view, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_connector_id': self.id}
        }
    
    def action_impexp_product(self):    
        """ Function to import and export as select
        
        ..todo:: Find more information about it
        
        :return: None
        
        """
        # self.ensure_one()
        
        try:
            form_view = self.env.ref('tracktrace_odoo_connector_spt.sync_product')
        
        except ValueError:
            form_view = False
        
        return {
            'name': 'Sync Product',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.product.spt.wizard',
            'view_id': form_view,
            'views': [(form_view, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_connector_id': self.id}
        }

    def action_impexp_manufacturer(self):    
        """ Function to import and export as select
        
        ..todo:: Find more information about it
        
        :return: None
        
        """
        # self.ensure_one()
        
        try:
            form_view = self.env.ref('tracktrace_odoo_connector_spt.sync_manufacturer')
        
        except ValueError:
            form_view = False
        
        return {
            'name': 'Sync Manufacturer',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.manufacturer.spt.wizard',
            'view_id': form_view,
            'views': [(form_view, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_connector_id': self.id}
        }
    
    def action_impexp_locations(self):    
        """ Function to import and export as select
        
        ..todo:: Find more information about it
        
        :return: None
        
        """
        # self.ensure_one()
        
        try:
            form_view = self.env.ref('tracktrace_odoo_connector_spt.sync_locations')
        
        except ValueError:
            form_view = False
        
        return {
            'name': 'Sync Locations',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.locations.spt.wizard',
            'view_id': form_view,
            'views': [(form_view, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_connector_id': self.id}
        }

    def action_impexp_containers(self):    
        """ Function to import and export as select
        
        ..todo:: Find more information about it
        
        :return: None
        
        """
        # self.ensure_one()
        
        try:
            form_view = self.env.ref('tracktrace_odoo_connector_spt.sync_containers')
        
        except ValueError:
            form_view = False
        
        return {
            'name': 'Sync Containers',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.container.spt.wizard',
            'view_id': form_view,
            'views': [(form_view, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_connector_id': self.id}
        }
    
    #TODO: Fazer o download das loactions  

