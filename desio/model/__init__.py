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

APP_ROLE_ADMIN = 'admin'
APP_ROLE_WRITE = 'write'
APP_ROLE_READ = 'read'

APP_ROLES = [APP_ROLE_ADMIN, APP_ROLE_WRITE, APP_ROLE_READ]

APP_ROLE_INDEX = {
    APP_ROLE_ADMIN: 3,
    APP_ROLE_WRITE: 2,
    APP_ROLE_READ: 1,
    None: 0
}

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


class Roleable(object):
    """
    This is a base class for all the objects that have roles
    """
    
    ##
    ### User connection stuff
    
    connection_class = None # EntityUser, ProjectUser, etc...
    object_name = None # 'project', 'entity', etc...
    
    @property
    def object_id_name(self):
        return (self.object_name+'_id')
        
    def get_role(self, user, status=STATUS_APPROVED):
        """
        OVERRIDE THIS.
        """
        return None
    
    def set_role(self, user, role):
        """
        Sets a role on an existing user.
        """
        uc = self.get_user_connection(user)
        if uc:
            uc.role = role
            return True
        return False
    
    def get_user_connection(self, user, status=STATUS_APPROVED):
        """
        Find a single user's membership within this org
        """
        q = Session.query(self.connection_class).filter(self.connection_class.user_id==user.id)
        if status:
            q = q.filter(self.connection_class.status==status)
        return q.filter(getattr(self.connection_class, self.object_id_name)==self.id).first()
    
    def get_user_connections(self, status=None):
        """
        Get all memberships in this org.
        """
        q = Session.query(self.connection_class).filter(getattr(self.connection_class, self.object_id_name)==self.id)
        if status and isinstance(status, basestring):
            q = q.filter(self.connection_class.status==status)
        if status and isinstance(status, (list, tuple)):
            q = q.filter(self.connection_class.status.in_(status))
        return q.all()
    
    def set_user_status(self, user, status):
        # could check pending?
        cu = self.get_user_connection(user)
        if not cu:
            return False
        
        cu.status = status
        return cu
    
    def approve_user(self, user):
        return self.set_user_status(user, STATUS_APPROVED)
    
    def reject_user(self, user):
        return self.set_user_status(user, STATUS_REJECTED)
    
    def attach_user(self, user, role=APP_ROLE_READ, status=STATUS_APPROVED):
        cu = Session.query(self.connection_class) \
                    .filter(getattr(self.connection_class, self.object_name)==self) \
                    .filter(self.connection_class.user==user).first()
        if cu:
            cu.role = role
            cu.status = status
            return cu
        
        cu = self.connection_class(user=user, role=role, status=status)
        setattr(cu, self.object_name, self) 
        Session.add(cu)
        return cu
    
    def remove_user(self, user):
        q = Session.query(self.connection_class).filter(getattr(self.connection_class, self.object_id_name)==self.id)
        q = q.filter(self.connection_class.user_id==user.id)
        cu = q.first()
        if cu:
            Session.delete(cu)
            return True
        return False