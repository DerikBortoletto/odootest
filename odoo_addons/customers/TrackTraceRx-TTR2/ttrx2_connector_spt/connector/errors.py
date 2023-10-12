
class TTr2ApiRequestError(Exception):
    def __init__(self, request, response=None):
        self.request = request
        self.response = response
        self.message = 'Request response failed %s, %s' % (str(request),str(response)) if bool(response) \
                       else 'Request response failed %s' % str(request)

    def __str__(self):
        return self.message

class TTr2ApiResourceMethodError(Exception):
    def __init__(self,Resource,Method):
        self.message = "The %s method, %s resource has no specific URL. Please refer to the TrackTrace2 manual" % (str(Resource),str(Method))
        
    def __str__(self):
        return self.message
