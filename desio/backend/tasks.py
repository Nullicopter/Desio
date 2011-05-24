
from celery.decorators import task, periodic_task
from celery.task.schedules import crontab, schedule

from desio.utils import binder, adobe
from datetime import datetime, timedelta

@periodic_task(run_every=schedule(timedelta(seconds=60)))
def export_fireworks():
    from pylons import config
    conf = config.get
    
    uname = conf('extractor.username')
    pw = conf('extractor.password')
    host = conf('extractor.host')
    port = conf('extractor.port')
    
    print uname, pw, host, port
    
    ext = binder.FireworksExtractor(uname, pw, host=host, port=port)
    ext.run()

@periodic_task(run_every=schedule(timedelta(seconds=120)))
def check_fireworks():
    
    pid = adobe.Fireworks.get_pid()
    if not pid:
        print 'Not running, restarting...'
        adobe.Fireworks.restart()
    else:
        fw = adobe.Fireworks()
        try:
            print 'Trying to connect...'
            fw.connect()
            fw.close()
            print 'OK'
        except adobe.AdobeException as e:
            print 'Fail. Killing FW'
            adobe.Fireworks.kill()

"""
# someday...
@task
def email(to, template_path, context=None, reply_to='', bcc='ogle.ben@gmail.com', **kw):
    from desio.utils import email as email_module
    email_module._send(to, template_path, context=context, reply_to=reply_to, bcc=bcc)
"""