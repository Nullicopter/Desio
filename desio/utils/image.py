
"""
## PSD convert with imagemagick:

convert somepsd.psd[0] out.psd

[0] is the indexed layer. It seems that index 0 is the combination of all visible layers.

## SVG to PNG

must install imagemagick with rsvg. You can check if it is using RSVG by running

convert -list format | grep SVG

output should look like:
    MSVG  SVG       rw+   ImageMagick's own SVG internal renderer
     SVG  SVG       rw+   Scalable Vector Graphics (RSVG 2.32.1)
    SVGZ  SVG       rw+   Compressed Scalable Vector Graphics (RSVG 2.32.1)

convert -depth 16 -background white -trim USA_Canada_time_zone_map.svg  tz.png

-trim will get rid of all extra space

## AI to PNG

uses ghostscript; can specify

-density ###

Default is 72dpi

convert -depth 16 -background white ai/vector_lemon.ai -trim +repage converted/lemon_ai.png

## EPS to PNG

uses ghostscript

-density ###

Default is 72dpi

convert -depth 16 -background white eps/headphones.eps -trim +repage converted/headphones_ai.png
"""

#import Image as PILImage
#import ImageChops

from magickwand.image import Image
from magickwand import api, wand
import tempfile, urllib, shutil
import os.path, re
from desio.utils import adobe, ignore_fireworks

EXTRACT_TYPE_THUMBNAIL = u'thumbnail'
EXTRACT_TYPE_FULL = u'full'
EXTRACT_TYPE_DIFF = u'diff'

PARSE_STATUS_PENDING = 'pending'
PARSE_STATUS_IN_PROGRESS = 'in_progress'
PARSE_STATUS_COMPLETED = 'completed'
PARSE_STATUS_FAILED = 'failed'

PARSE_TYPE_UNKNOWN = 'unknown'
PARSE_TYPE_IMAGEMAGICK = 'imagemagick'
PARSE_TYPE_FIREWORKS_OLD = 'fw_old'
PARSE_TYPE_FIREWORKS_CS3 = 'fw_cs3'
PARSE_TYPE_FIREWORKS_CS4 = 'fw_cs4'
PARSE_TYPE_FIREWORKS_CS5 = 'fw_cs5'

class ExtractedFile(object):
    def __init__(self, filename, type):
        self.extract_type = type
        self.filename = filename
    
    def __repr__(self):
        return 'ExtractedFile(%s, %s)' % (self.extract_type, self.filename)

class ExtractStatus:
    def __init__(self, status=PARSE_STATUS_COMPLETED, type=PARSE_TYPE_IMAGEMAGICK, file_type=None):
        self.status = status
        self.type = type
        self.file_type = file_type

