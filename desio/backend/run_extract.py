
"""
I didnt know where to put this. Move as you see fit. Will prolly have to change as
we move stuff like this into a real async task.

This will run the extract process for a given change and temp file.
"""

import sys, os.path, pylons
from desio.utils import image, load_config
from desio.model import Session, projects, commit

from collections import defaultdict as dd

def gen_extracts(change, tmp_filepath):
    """
    Will generate the file extracts for this change. The extracts include the thumbnail.
    
    :param change: is the change object.
    :param tmp_filepath: is the path to the original file
    """
    
    extracts = []
    indices = dd(lambda: 0) #each type of file will have its own count
    raw_extracts = image.extract(tmp_filepath)
    for e in raw_extracts:
        
        change_extract = projects.ChangeExtract(change=change, extract_type=e.extract_type, order_index=indices[e.extract_type])
        change_extract.set_contents(e.filename)
        Session.add(change_extract)
        extracts.append(change_extract)
        
        indices[e.extract_type] += 1
    
    commit()
    return extracts

if __name__ == '__main__':
    """
    accept 2 params:
    eid of the change
    path to file
    """
    if len(sys.argv) != 4:
        print 'Usage: %s development.ini change_eid /path/to/tmp_file.blah' % sys.argv[0]
        exit(1)
    
    ini, eid, filepath = sys.argv[1:]
    
    load_config(os.path.abspath(ini))
    
    change = Session.query(projects.Change).filter_by(eid=eid).first()
    if not change:
        print 'Cannot find change %s' % eid
        exit(1)
    
    print gen_extracts(change, filepath)