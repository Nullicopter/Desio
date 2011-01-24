from desio.lib.base import *
from desio.model import users
from desio.controllers.admin import AdminController

import formencode
import formencode.validators as fv

import sqlalchemy as sa

class SearchController(AdminController):
    
    def index(self):
        c.tab = 'Search'
        
        q = request.params.get('q')
        if q:
            c.query = q
            c.results = self._search(q)
        
        return self.render('/admin/search.html')
    
    def _search(self, query):
        if not query: return None
        
        ret = {}
        
        is_int = False
        try:
            query = int(query)
            is_int = True
        except: pass
        
        def filter(q, *args):
            if is_int:
                return q.filter_by(id=query)
            else:
                return q.filter(*args)
        
        like_query = '%'+ str(query).lower() +'%'
        
        #users
        q = Session.query(users.User)
        if is_int:
            q = q.filter_by(id=query)
        else:
            txt = query.split()
            for t in txt:
                word = '%'+t.strip().lower()+'%'
                q = q.filter(sa.or_(sa.func.lower(users.User.username).like(word), sa.func.lower(users.User.email).like(word),
                                    sa.func.lower(users.User.first_name).like(word), sa.func.lower(users.User.last_name).like(word)))
        q = q.order_by(sa.desc(users.User.is_active), sa.desc(users.User.id))
        ret['users'] = q.all()
        
        #orgs
        q = Session.query(users.Organization)
        if is_int:
            q = q.filter_by(id=query)
        else:
            txt = query.split()
            for t in txt:
                word = '%'+t.strip().lower()+'%'
                q = q.filter(sa.or_(sa.func.lower(users.Organization.name).like(word), sa.func.lower(users.Organization.subdomain).like(word)))
        q = q.order_by(sa.desc(users.Organization.is_active), sa.desc(users.Organization.id))
        ret['orgs'] = q.all()
        
        return ret