class Extractor(object):
    
    src_format = 'Unknown'
    dest_format = 'PNG'
    
    def __init__(self, image, out_filename=None, filename=None):
        self.image = image
        self.out_filename = out_filename
        self.filename = filename
    
    @classmethod
    def _get_tmp_file(cls, type, out_filename=None, dest_format=None):
        if out_filename:
            ofn = out_filename
            ofn = os.path.join(os.path.dirname(ofn), type +'_'+ os.path.basename(ofn))
            f = open(ofn, 'wb')
            name = f.name
        else:
            f, name = tempfile.mkstemp('.'+(dest_format or cls.dest_format))
            
            #why is this returning an int on my machine? Supposed to be a file pointer.
            if isinstance(f, int):
                f = os.fdopen(f, 'wb')
        
        return f, name
    
    def resize_if_huge(self, max_size=(1200, 5000)):
        """
        resize_if_huge is destructive to the image object. It will resize the image file if over
        max_size. Do this after you have done anything you need to do at full size.
        """
        x, y = self.image.size
        sx, sy = max_size
        if x > sx or y > sy:
            dx = x - sx
            dy = y - sy
            ratio = (float(x)/float(y))
            
            sz = (x, y)
            if dx > dy:
                #x dim over further than y dim
                # size to x dim
                sz = (sx, int(float(sx)/ratio))
            else:
                #y dim over further than x dim
                # size to y dim
                sz = (int(float(sy)*ratio), sy)
                
            print 'HUGE; resizing from', (x,y), 'to', sz
            
            self.image.resize(sz, blur=1.0)
            
            return True
        
        return False
    
    def _write_file(self, type, max_size=(1200, 5000)):
        """
        """
        
        self.resize_if_huge(max_size)
        
        f, name = self._get_tmp_file(type, self.out_filename)
        
        f.write(self.image.dump(self.dest_format))
        f.close()
        
        return ExtractedFile(name, type)
    
    def thumbnail(self, size=(400,300)):
        """
        Thumbnail is destructive to the image object. It will resize the image file.
        Do this after you have done anything you need to do at full size.
        
        Pretty smart thumbnailer. It will create an image that is cropped in the center
        with size 'size' as a max. It will scale the least amount it can, and it blurs a bit
        to make even really small text look pretty nice.
        """
        x, y = self.image.size
        sx, sy = size
        dx = x - sx
        dy = y - sy
        ratio = (float(x)/float(y))
        
        sz = (x, y)
        if dx > 0 and dy > 0:
            ratioy = float(sx)/ratio
            ratiox = float(sy)*ratio
            if ratioy >= sy:
                sz = (sx, int(ratioy))
            else:
                sz = (int(ratiox), sy)
            self.image.resize(sz, blur=1.0)
        
        dx = sz[0] - sx
        dy = sz[1] - sy
        
        cropsize = (min(x, sx), min(y, sy))
        offset = (dx >= 0 and dx/2 or 0, 0)
        
        self.image.crop(cropsize, offset)
        return [self._write_file(EXTRACT_TYPE_THUMBNAIL)]
    
    def extract(self, **kw):
        """
        Will return a list of all extracted files
        """
        s = ExtractStatus(file_type=self.image.format)
        return [self._write_file(EXTRACT_TYPE_FULL)] + self.thumbnail(), s
    
    @classmethod
    def difference(cls, prev_image, current_image):
        """
        params are filenames
        """
        print 'diffing', prev_image, current_image
        
        f, name = cls._get_tmp_file(EXTRACT_TYPE_DIFF)
        
        print 'Saving diff to', name
        
        """
        # PIL -- This complains that some pairs of images 'do not match' Even when
        # they are generated from the same PSD and are the same pixel size. WTF.
        # USING IMAGEMAGICK INSTEAD, BITCHES
        p = PILImage.open(prev_image)
        c = PILImage.open(current_image)
        
        diff = ImageChops.difference(c, p)
        
        diff.save(f, cls.dest_format) #TODO catch IOError and do something with it.
        f.close()
        
        del p
        del c
        del diff
        """
        
        image = Image(current_image)
        other = Image(prev_image)
        
        isize = image.size
        osize = other.size
        
        offset = (0,0)
        if isize != osize:
            #enabling this makes the diff always the same size as the largest one
            #disabling makes it the size of the most current one. Hopefully this doesnt
            #happen very often...
            if False:#isize < osize: #basically, if both x and y components are less
                #swap; image is always the larger one
                tmp = image
                image = other
                other = tmp
                
                tmp = isize
                isize = osize
                osize = tmp
            
            offset = ((isize[0] - osize[0])/2, (isize[1] - osize[1])/2)
        
        image.composite(other, offset, operator=wand.DIFFERENCE_COMPOSITE_OP)
        
        f.write(image.dump(cls.dest_format))
        f.close()
        
        image.destroy()
        other.destroy()
        
        return ExtractedFile(name, EXTRACT_TYPE_DIFF)

class GenericExtractor(Extractor):
    """
    This is for basic files like gif, jpg, etc. It will just thumbnail the images.
    """
    def __init__(self, image, out_filename=None, filename=None):
        super(GenericExtractor, self).__init__(image, out_filename, filename)
        
        self.image = image
        self.src_format = image.format

class SVGExtractor(Extractor):
    
    src_format = 'SVG'
    
    def extract(self, density=None, **kw):
        """
        Will return a list of all extracted files
        """
        #print 'orig', self.image.size
        #self.image.trim()
        #print 'post trim', self.image.size
        
        s = ExtractStatus(file_type=self.image.format)
        
        if density:
            self.image.resolution = (density, density)
            #print 'density change', self.image.size
        
        return [self._write_file(EXTRACT_TYPE_FULL)] + self.thumbnail(), s

class PostscriptExtractor(Extractor):
    """
    Postscript is used for all ps, eps, ai, and PDF files. Under the hood, it is using
    ghostscript.
    """
    
    #all as PS or PDF type from imageMagick
    src_format = 'PS'
    
    def extract(self, density=None, **kw):
        """
        Will return a list of all extracted files
        """
        #print 'orig', self.image.size
        #self.image.trim()
        #print 'post trim', self.image.size
        
        s = ExtractStatus(file_type=self.image.format)
        
        if density:
            self.image.resolution = (density, density)
            #print 'density change', self.image.size
        
        self.image.iterator_reset()
        
        images = []
        while self.image.iterator_next():
            images.append(self._write_file(EXTRACT_TYPE_FULL))
        
        self.image.iterator_reset()
        
        return images + self.thumbnail(), s

class PSDExtractor(Extractor):
    """
    """
    
    src_format = 'PSD'
    
    def extract(self, density=None, **kw):
        """
        Will return a list of all extracted files
        """
        s = ExtractStatus(file_type=self.image.format)
        return [self._write_file(EXTRACT_TYPE_FULL)] + self.thumbnail(), s

class PNGExtractor(Extractor):
    """
    This will be more complicated with the fireworks extraction.
    """
    
    src_format = 'PNG'
    
    def extract(self, density=None, **kw):
        """
        Will return a list of all extracted files
        """
        s = ExtractStatus(file_type=self.image.format)
        return [self._write_file(EXTRACT_TYPE_FULL)] + self.thumbnail(), s

