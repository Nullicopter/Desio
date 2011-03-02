
import os.path
from collections import defaultdict as dd
from paste.deploy.converters import asbool
import pylons

def load_config(ini_file, log_from_ini=False, do_logging=True):
    from paste.deploy import appconfig
    from desio.config.environment import load_environment

    ini_file = os.path.abspath(ini_file)
    # load config / pylons environment;
    # note: appconfig (as opposed to loadapp) doesn't load wsgi
    app_config = appconfig("config:%s" % (ini_file,))
    config = load_environment(app_config.global_conf, app_config.local_conf)
    from desio import model
    
    engine = config['pylons.app_globals'].sa_default_engine
    model.init_model(engine)
    pylons.config.push_process_config(config)

    if not do_logging:
        return

    if log_from_ini:
        try:
            # this fails because I want it to fail.
            logging.config.fileConfig(ini_file)
        except Exception, e:
            import traceback
            sys.stderr.write(traceback.format_exc())
        else:
            return

def to_unicode(s, encoding='utf-8'):
    """convert any value to unicode, except None"""
    if s is None:
        return None
    if isinstance(s, unicode):
        return s
    if isinstance(s, str):
        return s.decode(encoding, 'ignore')
    return unicode(s)

def find_short_description(words, cutoff=100):
    """Finds the first sentence in the glob of words."""
    if not words: return words
    
    if len(words) < cutoff: return words
    
    ret = []
    
    def append_tokens(input, output):
        count = 0
        for s in input:
            s = s.strip()
            if count + len(s) > cutoff: break
            output.append(s)
            count += len(s)
    
    sentences = words.split('.')
    append_tokens(sentences, ret)
    
    if ret:
        return ' '.join([s+'.' for s in sentences if s])
    else:
        w = words.split()
        append_tokens(w, ret)
        
        return ' '.join(ret)

_is_testing = None
def is_testing():
    """
    are we currently in test mode?
    """
    global _is_testing

    if _is_testing is None:
        # cache value
        _is_testing = asbool(pylons.config.get('is_testing', 'false'))

    return _is_testing