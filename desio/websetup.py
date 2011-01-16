"""Setup the desio application"""
import logging

import pylons
import pylons.test

from desio.config.environment import load_environment
from desio.model.meta import Session, Base
from desio.model.users import User, UserPreference, Organization, OrganizationUser
from desio.model import projects

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup desio here"""
    # Don't reload the app if it was loaded under the testing environment
    #if not pylons.test.pylonsapp:
    config = load_environment(conf.global_conf, conf.local_conf)
    
    engine = config['pylons.app_globals'].sa_default_engine
    
    #effin config garbage
    pylons.config._push_object(config)
    #init_model(engine)
    
    # Create the tables if they don't already exist
    Base.metadata.create_all(bind=engine)