class FWPNGExtractor(Extractor):
    
    src_format = 'Unknown'
    dest_format = 'PNG'
    
    @classmethod
    def read_head(cls, filename):
        d = ''
        f = None
        try:
            f = open(filename, 'rb')
            d = f.read(500)
        finally:
            if f: f.close()
        return d
    
    @classmethod
    def read_parse_type(cls, filename):
        head = cls.read_head(filename)
        if 'Fireworks CS5' in head: return PARSE_TYPE_FIREWORKS_CS5
        elif 'Fireworks CS4' in head: return PARSE_TYPE_FIREWORKS_CS4
        elif 'Fireworks CS3' in head: return PARSE_TYPE_FIREWORKS_CS3
        elif 'Fireworks' in head: return PARSE_TYPE_FIREWORKS_OLD
        return PARSE_TYPE_UNKNOWN
    
    @classmethod
    def preprocess(cls, filename):
        
        head = cls.read_head(filename)
        
        isit = 'Fireworks' in head
        
        return isit
    
    def async_extract(self, **kw):
        
        parse_type = self.read_parse_type(self.filename)
        
        #this will parse with the simple png parser
        files, _ = extract(self.filename, self.out_filename, preprocess=False, **kw)
        
        # let the external process know this needs to be parsed
        return files, ExtractStatus(PARSE_STATUS_PENDING, type=parse_type, file_type='FWPNG')
        
    def extract(self, async_extract=None, **kw):
        """
        Will return a list of all extracted files
        """
        if async_extract == True or (async_extract == None and ignore_fireworks()):
            return self.async_extract(**kw)
        
        parse_type = self.read_parse_type(self.filename)
        
        import os, os.path
        from mako.template import Template
        from mako.runtime import Context
        from StringIO import StringIO
        
        vol = urllib.quote(os.listdir('/Volumes')[0])
        prefix = 'file:///'+ vol
        
        temp_dir = tempfile.mkdtemp()
        eid = 'FILE'
        
        data = {
            'in_file': prefix + os.path.abspath(self.filename),
            'out_dir': prefix + temp_dir + '/',
            'eid': eid
        }
        
        #script template
        here = os.path.dirname(os.path.dirname(__file__))
        script = os.path.join(here, 'backend', 'fireworks_export.js')
        mytemplate = Template(filename=script)
        buf = StringIO()
        ctx = Context(buf, **data)
        mytemplate.render_context(ctx)
        val = buf.getvalue()
        
        script, scname = self._get_tmp_file(None, dest_format='js')
        script.write(val)
        script.close()
        
        c = adobe.Fireworks()
        c.connect()
        
        error = None
        special_script = prefix + scname
        try:
            x = c.call('fw', 'runScript', special_script)
        except adobe.AdobeException as e:
            error = e
            if e.code != adobe.ERROR_DIED:
                raise
            print 'Fireworks died. But we kind of dont care. ON WITH IT, BITCHES.'
        
        os.remove(scname)
        
        regex = re.compile('FILE([0-9]+)')
        def key(s):
            m = regex.search(s)
            if m:
                return int(m.group(1))
            return None
        
        #now there should be files.
        files = os.listdir(temp_dir)
        files.sort(key=key)
        files = [ExtractedFile(os.path.join(temp_dir, f), EXTRACT_TYPE_FULL) for f in files if key(f) != None]
        
        if files:
            self.image = Image(files[0].filename)
            files += self.thumbnail()
            self.image.destroy()
        elif error:
            raise error #ok, maybe it legitimately died.
        
        return files, ExtractStatus(type=parse_type, file_type='FWPNG')

EXTRACTORS = {
    'PSD': PSDExtractor,
    'PDF': PostscriptExtractor,
    'PS': PostscriptExtractor,
    'SVG': SVGExtractor,
    'PNG': PNGExtractor,
    'GIF': GenericExtractor,
    'JPEG': GenericExtractor,
}

PREPROCESSORS = [
    FWPNGExtractor
]

def extract(filename, out_filename=None, preprocess=True, **kw):
    """
    :param filename: the input filename
    :param out_filename: output filename. if blank, will use temp files.
    """
    img = None
    extractor_class = None
    
    # some files need to have their contents checked before we can know whether or not we can
    # parse them. Preprocessing does that.
    if preprocess:
        for pp in PREPROCESSORS:
            if pp.preprocess(filename):
                extractor_class = pp
                break
    
    if not extractor_class:
        try:
            img = Image(filename)
        except:
            import sys
            print sys.exc_info()
            raise
        
        extractor_class = EXTRACTORS.get(img.format)
    
    if extractor_class:
        extractor = extractor_class(img, out_filename, filename)
        ext = extractor.extract(**kw)
        if img and hasattr(img, 'destroy'): img.destroy()
        return ext
    
    if img and hasattr(img, 'destroy'): img.destroy()
    raise Exception('Wrong format: %s' % img.format)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-a", "--action", dest="action",
                      help="Run an action", default='extract')
    
    (options, args) = parser.parse_args()
    
    if not args:
        parser.error('Enter a filename or two')
    
    if options.action == 'extract':
        extract(args[0], args[1:] and args[1:][0] or None)
    
    if options.action == 'diff':
        if len(args) < 2:
            parser.error('Enter a previous and a current filename to diff')
        
        print Extractor.difference(args[0], args[1])
        