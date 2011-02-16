"""The application's model objects"""
import datetime
from desio.model.meta import Session, Base
from desio import utils

STATUS_APPROVED = u'approved'
STATUS_REJECTED = u'rejected'
STATUS_PENDING = u'pending'
STATUS_OPEN = u'open'
STATUS_COMPLETED = u'completed'
STATUS_INACTIVE = u'inactive'
STATUS_EXISTS = u'exists'
STATUS_REMOVED = u'removed'

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)
    
    from psycopg2 import extensions
    extensions.register_type(extensions.UNICODE)

def commit():
    """wrapper fn"""
    if utils.is_testing():
        Session.flush()
    else:
        Session.commit()

def flush():
    """Wrapper fn"""
    Session.flush()