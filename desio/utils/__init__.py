
import os.path
from collections import defaultdict as dd
from paste.deploy.converters import asbool
import pylons
from datetime import datetime

def load_config(ini_file, log_from_ini=False, do_logging=True):
    from paste.deploy import appconfig
    from desio.config.environment import load_environment

    ini_file = os.path.abspath(ini_file)
    # load config / pylons environment
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

def pluralize(num, if_many, if_one, if_zero=None):
    """
    returns the proper string based on the number passed.
    
    s = pluralize(1, "sites", "site")
    
    s would be 'site'
    """
    text = if_many
    
    if num == 0 and if_zero:
        text = if_zero
    elif num == 1:
        text = if_one
        
    return text.replace(u'{0}', unicode(num))

def relative_date(date, now=None):
    """
    could accept a timezone...
    """
    now = now or datetime.utcnow()
    
    td = (date - now)
    total_seconds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
    
    ret = {}
    ret['mstotal'] = int(total_seconds * 1000.0)
    ret['ispast'] = ret['mstotal'] < 0
    ret['mstotal'] = abs(ret['mstotal'])
    
    ret['ms'] = ret['mstotal'] % 1000
    ret['sectotal'] = int(ret['mstotal']/1000)
    ret['sec'] = ret['sectotal'] % 60
    ret['mintotal'] = int(ret['sectotal']/60)
    ret['min'] = ret['mintotal'] % 60
    ret['hourstotal'] = int(ret['mintotal']/60)
    ret['hours'] = ret['hourstotal'] % 24
    ret['daystotal'] = int(ret['hourstotal']/24)
    
    return ret

def relative_date_str(date, now=None):
    """
    could accept a timezone...
    """
    now = now or datetime.utcnow()
    
    if not date: return 'unknown'
    
    data = relative_date(date, now)
    
    if data['sectotal'] < 10 and data['ispast']: return 'Just now'
    
    if data['daystotal'] > 7: return date.strftime("%b %d, %Y")
    
    def modret(str):
        if data['ispast']:
            return str + ' ago'
        return 'in ' + str
    
    if data['daystotal'] == 1 and data['ispast']:
        return 'Yesterday'
    if data['daystotal'] == 1 and not data['ispast']:
        return 'Tomorrow'
    
    if data['daystotal'] > 0:
        return modret(pluralize(data['daystotal'], '{0} days', '{0} day'))
    
    if data['hourstotal']:
        return modret(pluralize(data['hourstotal'], '{0} hours', '{0} hour'))
    
    if data['mintotal']:
        return modret(pluralize(data['mintotal'], '{0} minutes', '{0} minute'))
    
    if data['sectotal']:
        return modret(pluralize(data['sectotal'], '{0} seconds', '{0} second'))
    
    if data['mstotal']:
        return modret(pluralize(data['mstotal'], '{0} millis', 'now!'))
    
    return date.strftime("%b %d, %Y")

def file_size(bytes, decimals=0):
    
    # Bytes is an integer
    k = 1024
    
    labels = [' bytes', 'KB', 'MB', 'GB', 'TB', 'OMFGs', 'WTFOMFGs']
    i = 0
    cur = bytes
    
    while cur >= k:
        cur /= k
        i+=1
    
    s = '%.'+str(decimals)+'f'
    return (s % (cur,)) + '' + labels[i]

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

_is_production = None
def is_production():
    """
    are we currently in test mode?
    """
    global _is_production

    if _is_production is None:
        # cache value
        _is_production = asbool(pylons.config.get('is_production', 'false'))

    return _is_production