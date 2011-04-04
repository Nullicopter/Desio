
"""
I didnt know where to put this. Move as you see fit. Will prolly have to change as
we move stuff like this into a real async task.

This will run the extract process for a given change and temp file.
"""

import sys, os.path, pylons, urllib
from desio.utils import image, load_config
from desio.model import Session, projects, commit

from collections import defaultdict as dd

def gen_diffs(prev_change, current_raw_extracts):
    """
    Diffs the current version's extracts with the previous versions extracts
    """
    if not prev_change or not current_raw_extracts:
        return []
    
    current_raw_extracts = [e for e in current_raw_extracts if e.extract_type == image.EXTRACT_TYPE_FULL]
    print 'current raw', current_raw_extracts
    
    prev_extracts = [e for e in prev_change.change_extracts if e.extract_type == image.EXTRACT_TYPE_FULL]
    prev_extracts.sort(key=lambda e: e.order_index)
    print 'prev', prev_extracts
    
    dler = urllib.URLopener()
    res = []
    for i in range(min(len(prev_extracts), len(current_raw_extracts))):
        url = prev_extracts[i].base_url + prev_extracts[i].url
        prev_fname, _ = dler.retrieve(url)
        cur_fname = current_raw_extracts[i].filename
        
        print 'diffing', i, url, 'with', cur_fname
        
        res.append(image.Extractor.difference(prev_fname, cur_fname))
    
    return res
    
    
def gen_extracts(change, tmp_filepath):
    """
    Will generate the file extracts for this change. The extracts include the thumbnail.
    
    :param change: is the change object.
    :param tmp_filepath: is the path to the original file
    """
    
    # find previous change
    previous = change.entity.get_change(version=change.version-1)
    
    extracts = []
    indices = dd(lambda: 0) #each type of file will have its own count
    raw_extracts = image.extract(tmp_filepath)
    raw_extracts += gen_diffs(previous, raw_extracts)
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
    path to file, the raw file (PSD, PDF, whatev...)
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