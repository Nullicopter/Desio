
from desio.lib.base import BaseController, h, c, auth, abort, redirect
from desio.model import users, fixture_helpers as fh
class AdminController(BaseController):
    
    def __before__(self, *a, **kw):
        if not auth.is_admin():
            return redirect('/')
            #abort(404)