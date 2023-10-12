import logging
import time
import json

from datetime import timedelta

from odoo import models, fields, api, _
from ..connector import TrackTraceApi2
from ..connector.service import get_last_param, get_list_param
from ..tools import CleanDataDict, DictAppendNewKeys
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDTF

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

    def ConnectorValidate(self):
        res = []
        if not bool(self.connector_id):
            res += ['The connector was not indicated']
        else:
            if not bool(self.wharehouse_id):
                res += ['The warehouse was not indicated']
        if not bool(self.company_id):
            res += ['The company was not indicated']

    connector_id = fields.Many2one('connector.spt', 'Connector', default=_connector_default)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    # send_to_ttr2 = fields.Boolean('Auto Send from/to TTRx', default=True)
    auto_create_in_ttr2 = fields.Boolean('Auto Send to create to TTRx', default=True)
    can_send_to_ttr2 = fields.Boolean('Can Send to TTRx', compute="compute_can_send_to_ttr2", store=False, readonly=True)
    has_connector = fields.Boolean('has connector', compute="compute_has_connector", store=False, readonly=True)
    
    def _can_send_to_ttr2(self):
        res = True if bool(self.connector_id) and self.connector_id.state == 'done' else False
        return res

    def compute_can_send_to_ttr2(self):
        for reg in self:
            reg.can_send_to_ttr2 = reg._can_send_to_ttr2()

    def compute_has_connector(self):
        for reg in self:
            reg.has_connector = True if bool(self.connector_id) and self.connector_id.state == 'done' else False
        
    def _get_parameter_raise_exception(self):
        params = self.env['ir.config_parameter'].sudo()
        return bool(params.get_param('ttrx2_connector_spt.raise_exception_on_cron', default=False))

    def _get_context_cron(self, context={}):
        raise_exception_on_cron=self._get_parameter_raise_exception()
        if not bool(context):
            context = dict(self.env.context or {})
        context['NotRaiseError'] = raise_exception_on_cron
        return context

    def _GetList(self, connector, resource, **kwargs):
        #TODO: Paginação
        # self.ensure_one()
        data_list = []
        try:
            connector.logger_info('LIST-IN', 'Try list request in %s:\n%s' % (resource,json.dumps(kwargs)), model=self._name, res_id=self.id)
            start_time = time.perf_counter()
            TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
            queries = kwargs.get("queries",{})
            params = TTRx.ParamsToDict(resource, **kwargs)
            queries.update(TTRx.QueriesToDict(**kwargs))
            if not bool(queries.get('nb_per_page')):
                queries['nb_per_page'] = connector.itens_per_page if connector.itens_per_page >= 10 and connector.itens_per_page <= 1000 else 100
                
            get_return = TTRx.make_request('LIST', resource, params=params, queries=queries)
            # ('\n'.join(get_return['message'])
            if get_return.get('sucess') != None:
                if get_return['sucess']:
                    data_list = get_return['json']
                    if isinstance(data_list, list):
                        msg = 'The %s get list return with %s itens.' % (resource,len(data_list))
                    else:
                        msg = 'The %s get list return with %s itens.' % (resource,data_list.get('nb_total_results', '[unknown]'))
                    if isinstance(data_list, dict):
                        data_list = data_list.get('data',[])
                else:
                    msg = 'The %s get list return error %s.' % (resource,get_return.get('message'))
                    data_list.append({'error': msg})
            end_time = time.perf_counter()
            exectime = f"\nExecution Time : {end_time - start_time:0.6f}"
            connector.logger_info('LIST-OUT', message=msg+exectime, model=self._name, res_id=self.id)
            self._cr.commit()
        except Exception as e:
            connector.logger_error('LIST-OUT', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return data_list

    def _GetRecord(self, connector, resource, **kwargs):
        # self.ensure_one()
        data = {}
        try:
            connector.logger_info('GET-IN', message='Try get request in %s:\n%s' % (resource,json.dumps(kwargs)), model=self._name, res_id=self.id)
            start_time = time.perf_counter()
            TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
            params = TTRx.ParamsToDict(resource, **kwargs)
            get_return = TTRx.make_request('GET', resource, params=params)
            if get_return.get('sucess') != None:
                if get_return['sucess']:
                    data = get_return['json']
                    msg = 'The %s returned the following dataset.\n%s' % (resource,str(data))
                    while isinstance(data, list):
                        data = data[0]
                else:
                    msg = 'The %s get record return error %s.' % (resource,get_return.get('message'))
                    data = {'error': get_return.get('message')}
            end_time = time.perf_counter()
            exectime = f"\nExecution Time : {end_time - start_time:0.6f}"
            connector.logger_info('GET-OUT', message=msg+exectime, model=self._name, res_id=self.id)
            self._cr.commit()
        except Exception as e:
            connector.logger_error('GET-OUT', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return data

    def _PostRecord(self, connector, resource, **kwargs):
        res = False
        try:
            connector.logger_info('POST-IN', message='try port request in %s\n%s' % (resource,json.dumps(kwargs.get('data', ""))), model=self._name, res_id=self.id)
            start_time = time.perf_counter()
            TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
            params = TTRx.ParamsToDict(resource, **kwargs)
            data = kwargs.get('data')
            post_return = TTRx.make_request('POST', resource, params=params, data=data)
            if post_return.get('sucess') != None:
                res = post_return['json']
                if post_return['sucess']:
                    msg = 'Succes! The post retorned %s ' % str(res)
                    res = self._ConvertRespFromTTRx(post_return['json'])
                else:
                    msg = 'Fault! The post retorned this error %s' % post_return.get('message')
                    res = {'erro': post_return.get('message')}
                    raise UserError(_(f"Error creating on portal {res}"))
            end_time = time.perf_counter()
            exectime = f"\nExecution Time : {end_time - start_time:0.6f}"
            connector.logger_info('POST-OUT', message=msg+exectime, model=self._name, res_id=self.id)

            # TODO  checar por que está gerando partner ao retornar erro de post no portal
            self._cr.commit()
        except Exception as e:
            connector.logger_error('POST-OUT', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return res

    def _PutRecord(self, connector, resource, **kwargs):
        # self.ensure_one()
        res = False
        try:
            connector.logger_info('PUT-IN', message='try put request in %s\n%s' % (resource,str(json.dumps(kwargs))), model=self._name, res_id=self.id)
            start_time = time.perf_counter()
            TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
            params = TTRx.ParamsToDict(resource, **kwargs)
            put_return = TTRx.make_request('PUT', resource, params=params, data=kwargs.get('data'))
            if put_return.get('sucess') != None:
                res = put_return['json']
                if put_return['sucess']:
                    res = self._ConvertRespFromTTRx(put_return['json'])
                    msg = 'Succes! The PUT retorned %s ' % str(res)
                else:
                    res = {'erro': put_return.get('message')}
                    msg = 'Fault! The post retorned this error %s' % put_return.get('message')
            end_time = time.perf_counter()
            exectime = f"\nExecution Time : {end_time - start_time:0.6f}"
            connector.logger_info('PUT-OUT', message=msg+exectime, model=self._name, res_id=self.id)
            self._cr.commit()
        except Exception as e:
            connector.logger_error('PUT-OUT', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return res

    def _DeleteRecord(self, connector, resource, **kwargs):
        # self.ensure_one()
        res = False
        try:
            connector.logger_info('DELETE-IN', message='try delete request in %s:\n%s' % (resource,json.dumps(kwargs)), model=self._name, res_id=self.id)
            start_time = time.perf_counter()
            TTRx = TrackTraceApi2(connector.api_url, connector.api_key)
            params = TTRx.ParamsToDict(resource, **kwargs)
            delete_return = TTRx.make_request('DELETE', resource, params=params)
            if delete_return.get('sucess') != None:
                res = delete_return['json']
                if delete_return['sucess']:
                    res = self._ConvertRespFromTTRx(delete_return['json'])
                    msg = 'Succes! The PUT retorned %s ' % str(res)
                else:
                    res = {'erro': delete_return.get('message')}
                    msg = 'Fault! The post retorned this error %s' % post_return.get('message')
            end_time = time.perf_counter()
            exectime = f"\nExecution Time : {end_time - start_time:0.6f}"
            connector.logger_info('DELETE-OUT', message=msg+exectime, model=self._name, res_id=self.id)
            self._cr.commit()
        except Exception as e:
            connector.logger_error('DELETE-OUT', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return res

    def _ConvertRespFromTTRx(self,values):
        res = {}
        try:
            for key, value in values.items():
                odoo_key = self._TTRxToOdoo.get(key)
                if bool(odoo_key):
                    res[odoo_key] = value
                if bool(values.get('queue_url',False)):
                    res['queue_url'] = values['queue_url']
                if bool(values.get('queue_uuid',False)):
                    res['queue_uuid'] = values['queue_uuid']
        except Exception as e:
            connector.logger_error('CONV-RESP-TTRX', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return res

    def _TTRxPrimaryKeysToList(self):
        ttrxkey = self._TTRxKey or self._order or ''
        return ttrxkey.split(',') if bool(ttrxkey) else []
    
    def _OdooToTTRxToList(self, primary_model=None):
        try:
            if not bool(primary_model):
                res = list(self._OdooToTTRx.keys())
            else:
                #TODO: erro do submodal
                res = list(self._OdooToTTRx[primary_model].keys())
        except Exception as e:
            connector.logger_error('CONV-ODOO-TTRX-LIST', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
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

    def _ParamTTRxToOdoo(self, param, primary_model=None):
        res = param
        itemsList = []
        if bool(primary_model):
            ipm = self._OdooToTTRx.get(primary_model)
            if bool(ipm):
                itemsList = ipm.items()
        else:
            itemsList = self._OdooToTTRx.items()
        for item in itemsList:
            if item[1] == param:
                res = item[0]
                break
        return res
    
    def _getUriParamsInSelf(self, resource, primary_model=None): 
        res = {}
        params = self._GetParamURItoTTRx(resource)
        for ttr_uri in params:
            odoo_uri = self._ParamTTRxToOdoo(ttr_uri, primary_model)
            res[ttr_uri] = self._GetValueKey(odoo_uri) if bool(self) else None
        return res
 
    def _GetUriParams(self, resource, primary_model=None, values=None):
        res = {}
        try:
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
        except Exception as e:
            connector.logger_error('GET-URI-PARAM', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return res

    def _GetTTRxDomainToSearch(self, data):
        res = []
        try:
            params = self._TTRxPrimaryKeysToList()
            for param in params:
                value = data[param]
                item = (param,'=',value)
                res.append(item)
        except Exception as e:
            connector.logger_error('GET-DOMAIN-SEARCH', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return res
    
    def _TTRxKeyValue(self, resource):
        return get_list_param(resource)

    def FromOdooToTTRx(self, connector, values={}):
        connector.logger_info('FROM/TO', message='try convert Odoo structure to TTRx data (%s)' % str(values), model=self._name, res_id=self.id)
        var = {}
        return var
    
    def FromTTRxToOdoo(self, connector, values):
        connector.logger_info('TO/FROM', message='try convert TTRx data to Odoo structure (%s)' % str(values), model=self._name, res_id=self.id)
        var = {}
        return var

    def BeforeCreateFromTTRx(self, connector, response, data):
        return True

    def AfterCreateFromTTRx(self, connector, response, data):
        pass

    def DeleteDependencies(self, connector, **params):
        pass

    def BeforeCreateInTTRx(self, **params):
        return True

    def AfterCreateInTTRx(self, **params):
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
        connector.logger_info('TRYSEARCH', message='try search registry in Odoo:\n%s' % str(params), model=self._name, res_id=self.id)
        exist = self.env[self._name]
        try:
            primary_model = params.get('primary_model')
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            uri_params = self._GetParamURItoTTRx(resource)
            if len(uri_params) > 0:
                values = self._ConvertRespFromTTRx(values=params) 
                domain = self._GetTTRxDomainToSearch(values)
                exist = self.search(domain, limit=1)
        except Exception as e:
            connector.logger_error('TRYSEARCH', message=str(e), model=self._name, res_id=self.id)                
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        return exist

    def SyncFromTTRx(self, connector, **params):
        context = dict(self.env.context or {}) 
        connector.logger_info('TRYSYNCFROMTTRX', message='try sync data from TTRx list in Odoo %s' % str(params), model=self._name, res_id=self.id)
        res = self.env[self._name]
        context['NewOnly'] = bool(params.get('NewOnly',False))
        context['MySelf'] = bool(params.get('MySelf',False))
        context['NoUpdate'] = bool(params.get('NoUpdate',False))
        context['NoCreate'] = bool(params.get('NoCreate',False))
        context['ForceUpdate'] = bool(params.get('ForceUpdate',False))
        context['RaiseError'] = bool(params.get('RaiseError',False))
        if not bool(connector.wharehouse_id):
            erro = """
    The wharehouse was not indicated!
        First configure the following options in the inventory settings:
    
        * Warehouse Section
        1) Enable "Storage Locations";
        2) Enable "Mult-Step Routes"."""
            connector.logger_error('TRYSYNCFROMTTRX', message=erro, model=self._name, res_id=self.id)
        else:
            primary_model = params.get('primary_model') if bool(params.get('primary_model')) else self.primary_model \
                            if hasattr(self, 'primary_model') else None
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            if context['MySelf']:
                if not bool(self.ids):
                    return res
                if bool(primary_model):
                    params['primary_model'] = primary_model
                params.update(self.with_context(context)._GetUriParams(resource,primary_model=primary_model))
                res += self.with_context(context)._CreateUpdateFromTTRx(connector, **params)
            else:
                last_param = get_last_param(resource)
                if bool(last_param) and last_param in params:
                    register = self.with_context(context).TTRxSearch(connector,**params)
                    if not bool(register) or context['ForceUpdate']:
                        res += register.with_context(context)._CreateUpdateFromTTRx(connector, **params)
                    else:
                        res += register
                else:
                    data_list = self.with_context(context)._GetList(connector, resource, **params) or []
                    for data in data_list:
                        params_data = {}
                        params_data.update(params)
                        for key in params_data.keys():
                            if not bool(params_data.get(key,False)):
                                params_data[key] = data.get(key,params_data[key])
                        params_data.update(data)
                        param_uri = self.with_context(context)._GetParamsTTRxToURI(resource, params_data)
                        params_data.update(param_uri)
                        update = True
                        if context['NewOnly']:
                            domain = self._GetTTRxDomainToSearch(data)
                            exist = self.search(domain, limit=1)
                            if bool(exist):
                                update = False
                        if update:
                            CleanDataDict(params_data)
                            res += self.with_context(context)._CreateUpdateFromTTRx(connector, **params_data)
        return res
    
    def _CreateUpdateFromTTRx(self, connector, **params):
        """
            submodal
            primarykey
        """
        connector.logger_info('CREATEUPDATE', message='try create/update a registry from TTRx data in Odoo %s' % str(params), model=self._name, res_id=self.id)
        context = dict(self.env.context or {})
        NoCreate = bool(context.get('NoCreate',False))
        NoUpdate = bool(context.get('NoUpdate',False))
        response, data = self.GetValuesInTTRx(connector, **params)
        exist = self.env[self._name]
        try:
            if bool(response) and not bool(response.get('error')):
                domain = self._GetTTRxDomainToSearch(data)
                exist = self.search(domain, limit=1)
                res = exist.BeforeCreateFromTTRx(connector, response, data)
                if bool(res):
                    if bool(exist):
                        if not NoUpdate:
                            context = dict(self.env.context or {})
                            context['no_rewrite'] = True
                            exist.with_context(context).write(data)
                    else:
                        if not NoCreate:
                            exist = self.create(data)
                exist.AfterCreateFromTTRx(connector,response,data)
                exist._cr.commit()
            elif bool(response) and bool(response.get('error',False)):
                connector.logger_error('CREATEUPDATE', message=str(response.get('error','')), model=self._name, res_id=self.id)
                if not self.env.context.get('NotRaiseError',False):
                    raise UserError(response['error'])
        except Exception as e:
            _logger.warning(f"Error creating or updating from portal {e} 1")
            self.env.cr.rollback()
            connector.logger_error('TRYSYNCFROMTTRX', message=str(e), model=self._name, res_id=self.id)
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
            _logger.warning(f"Error creating or updating from portal {e} 2")
        if not exist:
            # raise UserError(response['error'])
            _logger.warning(f"Error creating or updating from portal {response} 3")
        return exist

    def GetValuesInTTRx(self, connector, **params):
        connector.logger_info('GETREGISTRY', message='try get a registry in TTRx from params:\n%s' % str(params), model=self._name, res_id=self.id)
        primary_model = params.get('primary_model',None)
        resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
        uri_params = self._GetParamURItoTTRx(resource)
        if len(uri_params) > 0:
            if len(self.ids) == 1:
                get_params = self._getUriParamsInSelf(resource,primary_model)
            else:
                get_params = params
            response = self._GetRecord(connector, resource, **get_params)
        else:
            response = params
        data = {}
        if bool(response):
            if not bool(response.get('error')):
                DictAppendNewKeys(params,response)
                data.update(self.FromTTRxToOdoo(connector, response))
                data['connector_id'] = connector.id
        return response, data

    @api.model
    def create(self, values):
        created = super(CustomConnectorSpt, self).create(values)
        for reg in created:
            if reg.auto_create_in_ttr2 and bool(reg.has_connector):
                reg.CreateInTTRx(connector=reg.connector_id,values=values)
        return created

    def CreateInTTRx(self, connector, **params):
        # self.ensure_one()
        connector.logger_info('TRYCREATE', message='try create a new registry from Odoo to TTRx %s' % str(params), model=self._name, res_id=self.id)
        create_response = False
        primary_model = self.primary_model if hasattr(self, 'primary_model') else None
        data = self.FromOdooToTTRx(connector=connector)
        if len(data) > 0:
            params = {'data': data}
            listPKey = self._OdooToTTRxToList(primary_model)
            if bool(listPKey) and not bool(self._GetValueKey(listPKey[-1])):
                resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
                params.update(self._GetUriParams(resource,primary_model=primary_model))
                if bool(self.BeforeCreateInTTRx(**params)):
                    create_response = self._PostRecord(connector, resource, **params) 
                    if bool(create_response) and not bool(create_response.get('erro')):
                        # _logger.info(f"Error creating on portal {error_create_response}")
                        context = dict(self.env.context or {})
                        context['no_rewrite'] = True
                        self.with_context(context).write(create_response)
                    else:
                        error_create_response = create_response.get('erro')
                        _logger.warning(f"Error creating on portal {error_create_response}")
                        self.AfterCreateInTTRx(**params)
                        raise UserError(_(f"Error creating on portal {error_create_response}"))
        return create_response

    def write(self, vals):
        toWrite = self.env[self._name]
        if not self.env.context.get('no_rewrite', False):
            for reg in self:
                if bool(reg.has_connector) and reg._can_send_to_ttr2() and not vals.get('no_send_to_ttr2',False):
                    response = reg.WriteInTTRx(reg.connector_id, **vals)
                    if not bool(response) or not bool(response.get('erro')):
                        toWrite = toWrite + reg
                    else:
                        write_error_mgs = response.get('erro', None)
                        toWrite = toWrite + reg
                        _logger.warning(_(f'Error on editing {write_error_mgs}'))
                        # raise UserError(_(f'Error on editing {write_error_mgs}'))
                else:
                    toWrite = toWrite + self
        else:
            toWrite = toWrite + self
        return super(CustomConnectorSpt, toWrite).write(vals)
        
    def WriteInTTRx(self, connector, **vals):
        # self.ensure_one()
        connector.logger_info('TRYUPDATE', message='try update a old registry from Odoo to TTRx %s' % str(vals), model=self._name, res_id=self.id)
        primary_model = self.primary_model if hasattr(self, 'primary_model') else vals['primary_model'] if bool(vals.get('primary_model')) else None
        listPKey = self._OdooToTTRxToList(primary_model)
        data = self.FromOdooToTTRx(connector=connector,values=vals)
        write_response = None
        if len(data) > 0 and bool(listPKey) and bool(self._GetValueKey(listPKey[-1])):
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            params = {'data': self.FromOdooToTTRx(connector=connector,values=vals), 'values': vals}
            params.update(self._GetUriParams(resource,primary_model=primary_model))            
            if bool(self.BeforeWriteInOdoo(**params)):
                write_response = self._PutRecord(connector, resource, **params)
                params['response'] = write_response 
                self.AfterWriteInOdoo(**params)
            else:
                write_response = False
        return write_response

    def unlink(self):
        toUnlink = self.env[self._name]
        for record in self:
            if bool(record.has_connector) and record.connector_id.auto_delete:
                response = record.DeleteInTTRx(connector=record.connector_id)
                if not bool(response) or not bool(response.get('erro')):
                    toUnlink = toUnlink + record
                else:
                    raise UserError(f'Erro: {response.get("erro", "")}')
            else:
                toUnlink = toUnlink + record
        return super(CustomConnectorSpt, toUnlink).unlink()

    def DeleteInTTRx(self, connector, **params):
        # self.ensure_one()
        connector.logger_info('TRYDELETE', message='try delete a registry from Odoo to TTRx %s' % str(params), model=self._name, res_id=self.id)
        primary_model = self.primary_model if hasattr(self, 'primary_model') else None
        listPKey = self._OdooToTTRxToList(primary_model)
        if bool(listPKey) and bool(self._GetValueKey(listPKey[-1])) and connector.auto_delete:
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            params ={'data': self.FromOdooToTTRx(connector=connector,values=params)}
            params.update(self._GetUriParams(resource,primary_model=primary_model))            
            if bool(self.BeforeUnlinkInOdoo(**params)):
                delete_response = self._DeleteRecord(connector, resource, **params)
                params['response'] = delete_response 
                self.AfterUnlinkInOdoo(**params)
                return delete_response
        return False

    def action_send(self):
        return True

    def action_refresh(self):
        for reg in self:
            if reg.has_connector:
                reg.SyncFromTTRx(reg.connector_id,MySelf=True,ForceUpdate=True)
        return True

    def action_test(self):
        return True

class ConnectorSptLastUpdate(models.Model):
    _name = 'connector.spt.lastupdate'
    _description = 'Last Update Connector'
    
    name = fields.Datetime('Date Updated')
    connector_id = fields.Many2one('connector.spt', 'Connector')
    company_id = fields.Many2one('res.company', 'Company', related="connector_id.company_id")
    method = fields.Char('Method')
        
class ConnectorSpt(models.Model):
    _name = 'connector.spt'
    _description = 'Connector TrackTrace V2'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'name'
    

    name = fields.Char('Name', required=1, copy=False, readonly=True, states=READ_STATE)
    
    company_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.user.company_id, copy=False, 
                                 readonly=True, states=READ_STATE)

    api_environment = fields.Selection([('test', 'Testing'), ('production', 'Production')], string='Environment', default='test', copy=False, readonly=True, states=READ_STATE)
    
    api_key = fields.Char('API Key', copy=False, readonly=True, states=READ_STATE)
    portal_url = fields.Char('Portal Url', readonly=True, states=READ_STATE)

    api_url = fields.Char('TTrx2 API Url',  compute="_compute_api_url", store=False)
    
    auto_delete = fields.Boolean('Auto Delete', default=False, required=True)

    
    auto_vacuum = fields.Boolean('Auto Vacuumm', default=True, required=True)

    auto_data_sync = fields.Boolean('Auto Data Sync', default=True, required=True)

    state = fields.Selection(selection=[('draft', 'Not Confirmed'),('stop', 'Paused'),('done', 'Confirmed')], string='Status', required=True, 
                             readonly=True, copy=False, tracking=True, default='draft')
    auto_create_new_partner = fields.Boolean("Auto Create New Trading Partner?", default=True)
    
    last_update_date = fields.Date('Last Update in', default='2020-01-01')
    
    log_ids = fields.One2many('tracktrace.log.spt','connector_id', string="Logs", readonly=True)
    
    updated_ids = fields.One2many('connector.spt.lastupdate','connector_id', string="Updates")
    
    active = fields.Boolean("Active", default=True)

    wharehouse_id = fields.Many2one('stock.warehouse', string="Default Warehouse", domain=[('reception_steps','=','three_steps')])
    
    lot_number = fields.Selection([
        ('always_required', 'Always Required'),
        ('optional_to_add_inventory_required_to_sell', 'Optional to add inventory, required to sell'),
        ('always_optional', 'Always Optional')], string='Lot Number', default="always_required")
    
    serial_number = fields.Selection([
        ('always_required', 'Always Required'),
        ('optional_to_add_inventory_required_to_sell', 'Optional to add inventory, required to sell'),
        ('always_optional', 'Always Optional')], string='Serial Number', default="always_required")
    
    strict_inventory_policies = fields.Boolean('Strict Inventory Policies', default=False)
    
    edi_source = fields.Selection([
        ('require_product_reception_verification', 'Require product reception verification'),
        ('move_to_inventory_unless_lot_missing', 'Move to inventory, unless lot is missing'),
        ('move_to_inventory_unless_lot_or_serial_missing', 'Move to inventory, unless lot or serial is missing'),
        ('move_to_inventory', 'Move to inventory')], string='From EDI Source', default="move_to_inventory")
    epcis_source = fields.Selection([
        ('require_product_reception_verification', 'Require product reception verification'),
        ('move_to_inventory_unless_lot_missing', 'Move to inventory, unless lot is missing'),
        ('move_to_inventory_unless_lot_or_serial_missing', 'Move to inventory, unless lot or serial is missing'),
        ('move_to_inventory', 'Move to inventory')], string='From EPCIS Source', default="move_to_inventory")
    other_source = fields.Selection([
        ('require_product_reception_verification', 'Require product reception verification'),
        ('move_to_inventory_unless_lot_missing', 'Move to inventory, unless lot is missing'),
        ('move_to_inventory_unless_lot_or_serial_missing', 'Move to inventory, unless lot or serial is missing'),
        ('move_to_inventory', 'Move to inventory')], string='From Other Source', default="move_to_inventory")
    unknown_products = fields.Selection([
        ('goes_to_products_reception', 'Goes to products reception'),
        ('decline_product', 'Refuse/Decline the product'),
        ('add_product', 'Add the product to the product database'), ], string='Unknown Products', default='add_product')
    unknown_partners = fields.Selection([
        ('decline_partner', 'Refuse/Decline the partner'),
        ('add_partner', 'Add the product to the partner database'), ], string='Unknown Partner', default='add_partner')
    auto_send_picking = fields.Selection([
        ('auto', 'Auto Send'),
        ('manual', 'Manual Send'), ], string='Send Picking', default='auto')

    auto_approve_outbound = fields.Selection([
        ('auto', 'Auto Approve'),
        ('manual', 'Manual Approve'), ], string='Approve Outbound', default='auto')
    
    itens_per_page = fields.Integer(string='Itens per page', default=100)

    def _get_parameter_raise_exception(self):
        params = self.env['ir.config_parameter'].sudo()
        return bool(params.get_param('ttrx2_connector_spt.raise_exception_on_cron', default=False))

    def _get_context_cron(self, context={}):
        raise_exception_on_cron=self._get_parameter_raise_exception()
        if not bool(context):
            context = dict(self.env.context or {})
        context['NotRaiseError'] = raise_exception_on_cron
        return context

    @api.model
    def get_data(self):
        #TODO: Fazer o domínio
        company = self.env.company
        connector = self.search([('company_id','=',company.id),('state','in',['stop','done'])],limit=1)
        if not bool(connector):
            var = {
                'values': {
                    'show_demo': True,
                    'state': connector.state,
                    'company': company.id,
                    'connector': connector.id,
                    'name': 'This connector has not been verified.',
                    'purchase': {
                        'last_update': '30/06/2022',
                        'itens': '0126',
                        'todo': '0126',
                    },
                    'sale': {
                        'last_update': '30/06/2022',
                        'itens': '0289',
                        'todo': '0289',
                    },
                    'pickin': {
                        'last_update': '30/06/2022',
                        'itens': '0259',
                        'todo': '0259',
                    },
                    'pickout': {
                        'last_update': '30/06/2022',
                        'itens': '0115',
                        'todo': '0115',
                    },
                },
            }
        else:
            in_picking_type = self.env['stock.picking.type'].search([('code','=','incoming')])
            out_picking_type = self.env['stock.picking.type'].search([('code','=','outgoing')])
            purchases = self.env['purchase.order'].search([('company_id','=',company.id)])
            sales = self.env['sale.order'].search([('company_id','=',company.id)])
            in_picking = self.env['stock.picking'].search([('company_id','=',company.id),
                                                           ('picking_type_id','in',in_picking_type.ids)])
            out_picking = self.env['stock.picking'].search([('company_id','=',company.id),
                                                           ('picking_type_id','in',out_picking_type.ids)])
            var = {
                'values': {
                    'show_demo': False,
                    'name': connector.name,
                    'state': connector.state,
                    'company': company.id,
                    'connector': connector.id,
                    'purchase': {
                        'last_update': connector.last_update_date,
                        'itens': "{0:0>4}".format(len(purchases)),
                        'todo': "{0:0>4}".format(len(purchases.filtered(lambda x: x.uuid == False))),
                    },
                    'sale': {
                        'last_update': connector.last_update_date,
                        'itens': "{0:0>4}".format(len(sales)),
                        'todo': "{0:0>4}".format(len(sales.filtered(lambda x: x.uuid == False))),
                    },
                    'pickin': {
                        'last_update': connector.last_update_date,
                        'itens': "{0:0>4}".format(len(in_picking)),
                        'todo': "{0:0>4}".format(len(in_picking.filtered(lambda x: x.uuid == False))),
                    },
                    'pickout': {
                        'last_update': connector.last_update_date,
                        'itens': "{0:0>4}".format(len(in_picking)),
                        'todo': "{0:0>4}".format(len(in_picking.filtered(lambda x: x.uuid == False))),
                    },
                },
            }
        return var

    @api.model
    def create_action(self, action_ref, title, connector_id=False):
        action = self.env["ir.actions.actions"]._for_xml_id(action_ref)
        if title:
            action['display_name'] = title
        action['views'] = [(False, view) for view in action['view_mode'].split(",")]
        if bool(connector_id):
            action['context'] = {'default_connector_id': connector_id}
            action['domain'] = [('connector_id','=',connector_id)]
        return {'action': action}

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

    @api.onchange('company_id', 'api_key', 'api_environment')
    def onchange_company_id(self):
        if bool(self.company_id):
            self.name = "This is the company connector %s" % (self.company_id.name)
        else:
            self.name = "This is a connector"
        self.state = 'draft'

    @api.onchange("api_environment", "api_key", "name")
    def onchange_api_environment_key(self):
        self.state = "draft"

    def action_test(self):
        for reg in self:
            reg.auto_impexp_all()

    def action_confirm(self):
        for reg in self:
            resp = reg.test_connection()

    def test_connection(self):
        for reg in self:
            msg = []
            if not bool(reg.company_id):
                msg += ["The company was not indicated;"]
            else:
                company = reg.company_id
                if not bool(company.name):
                    msg += ["Enter your company's address;"]
                if not bool(company.zip):
                    msg += ["Enter your company's zip;"]
                if not bool(company.city):
                    msg += ["Enter your company's city;"]
                if not bool(company.state_id):
                    msg += ["Enter your company's state;"]
                if not bool(company.country_id):
                    msg += ["Enter your company's country;"]
            if not bool(reg.api_key):
                msg += ["Enter the API key to connect to the TrackTraceRx portal;"]
            if not bool(reg.api_environment):
                msg += ["Enter the API Environment to connect to the TrackTraceRx portal;"]
            if not bool(reg.wharehouse_id):
                msg += ["Inform which warehouse will be used by the connector to organize the locations;"]
            if len(msg) > 0:
                value = "Errors in the connector %s: \n" % reg.name
                value += "\n".join(msg)
                raise UserError(value)
            reg.state = 'draft'
            queries = {'status': 'AVAILABLE'}
            resp = TrackTraceApi2(self.api_url, self.api_key).GetList('product.spt', queries=queries)
            if bool(resp) and resp.get('sucess',False):
                title = "Connected!"
                reg.company_id.ttrx_api_tested = True
                reg.company_id.api_key = self.api_key
                message = "The connection with TTr2 is OK!"
                self.message_post(body=message)
                reg.state = 'stop'
            else:
                raise UserError('Error in connection with TTr2.\n%s' % str(resp))

    def action_invalidate(self):
        for reg in self:
            reg.state = 'draft'

    def action_pause(self):
        for reg in self:
            reg.state = 'stop'

    def action_continue(self):
        for reg in self:
            crow_id = self.env.ref('ttrx2_connector_spt.ir_cron_get_data_base').sudo()
            if bool(crow_id) and not crow_id.active:
                crow_id.nextcall = fields.Datetime.now() + timedelta(minutes=1)
                crow_id.active = True
            reg.state = 'done'
        
   
    def action_impexp_partner(self):
        """ Function to import and export as select
    
        ..todo:: Find more information about it
    
        :return: None
    
        """
        # self.ensure_one()
    
        try:
            form_view = self.env.ref('ttrx2_connector_spt.view_sync_partner_spt_wizard_form')
    
        except ValueError:
            form_view = False
    
        return {
            'name': 'Sync Partner',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.partner.spt.wizard',
            'view_id': form_view.id,
            'views': [(form_view.id, 'form')],
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
    
    def action_impexp_salers(self):    
        """ Function to import and export as select
    
        ..todo:: Find more information about it
    
        :return: None
    
        """
        # self.ensure_one()
    
        try:
            form_view = self.env.ref('tracktrace_odoo_connector_spt.sync_saler')
    
        except ValueError:
            form_view = False
    
        return {
            'name': 'Sync saler',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.sale.spt.wizard',
            'view_id': form_view,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_connector_id': self.id}
         }
    
    def _cron_unlink_logs(self):  
        self.logger_info('CRON-DELETE-LOGS', '*** Start Cron Unlink Logs ***', self._name, self.id)
        try:
            date_limit = (fields.Datetime.now() - timedelta(days=30)).strftime(DSDTF)
            regs = self.search([('state','=','done'),('auto_vacuum','=',True)])
            for reg in regs:
                Logs = self.env['tracktrace.log.spt'].search([('create_date','<=',date_limit),('connector_id','=',reg.id)])
                i = len(Logs)
                if i > 0:
                    Logs.unlink(); 
        except Exception as e:
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        finally:
            self.logger_info('CRON-DELETE-LOGS', '*** Stop Cron Unlink Logs ***', self._name, self.id)
            
    def _cron_get_data_base(self):
        self.env['tracktrace.log.spt'].addLog(self.id, model=self._name, method='UPDATE-DATA-BASE', message='*** Starting Crow ***')
        context = self._get_context_cron()
        try:
            regs = self.search([('state','=','done'),('auto_data_sync','=',True)])
            for reg in regs:
                res = reg.with_context(context).auto_impexp_all()
        except Exception as e:
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        finally:
            self.env['tracktrace.log.spt'].addLog(self.id, model=self._name, method='UPDATE-DATA-BASE', message='*** Ending Crow ***')

    def _cron_get_data_queue(self):
        self.logger_info('CRON-LIST-QUEUE', '*** Starting Crow ***', self._name, self.id)
        try:
            regs = self.search([('state','=','done'),('auto_data_sync','=',True)])
            for reg in regs:
                reg.auto_imp_queue()
        except Exception as e:
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
        finally:
            self.logger_info('CRON-LIST-QUEUE', '*** Ending Crow ***', self._name, self.id)

    def _cron_get_data_move(self): 
        self.logger_info('CRON-LIST-ORDERS', '*** Starting Crow ***', self._name, self.id)
        context = self._get_context_cron()
        regs = self.search([('state','=','done'),('auto_data_sync','=',True)])
        try:
            for reg in regs:
                res1 = reg.with_context(context).auto_impexp_purchase()
                self.logger_info('CRON-LIST-ORDERS-PO-END', '%s' % str(len(res1)), self._name, self.id)
                res2 = reg.with_context(context).auto_impexp_sale()
                self.logger_info('CRON-LIST-ORDERS-SO-END', '%s' % str(len(res2)), self._name, self.id)
        except Exception as e:
            self.logger_error('CRON-LIST-ORDERS', str(e), self._name, self.id)
        finally:
            self.logger_info('CRON-LIST-ORDERS', '*** Ending Crow ***', self._name, self.id)

    def _cron_get_transfers_in(self, raise_error=False):
        self.logger_info('CRON-LIST-TRANSF-IN', '*** Starting Crow ***', self._name, self.id)
        try:
            context = self._get_context_cron()
            res = self.with_context(context).import_transfers_outbound()
        except Exception as e:
            self.logger_error('CRON-LIST-TRANSF-IN', str(e), self._name, self.id)
        finally:
            self.logger_info('CRON-LIST-TRANSF-IN', '*** Ending Crow ***', self._name, self.id)

    def _cron_get_transfers_out(self, raise_error=False):
        self.logger_info('CRON-LIST-TRANSF-OUT', '*** Starting Crow ***', self._name, self.id)
        try:
            context = self._get_context_cron()
            res = self.with_context(context).import_transfers_outbound()
        except Exception as e:
            self.logger_error('CRON-LIST-TRANSF-OUT', str(e), self._name, self.id)
        finally:
            self.logger_info('CRON-LIST-TRANSF-OUT', '*** Ending Crow ***', self._name, self.id)

    def auto_impexp_all(self):
        self.ensure_one()
        if self.state == 'done':
            try:
                self.env['license.types.management.spt'].SyncFromTTRx(connector=self)
                if self.unknown_partners == 'add_partner':
                    self.env['res.partner'].SyncFromTTRx(connector=self)
                    self.env['manufacturers.spt'].SyncFromTTRx(connector=self)
                    self.env['thrid.party.logistic.provide.spt'].SyncFromTTRx(connector=self)
                self.env['locations.management.spt'].SyncFromTTRx(connector=self)
                self.env['products.status.spt'].SyncFromTTRx(connector=self)
                self.env['products.types.spt'].SyncFromTTRx(connector=self)
                self.env['identifiers.types.spt'].SyncFromTTRx(connector=self)
                self.env['product.requirement.spt'].SyncFromTTRx(connector=self)
                self.env['product.category'].SyncFromTTRx(connector=self)
                self.env['pack.size.type.spt'].SyncFromTTRx(connector=self)
                self.env['pharma.dosage.forms.spt'].SyncFromTTRx(connector=self)
                if self.unknown_products == 'add_product':
                    self.env['product.spt'].SyncFromTTRx(connector=self)
                self.last_update_date = fields.date.today()
            except Exception as e:
                self.env['tracktrace.log.spt'].addLog(self.id, model=self._name, method='CROWUPDATEDATA', 
                                                      message='Error in try refreshing a registry from TTRx data in Odoo (%s)' % str(e), 
                                                      typein='error')
                return False
        return True

    def auto_impexp_purchase(self, NewOnly=True):
        self.ensure_one()
        orders = self.env['purchase.order']
        if self.state == 'done':
            if not NewOnly:
                order_ids = self.env['purchase.order']._get_orders_to_update_from_ttrx()
                for order_id in order_ids:
                    order = self.env['purchase.order'].browse(order_id)
                    order.SyncFromTTRx(connector=self, MySelf=True)
                    orders |= order
            orders |= self.env['purchase.order'].SyncFromTTRx(connector=self, NewOnly=True)
        return orders
       
    def auto_impexp_sale(self, NewOnly=True):
        self.ensure_one()
        orders = self.env['sale.order']
        if self.state == 'done':
            if not NewOnly:
                order_ids = self.env['sale.order']._get_orders_to_update_from_ttrx()
                for order_id in order_ids:
                    order = self.env['sale.order'].browse(order_id)
                    order.SyncFromTTRx(connector=self, MySelf=True)
                    orders |= order
            orders |= self.env['sale.order'].SyncFromTTRx(connector=self, NewOnly=True)
        return orders

    def auto_imp_queue(self):
        self.ensure_one()
        if self.state == 'done':
            try:
                self.env['queue.spt'].SyncFromTTRx(connector=self)           
            except Exception as e:
                self.env['tracktrace.log.spt'].addLog(self.id, model=self._name, method='CROWUPDATEQUEUE', 
                                                      message='Error in try refreshing a registry from TTRx data in Odoo (%s)' % str(e), 
                                                      typein='error')
                return False
        return True

    def import_transfers_inbound(self):
        res = self.env['stock.picking']
        lines = self.env['purchase.order.line'].search([('state','in',['purchase']),('uuid','!=',False)])
        order_ids = set()
        for line in lines.filtered(lambda x: x.qty_received < x.product_qty):
            order_ids.add(line.order_id.id)
        orders = self.env['purchase.order'].browse(order_ids) if len(order_ids) > 0 else self.env['purchase.order']
        for order in orders:
            transfers = order.picking_ids.filtered(lambda x: bool(x.uuid) and x.is_verified == False and x.state not in ['cancel'])
            if len(transfers) > 0:
                res |= order.CreateTTRxPicking()
        return res

    def import_transfers_outbound(self):
        res = self.env['stock.picking']
        lines = self.env['sale.order.line'].search([('state','in',['sale']),('uuid','!=',False)])
        order_ids = set()
        for line in lines.filtered(lambda x: x.qty_delivered < x.product_uom_qty):
            order_ids.add(line.order_id.id)
        orders = self.env['sale.order'].browse(order_ids) if len(order_ids) > 0 else self.env['sale.order']
        for order in orders:
            transfers = order.picking_ids.filtered(lambda x: bool(x.uuid) and x.is_shipped == False and x.state not in ['cancel'])
            if len(transfers) > 0:
                res |= order.CreateTTRxPicking()
        return res

    def logger_info(self, method, message, model=False, res_id=False):
        log = self.env['tracktrace.log.spt']
        val = {
            'connector_id': self.id,
            'method': method,
            'message': message,
            'model': model,
            'res_id': res_id,
            'type': 'info',
            'create_date': fields.Datetime.now(),
        }
        return log.create(val)

    def logger_warn(self, method, message, model=False, res_id=False):
        log = self.env['tracktrace.log.spt']
        val = {
            'connector_id': self.id,
            'method': method,
            'message': message,
            'model': model,
            'res_id': res_id,
            'type': 'warn',
            'create_date': fields.Datetime.now(),
        }
        return log.create(val)

    def logger_error(self, method, message, model=False, res_id=False):
        log = self.env['tracktrace.log.spt']
        val = {
            'connector_id': self.id,
            'method': method,
            'message': message,
            'model': model,
            'res_id': res_id,
            'type': 'error',
            'create_date': fields.Datetime.now(),
        }
        return log.create(val)
       
