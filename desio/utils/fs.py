import os

def setup_directories(config):
    for config_key in ['files_storage']:
        if os.path.exists(config[config_key]):
            continue
        
        os.makedirs(config['files_storage'])