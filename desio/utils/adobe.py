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

import socket, subprocess, time, os, signal
from xml.etree import ElementTree

ERROR_DIED = 1
ERROR_CANTCONNECT = 2
PATH = '/Applications/Adobe Fireworks CS5/Adobe Fireworks CS5.app/'
RESTART = ['open', PATH]

class AdobeException(Exception):
    def __init__(self, code, message=None):
        self.code = code
        self.message = message
    def __repr__(self):
        return 'AdobeException(%s, %s)' % (self.code, self.message)

class Client(object):
    
    TYPES = {
        'str': 'string',
        'int': 'int',
        'unicode': 'string',
        'float': 'double',
        'bool': 'bool'
    }
    
    def __init__(self):
        self._con_params = None
        self._sock = None
        self._create()
    
    def _create(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self, host, port=12124):
        self._con_params = (host, port)
        try:
            self._sock.connect(self._con_params)
        except socket.error as e:
            raise AdobeException(ERROR_CANTCONNECT, "Cannot connect :(")
    
    def close(self):
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            del self._sock
            self._sock = None
        except socket.error as e:
            pass
    
    def reconnect(self):
        print 'attempting to reconnect...'
        if self._con_params:
            print 'reconnecting with %s' % (self._con_params,)
            self.close()
            self.connect(*self._con_params)
    
    def send(self, payload):
        
        if ord(payload[-1]) != 0:
            payload = payload+'\0'
        
        return self._sock.send(payload)
    
    def recv(self):
        
        res = []
        r = self._sock.recv(1)
        while True:
            if not r:
                raise AdobeException(ERROR_DIED, "Fireworks probably died.")
                #self.reconnect()
                #return None
            if not ord(r): break
            
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
    
    PROCESS = 'Fireworks'
    
    def connect(self, host='127.0.0.1', port=12124):
        super(Fireworks, self).connect('127.0.0.1', port)
    
    @classmethod
    def get_pid(cls):
        for line in os.popen("ps xa"):
            fields = line.split()
            pid = fields[0]
            process = ' '.join(fields[4:])
            
            if process.find(cls.PROCESS) > 0:
                return int(pid)
        return None
    
    @classmethod
    def kill(cls):
        pid = cls.get_pid()
        if pid:
            os.kill(pid, signal.SIGKILL)
    
    @classmethod
    def restart(cls):
        cls.kill()
        subprocess.call(RESTART)
        time.sleep(5)
    
    def reconnect(self):
        self.close()
        subprocess.call(RESTART)
        time.sleep(5)
        self.kill()
        time.sleep(5)
        subprocess.call(RESTART)
        time.sleep(5)
        #super(Fireworks, self).reconnect()

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

    