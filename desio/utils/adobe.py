"""
from desio.utils.adobe import Client
c = Client()
c.connect('localhost')
c.call('fw', 'openDocument', 'file:///Macintosh%20HD/Users/benogle/work/git/desio/images/fwpng/adgroup_frameworks_CS5.png', False, True)

c.call('fw', 'openDocument', 'file:///Macintosh%20HD/Users/benogle/work/git/desio/images/fwpng/adgroup_frameworks_CS3.png', False, True)

x = c.call('fw', 'exportPages', None, 'Images', 'All', 'file:///Macintosh%20HD/Users/benogle/work/git/desio/images/convert')

for i in range(230000, 250000):
    try:
        y = c.call(i, 'pageName', command='get')
        print '!!!', i
        break
    except: pass
"""

import socket
from xml.etree import ElementTree

class AdobeException(Exception):
    def __init__(self, code):
        self.code = code
    def __repr__(self):
        return 'AdobeException(%s)' % self.code

class Client(object):
    
    TYPES = {
        'str': 'string',
        'int': 'int',
        'unicode': 'string',
        'float': 'double',
        'bool': 'bool'
    }
    
    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self, host, port=12124):
        self._sock.connect((host, port))
    
    def send(self, payload):
        
        if ord(payload[-1]) != 0:
            payload = payload+'\0'
        
        return self._sock.send(payload)
    
    def recv(self):
        
        res = []
        r = self._sock.recv(1)
        while ord(r):
            res.append(r)
            r = self._sock.recv(1)
        
        out = ''.join(res)
        print out
        return out
    
    def call(self, obj, function, *args, **kw):
        """
        effectively obj.function(*args)
        """
        command = kw.get('command') or 'func'
        
        call = ['<%s name="%s" obj="%s">' % (command, function, obj)]
        
        for i, a in enumerate(args):
            if a == None:
                call.append('<null order="%d" />' % (i))
            else:
                typ = self.TYPES.get(type(a).__name__)
                if typ == 'bool':
                    a = str(a).lower()
                
                call.append('<%s order="%d" value="%s" />' % (typ, i, a))
        
        call.append('</%s>' % command)
        call = ''.join(call)
        
        print call
        
        self.send(call)
        
        x = ElementTree.XML(self.recv())
        if len(x) == 0 and 'error' in x.attrib:
            raise AdobeException(x.attrib['error'] and int(x.attrib['error']) or 'unknown')
        
        return x

class Fireworks(Client):
    
    def connect(self, port=12124):
        super(Fireworks, self).connect('127.0.0.1', port)

if __name__ == '__main__':
    import sys, os, os.path, urllib
    #inp, out = sys.argv[1:]
    #inp, out = os.path.abspath(inp), os.path.abspath(out)
    
    inp = os.path.abspath(sys.argv[1])
    
    dirs = os.listdir('/Volumes')
    dir = urllib.quote(dirs[0])
    
    c = Fireworks()
    c.connect()
    
    x = c.call('fw', 'runScript', 'file:///'+ dir + '/' + inp)
    print x

    