import logging
import urllib.error
import urllib.request
import requests
_logger = logging.getLogger(__name__)

from . import service
from ..tools import CleanDataDict

   


class TrackTraceApi2(object):
    _queries_words = ['sort_by','sort_by_asc','nb_per_page','page','licence_type_id','value','po_nbr']
    
    def __init__(self, api_url, api_key):
        """
        Inicialização do objeto TrackTraceApi2. 
        :param api_url: Url da API da TrackTrace2;
        :param api_key: Chave da API.
        """
        self.api_url = api_url
        self.api_key = api_key

    def _query(self, queries):
        res = ''
        if bool(queries):
            vals = []
            for key,value in queries.items():
                vals.append('%s=%s' % (str(key),str(value)))
            res = '?%s' % ('&'.join(vals))
        return res
    
    def _count_params(self, resource):
        uri = service.get_uri(resource)
        open = uri.count('{')
        close = uri.count('}')
        return min(open,close)

    def _get_params_uri(self, resource, method):
        uri = service.get_uri(resource, method)
        res = []
        if bool(uri):
            a = uri.find('{')
            while a > 0:
                b = uri.find('}')
                if b > a:
                    val = uri[a+1:b]
                    if len(val) > 0:
                        res.append(val)
                    uri = uri[:a-1]+uri[b+1:]
                    a = uri.find('{')
        return res

    def GetIdentifierField(self, resource, defaut=None):
        uri = service.get_uri(resource,'GET')
        x1 = str(uri).rfind('{')
        x2 = str(uri).rfind('}')
        if x1 >= 0 and x2 > x1:
            return uri[x1+1:x2]
        else:
            return defaut

    def QueriesToDict(self, **kwargs):
        res = {}
        for key, value in kwargs.items():
            if key in self._queries_words and key != 'data': 
                res[key] = value
        CleanDataDict(res)
        return res

    def ParamsToDict(self, resource, **kwargs):
        res = {}
        params = self._get_params_uri(resource,'GET')
        data = kwargs['data'] if bool(kwargs.get('data')) else {}
        for param in params:
            res[param] = kwargs.get(param)
            if not bool(res[param]):
                res[param] = data.get(param)
        CleanDataDict(res)
        return res

    def GetRecord(self, resource, **kwargs):
        return self._make_request('GET', resource, params=kwargs.get('params',{}))
    
    def GetList(self, resource, **kwargs):
        return self._make_request('LIST', resource, params=kwargs.get('params',{}), queries=kwargs.get('queries',{}))
    
    def PostRecord(self, resource, **kwargs):
        return self._make_request('POST', resource, params=kwargs.get('params',{}), data=kwargs.get('data',{}))
    
    def PutRecord(self, resource, **kwargs):
        return self._make_request('PUT', resource, params=kwargs.get('params',{}), data=kwargs.get('data',{}))
    
    def DeleteRecord(self, resource, **kwargs):
        return self._make_request('DELETE', resource, params=kwargs.get('params',{}))

    def make_request(self, method, resource, headers=None, params={}, queries={}, data={}):
        return self._make_request(method, resource, headers=headers, params=params, queries=queries, data=data)
        
    def _make_request(self, method, resource, headers=None, params={}, queries={}, data={}):
        """
        Sends the request to the URI with the method passing the parameters and data
        :param method: Call method URI [GET,POST,PUT]
        :param uri: URI to call;
        :param params: List of parameters to be sent along with the method.
        :param: data: Data passed in the request.
        """
        msg = []
        sucess = False
        req = None
        api_url = ''
        json = None
        if method not in service.METHODS:
            msg.append('Invalid method %s' % method)
        
        if not bool(self.api_key):
            msg.append('Inform the API Key')

        if not bool(self.api_url):
            msg.append('Inform the API URL')

        uri = ''
        list_param = None
        if not service.uri_exist(resource):
            msg.append('Resource does not exist')
        else:
            uri += service.get_uri(resource,method)
            list_param = self._get_params_uri(resource, method)
            if len(list_param) > 0:
                if isinstance(params, dict):
                    for prm in list_param:
                        if not bool(params.get(prm)):
                            msg.append('Parameter %s not found' % prm)
                    if len(msg) == 0:
                        uri = uri.format(**params)
                else:
                    new_params = {}
                    count = 0
                    for prn in list_param:
                        new_params[prn] = params[count] 
            # else:
            #     param_tot = self._count_params(resource)
            #     dif_param = abs(len(params) - param_tot)
            #     if dif_param != 0:
            #         msg.append('%s parameters are missing' % dif_param)
            #     else:
            #         uri = uri.format(*params)
        api_url += '%s%s%s' % (self.api_url,uri,self._query(queries))

        if len(msg) == 0:
            if method == service.METHOD_LIST:
                method = service.METHOD_GET
        
            api_header = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'Authorization': self.api_key,
            }
            if bool(headers):
                api_header.update(headers)

            try:
                _logger.debug('>>> Uri TTRx %s and data = %s' % (api_url,str(data)))
                req = requests.request(method=method, url=api_url, headers=api_header, data=data or {})
                json = req.json()
                _logger.debug('>>> Resposta %s' % str(req))
                if 200 <= req.status_code <= 299:
                    msg.append("Successful request.")
                    sucess = True
                else:
                    msg.append('[%s] %s' % (json.get('code','no code'),json.get('message','no message')))
                    
            except urllib.error.HTTPError as e:
                msg.append("Failed request, please check your request.\n %s \n\r %s" % (api_url, e.read().decode("utf8", 'ignore')))
            except urllib.error.URLError as e:
                msg.append("Failed to send request, please check your API connection key.\n %s \n\r %s" % (api_url, e.reason))
            except Exception as e:
                msg.append("Failed to connect, please check your Internet\n\r %s" % str(e))

        return {
            'sucess': sucess,
            'message': msg,
            'answer': req,
            'url': api_url,
            'status_code': req.status_code if (bool(req)) else None,
            'json': json,
        }
        
        