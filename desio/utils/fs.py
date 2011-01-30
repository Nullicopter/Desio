import os
import urlparse

def setup_directories(config):
    for config_key in ['files_storage']:
        path_url = config[config_key]
        path = urlparse.urlsplit(path_url).path
        if os.path.exists(path):
            continue
        
        os.makedirs(path)
