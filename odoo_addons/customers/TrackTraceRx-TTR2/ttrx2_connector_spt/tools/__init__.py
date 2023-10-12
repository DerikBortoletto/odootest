from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

DEFAULT_TTRX2_DATETIME = '%Y-%m-%d %H:%M:%S'
DEFAULT_TTRX2_DATE = '%Y-%m-%d'

def DateTimeToOdoo(vlDatetime):
    res = None
    if bool(vlDatetime):
        if isinstance(vlDatetime, dict):
            date = vlDatetime['date'][0:10]
            hour = vlDatetime['date'][11:19]
        else:
            date = vlDatetime[0:10]
            hour = vlDatetime[11:19]
        vlDatetime = "%s %s" % (date,hour)
        try:
            pDatetime = datetime.strptime(vlDatetime, DEFAULT_TTRX2_DATETIME)
            res = pDatetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        except:
            pass
    return res

def DateToOdoo(vlDate):
    res = None
    if bool(vlDate):
        vlDate = vlDate[0:10]
        try:
            pDate = datetime.strptime(vlDate, DEFAULT_TTRX2_DATETIME)
            res = pDate.strftime(DEFAULT_SERVER_DATE_FORMAT)
        except:
            pass
    return res


def CleanDataDict(values):
    for key, value in dict(values).items():
        if value is None:
            del values[key]

def CleanDataList(values):
    res = []
    for value in values:
        if value is not None:
            res.append(value)

def StrToFloat(value):
    res = 0.0
    if bool(value):
        res = str(value).replace(',', '.')
        try:
            res = float(res)
        except:
            pass
    return res

def DictAppendNewKeys(dict_in, dict_out):
    for key,value in dict_in.items():
        if dict_out.get(key) == None:
            dict_out[key] = value
