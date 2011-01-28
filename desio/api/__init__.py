from desio.lib.base import h, logger
from desio.model import Session, users, projects, STATUS_APPROVED
from desio.model.users import ROLE_ADMIN, ROLE_USER
import sqlalchemy as sa
from pylons.controllers.util import abort

from desio.lib import auth

from pylons_common.lib.utils import objectify
from pylons_common.lib.date import convert_date
from pylons_common.lib.exceptions import *
from pylons_common.web.validation import validate
from pylons_common.lib.decorators import enforce as base_enforce, zipargs, stackable

import formencode.validators as fv

"""
    @enforce MUST be specified before @auth on your api functions. @enforce will convert strings to
    proper DB objects when coming in from the web service. @auth relies on there being proper DB
    objects to do must_own authorization.
"""

def enforce(**types):
    """
    Assumes all arguments are unicode strings, and converts or resolves them to more complex objects.
    If a type of the form [Type] is specified, the arguments will be interpreted as a comma-delimited
    list of strings that will be converted to a list of complex objects. 
    """
    
    # put any defaults here...
    types.setdefault('user', users.User)
    types.setdefault('real_user', users.User)
    types.setdefault('organization', users.Organization)
    types.setdefault('project', projects.Project)
    
    return base_enforce(Session, **types)
    
def authorize(*filters):
    
    """
    Authorization checking. Pass in objects that have a check() method. In your check method
    you can raise client exceptions.
    """
    @stackable
    def decorator(fn):
        
        @zipargs(fn)
        def new(**kwargs):
            
            # find the user
            real_user = kwargs.get('real_user')
            user = kwargs.get('user')
            if user is None:
                try:
                    real_user = auth.get_real_user()
                    user = auth.get_user()
                except TypeError, e:
                    real_user = None
                    user = None
            
            dargs = dict([i for i in kwargs.items()])
            dargs['real_user'] = real_user
            dargs['user'] = user
            
            #get rid of self from the decorated object
            if 'self' in dargs:
                del dargs['self']
                
            for filter in filters:
                filter.check(**dargs)
            
            
            return fn(**kwargs)
            
        return new
    return decorator

class IsNotLoggedIn(object):
    
    def check(self, real_user, user, **kwargs):
        if real_user or user:
            raise ClientException("You cannot be logged in.", INCOMPLETE, field='user')
        return True

class IsLoggedIn(object):
    
    def check(self, real_user, user, **kwargs):
        if not real_user:
            raise ClientException("Please Login!", INCOMPLETE, field='user')
        return True

class IsAdmin(IsLoggedIn):
    
    def check(self, real_user, user, **kwargs):
        super(IsAdmin, self).check(real_user, user, **kwargs)
        
        if not real_user.is_admin():
            raise ClientException("User must be an admin", FORBIDDEN)
        
        return True

class HasRole(IsLoggedIn):
    
    def __init__(self, *roles):
        self.roles = roles
    
    def check(self, real_user, user, **kwargs):
        super(HasRole, self).check(real_user, user, **kwargs)
        
        if real_user.role not in self.roles:
            raise ClientException("User must be in role %s" % self.roles, FORBIDDEN)
        
        return True

ORGANIZATION_ROLE_ADMIN = ROLE_ADMIN
ORGANIZATION_ROLE_CREATOR = 'creator'
ORGANIZATION_ROLE_USER = ROLE_USER

class HasRole(IsLoggedIn):
    def __init__(self, roles, param=None):
        self.param = param
        self.roles = roles
    
    def check(self, real_user, user, **kwargs):
        super(HasRole, self).check(real_user, user, **kwargs)
        
        #assume admins are not special. They can pretend and get the user's behaviors
        #otherwise we could short circuit here with a check to is admin
        obj = kwargs.get(self.param)
        if not obj:
            raise ClientException('No %s specified' % (self.param), NOT_FOUND, field=self.param)
        
        role = obj.get_role(user, status=STATUS_APPROVED)
        
        if not role or role not in self.roles:
            raise ClientException('CANNOT(!)', FORBIDDEN, field=self.param)
        
        return True

