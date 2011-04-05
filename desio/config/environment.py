"""Pylons environment configuration"""
import os, atexit
import pylons, turbomail

from mako.lookup import TemplateLookup
from pylons.configuration import PylonsConfig
from pylons.error import handle_mako_error
from sqlalchemy import engine_from_config
from paste.deploy.converters import asbool

import desio.lib.app_globals as app_globals
import desio.lib.helpers
from desio.config.routing import make_map
from desio.model import init_model
from desio.utils import fs

from pylons_common.sqlalchemy.proxy import TimerProxy

def setup_turbomail(config):
    from turbomail.control import interface
    
    cmap = {
        'smtp_server': 'mail.smtp.server',
        'smtp_username': 'mail.smtp.username',
        'smtp_password': 'mail.smtp.password',
        'smtp_use_tls': 'mail.smtp.tls'
    }
    
    boolkeys = (
        'mail.smtp.tls',
        'mail.tls',
        'mail.smtp.debug',
        'mail.debug'
    )
    
    for k, v in config.items():
        if k in cmap and cmap[k] not in config:
            config[cmap[k]] = v
    
    for k, v in config.items():
        if k.endswith('.on') or (k in boolkeys):
            config[k] = asbool(v)
    
    if config.get('mail.on'):
        interface.start(config)

@atexit.register
def teardown_turbomail():
    from turbomail.control import interface
    interface.stop()

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    config = PylonsConfig()
    
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='desio', paths=paths)

    config['routes.map'] = make_map(config)
    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.h'] = desio.lib.helpers
    config['pylons.strict_tmpl_context'] = False
    
    config['beaker.session.cookie_expires'] = None
    
    # Setup cache object as early as possible
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)
    

    # Create the Mako TemplateLookup, with the default auto-escaping
    config['pylons.app_globals'].mako_lookup = TemplateLookup(
        directories=paths['templates'],
        error_handler=handle_mako_error,
        module_directory=os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding='utf-8', default_filters=['escape'],
        imports=['from webhelpers.html import escape'])

    # Setup the SQLAlchemy database engine
    config['pylons.app_globals'].sa_default_engine = engine_from_config(config, 'sqlalchemy.default.', proxy=TimerProxy())
    init_model(config['pylons.app_globals'].sa_default_engine)
    
    config['pylons.errorware']['smtp_username'] = config.get('smtp_username')
    config['pylons.errorware']['smtp_password'] = config.get('smtp_password')
    config['pylons.errorware']['smtp_use_tls'] = config.get('smtp_use_tls')
    config['pylons.errorware']['smtp_port'] = config.get('smtp_port')
    
    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    fs.setup_directories(config)
    setup_turbomail(config)
    
    return config
