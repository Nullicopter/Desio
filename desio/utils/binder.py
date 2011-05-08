"""
This is a wrapper for our api.

from desio.utils import binder
c = binder.Client('robot@binder.io', 'f0ckm@rthA')
c._request('/change/get', parse_status='completed')

"""
import subprocess, binascii, urllib, httplib, base64, os.path, simplejson as json, tempfile
from pylons_common.lib.utils import objectify
from desio.utils import image

from collections import defaultdict as dd

CONTENT_TYPE_OCTET = 'application/octet-stream; charset="utf-8"'
CONTENT_TYPE_URL_ENCODED = "application/x-www-form-urlencoded"

METHOD_POST = 'POST'
METHOD_GET = 'GET'

def l(s):
    print s

class Client(object):
    
    def __init__(self, username, password, host='www.dev.local', port='5000', prefix='/api/v1'):
        self._auth = base64.b64encode("%s:%s" % (username, password))
        self._host = host
        self._port = port
        self._prefix = prefix
    
    def _unjsonify(self, response):
        """
        Takes the response from a client_async-decorated action
        and returns a python object derived from it.
        """
        return objectify(json.loads(response))
    
    def _request(self, url, id=None, headers=None, content_type=CONTENT_TYPE_URL_ENCODED, method=METHOD_POST, body=None, **kwargs):
        """
        """
        
        params = urllib.urlencode(kwargs.items())
        
        if body is None and content_type == CONTENT_TYPE_URL_ENCODED and method == METHOD_POST:
            body = params
        
        h = {
            "Content-type": content_type,
            "Authorization": "Basic " + self._auth,
            'Accept': 'application/json'
        }
        if headers: h.update(headers)
        
        if url[0] == '/': url = url[1:]
        url = os.path.join(self._prefix, url)
        
        if id:
            url = os.path.join(url, id)
        
        if method == METHOD_GET:
            url = url + '?' + params
        
        conn = httplib.HTTPConnection(self._host, port=self._port)
        conn.request(method, url, body, h)
        
        response = conn.getresponse()
        data = response.read()
        
        try:
            data = self._unjsonify(data)
        except: pass
        
        return response.status, data
    
    def get(self, module, fn, method=METHOD_GET, **k):
        return self._request(os.path.join(module, fn), method=METHOD_GET, **k)
    
    def post(self, module, fn, method=METHOD_POST, **k):
        return self._request(os.path.join(module, fn), method=METHOD_POST, **k)

class FireworksExtractor(object):
    
    DOWNLOAD_URL = '/file/change/%s'
    
    def __init__(self, username, password, host='www.dev.local', port='5000'):
        self.c = Client(username, password, host=host, port=port)
    
    def download_file(self, url):
        
        l('Downloading file from %s' % url)
        
        h = {
            "Authorization": "Basic " + self.c._auth,
            'Accept': 'application/octet-stream'
        }
        
        conn = httplib.HTTPConnection(self.c._host, port=self.c._port)
        conn.request(METHOD_GET, url, headers=h)
        
        response = conn.getresponse()
        data = response.read()
        
        if response.status == 200:
            f, name = tempfile.mkstemp('.png')
            if isinstance(f, int):
                f = open(name, 'wb')
            
            f.write(data)
            f.close()
            
            return name
        else:
            l(data)
        
        return None
    
    def upload_extract(self, extracted_file, index, change):
        l('Uploading extract %d: %s for change %s' % (index, extracted_file, change.change_eid))
        
        headers = {
            'X-Up-Order-Index': index,
            'X-Up-Type': extracted_file.extract_type
        }
        
        f = open(extracted_file.filename, 'rb')
        body = f.read()
        f.close()
        
        print self.c.post('change', 'upload_extract', id=change.change_eid, headers=headers, content_type=CONTENT_TYPE_OCTET, body=body)

    def generate_diffs(self, extracts, change):
        
        if change.version == 1: return []
        
        status, prev_file = self.c.get('file', 'get', id=change.file_eid, version=change.version-1)
        if status == 200:
            prev_file = prev_file.results
            prev_extracts = [e for e in prev_file.extracts if e.extract_type == image.EXTRACT_TYPE_FULL]
            extracts = [e for e in extracts if e.extract_type == image.EXTRACT_TYPE_FULL]
            
            res = []
            for i in range(min(len(prev_extracts), len(extracts))):
                prev_fname = self.download_file(prev_extracts[i].url)
                cur_fname = extracts[i].filename
                
                res.append(image.Extractor.difference(prev_fname, cur_fname))
            
            return res
        
        return []
        
    def extract_file(self, filename, change):
        l('Extracting file for change %s from %s' % (change.change_eid, filename))
        
        indices = dd(lambda: 0)
        
        #set status to in progress
        #self.c.post('change', 'edit', change=change.change_eid, parse_status=image.PARSE_STATUS_IN_PROGRESS)
        
        ext = image.FWPNGExtractor(None, filename=filename)
        
        extracts, status = ext.extract(async_extract=False)
        extracts += self.generate_diffs(extracts, change)
        for extract in extracts:
            self.upload_extract(extract, indices[extract.extract_type], change)
            indices[extract.extract_type] += 1
        
        # set status to completed
        #self.c.post('change', 'edit', change=change.change_eid, parse_status=image.PARSE_STATUS_COMPLETED)
    
    def get_changes(self):
        return self.c.get('change', 'get', parse_status='pending')
    
    def run(self):
        status, resp = self.get_changes()
        
        changes = resp.results
        if status == 200:
            for ch in changes:
                if ch.parse_type == image.PARSE_TYPE_FIREWORKS_CS5:
                    fname = self.download_file(self.DOWNLOAD_URL % ch.change_eid)
                    if fname:
                        self.extract_file(fname, ch)
        else:
            l('change/get Status %s' % status)
    
if __name__ == '__main__':
    
    import sys
    c = FireworksExtractor(*sys.argv[1:])
    c.run()