class CanReadOrg(HasRole):
    """
    They can read all the projects they have access to. They can see org activity, etc.
    """
    def __init__(self, param='organization'):
        super(CanReadOrg, self).__init__(
            [users.ORGANIZATION_ROLE_USER, users.ORGANIZATION_ROLE_CREATOR, users.ORGANIZATION_ROLE_ADMIN],
            param=param)
    
    def check(self, real_user, user, **kwargs):
        if real_user.is_admin(): return True
        
        return super(CanReadOrg, self).check(real_user, user, **kwargs)

class CanContributeToOrg(HasRole):
    """
    They can create and modify projects and membership in projects.
    """
    def __init__(self, param='organization'):
        super(CanContributeToOrg, self).__init__(
            [users.ORGANIZATION_ROLE_ADMIN, users.ORGANIZATION_ROLE_CREATOR],
            param=param)

class CanAdminOrg(HasRole):
    """
    They are an organization admin. They can edit CC information, organization membership, they
    can read/write all projects.
    """
    def __init__(self, param='organization'):
        super(CanAdminOrg, self).__init__([users.ORGANIZATION_ROLE_ADMIN], param=param)

##
### Project auth decorators
##

class CanReadProject(HasRole):
    """
    They can read all the projects they have access to. They can see org activity, etc.
    """
    def __init__(self, param='project'):
        super(CanReadProject, self).__init__(
            [projects.PROJECT_ROLE_READ, projects.PROJECT_ROLE_WRITE, projects.PROJECT_ROLE_ADMIN],
            param=param)
    
    def check(self, real_user, user, **kwargs):
        if real_user.is_admin(): return True
        
        return super(CanReadProject, self).check(real_user, user, **kwargs)

class CanWriteProject(HasRole):
    """
    They can create and modify projects and membership in projects.
    """
    def __init__(self, param='project'):
        super(CanWriteProject, self).__init__(
            [projects.PROJECT_ROLE_WRITE, projects.PROJECT_ROLE_ADMIN],
            param=param)

class CanAdminProject(HasRole):
    """
    They are an organization admin. They can edit CC information, organization membership, they
    can read/write all projects.
    """
    def __init__(self, param='project'):
        super(CanAdminProject, self).__init__([projects.PROJECT_ROLE_ADMIN], param=param)

class MustOwn(IsLoggedIn):
    
    def __init__(self, *params):
        self.params = params
    
    def check(self, real_user, user, **kwargs):
        super(MustOwn, self).check(real_user, user, **kwargs)
        
        # user.must_own takes a list of objects. This allows the user to pass in a single
        # param name, or multiple names.
        mo = self.params
        
        #pull the objects that correspond to the param names from the function's args.
        mo_obj_list = []
        for var in mo:
            if var not in kwargs:
                raise ClientException("Parameter '%s' not found in function arguments." % (var), NOT_FOUND, field=var)
            mo_obj_list.append(kwargs[var])
        
        real_user.must_own(*mo_obj_list)
        return True

class MustOwnIfPresent(IsLoggedIn):
    
    def __init__(self, *params):
        self.params = params
    
    def check(self, real_user, user, **kwargs):
        super(MustOwnIfPresent, self).check(real_user, user, **kwargs)
        # user.must_own takes a list of objects. This allows the user to pass in a single
        # param name, or multiple names.
        mo = self.params
        
        #pull the objects that correspond to the param names from the function's args.
        mo_obj_list = []
        for var in mo:
            if var in kwargs and kwargs[var] != None:
                mo_obj_list.append(kwargs[var])
        
        if mo_obj_list:
            real_user.must_own(*mo_obj_list)
        
        return True

class ConvertDate(fv.FancyValidator):
    def _to_python(self, value, state):
        
        try:
            value = convert_date(value)
        except (ValueError,), e:
            raise fv.Invalid(e.args[0], value, state)
        
        return value

