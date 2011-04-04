import os
import urlparse

def setup_directories(config):
    def doit(config_key):
        path_url = config[config_key]
        path = urlparse.urlsplit(path_url).path
        if os.path.exists(path):
            return
        
        os.makedirs(path)
    
    url = urlparse.urlsplit(config['files_storage'])
    if url.scheme == 'file':
        doit('files_storage')
