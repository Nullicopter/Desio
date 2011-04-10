#!/usr/bin/env python
import getopt, sys
from paste.deploy import appconfig
from migrate.versioning.shell import main

def get_db_url_from_ini():
    """
    read the database url from a pylons ini
    """
    argv = list(sys.argv)
    if len(argv) > 1:
        last_arg = argv[-1]
        if last_arg.endswith(".ini"):
            ini_file = last_arg
            app_config = appconfig("config:%s" % (ini_file,), relative_to="../..")
            return app_config.local_conf["sqlalchemy.default.url"]
            
if __name__ == "__main__":
    # parse command line options
    # usage: manage.py 
    kw = dict(repository = 'migrations')
    url = get_db_url_from_ini()
    if url:
        kw['argv'] = sys.argv[1:-1]
        kw['url'] = url

    main(**kw)
    