class FieldEditor(object):
    """
    The edit functions for a given object are big and tend to be error prone.
    This class allows you to just specify a validator class, the params you want
    to edit, and some functions to edit those params.
    
    This class will handle editing of one variable at a time, it will catch and
    package up multiple errors, and it will do general authorization.
    
    You just extend it and add your edit functions with name edit_<param_name>
    Then you instantiate and call edit(). Example function:
    
    def edit_budget(real_user, user, campaign, key, value):
        raise exceptions.ClientException('OMG bad shit is happening!', field=key)
    
    'key' would be 'budget'
    
    Notes:
    
    * If the user is not an admin and he tries ot edit an admin field, the editor
      will just ignore the field as if he had not specified it.
    * Your editing can work one param at a time.
      so /api/v1/campaign/edit?name=my+name
      /api/v1/campaign/edit?key=name&value=my+name are equivalent
    * Your field editing functions can be passed None
      so /api/v1/campaign/edit?cpc= would unset the CPC.
      If you dont want to accept None, check for it in your edit_ function, not
      in the validator.
    * You must do object ownership authorization outside of this editor. The only
      auth this thing does is an admin check for the editing of admin fields.
      Use the @auth(must_own='asd') on your edit api function.
    * Your edit_ functions can raise ClientExceptions. They will be packaged up in
      a CompoundException and be returned to the client side as a collection.
      If you raise an AdrollException, it will get through to the error middleware.
    """
    
    def __init__(self, fields, admin_fields, validator):
        self.validator = validator
        self.fields = fields
        self.admin_fields = admin_fields
    
    def _edit_generic(self, name, obj, key, param, can_be_none=False):
        if not can_be_none and param == None:
            raise exceptions.ClientException('Please enter a %s' % name, field=key)
        
        old = getattr(obj, key)
        setattr(obj, key, param)
        self.log(name, key, old, getattr(obj, key))
    
    def log(self, field, key, old_val, new_val):
        logger.info('%s edited by %s: %s (%s) = %s from %s' % (self.object, self.real_user, field, key, new_val, old_val))
    
    def edit(self, real_user, user, obj, key=None, value=None, **kwargs):
        
        self.real_user = real_user
        self.user = user
        self.object = obj
        self.params = kwargs
        
        # for the single field edit
        if key and value != None and key not in kwargs:
            kwargs[key] = value
        
        # There is no authorization check in here. This is effectively it.
        # If the user is not an admin, the admin fields are stripped out. 
        editable_keys = set(real_user.is_admin() and (self.fields + self.admin_fields) or self.fields)
        
        # is there anything we can edit?
        to_edit = [k for k in kwargs.keys() if k in editable_keys]
        if not to_edit:
            raise ClientException('Specify some parameters to edit, please.', code=INCOMPLETE)
        
        # we fill out the kwargs so we dont piss off the validator. hack. poo. Must have all
        # fields as the validator will too.
        for k in self.fields + self.admin_fields:
            if k not in kwargs or k not in editable_keys:
                kwargs[k] = None
        
        params = validate(self.validator, **kwargs)
        
        #this is for collecting errors. 
        error = CompoundException('Editing issues!', code=FAIL)
        
        # only go through the keys that we got in the original call/request (to_edit)
        for k in to_edit:
            if k not in editable_keys: continue
            param = params[k]
            
            fn_name = 'edit_%s' % k
            if hasattr(self, fn_name):
                
                try:
                    results = getattr(self, fn_name)(real_user, user, obj, k, param)
                except ClientException, e:
                    # if error from editing, we will package it up so as to
                    # return all errors at once
                    error.add(e)
            else:
                #this is an adroll exception cause it should bubble up to a WebApp email
                raise AppException('Cannot find %s edit function! :(' % fn_name, code=INCOMPLETE)
        
        if error.has_exceptions:
            raise error
        
        Session.flush()
        
        return True

import user
import organization
import project
import error
