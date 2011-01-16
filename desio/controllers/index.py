from desio.lib.base import *

class IndexController(BaseController):
    """
    """
    def index(self, **k):
        return self.render('/index/index.html')

