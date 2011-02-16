import os, sys
import urlparse
import shutil

class LocalUploader(object):
    """
    Move files to specified directories
    """
    def __init__(self, base_url):
        parsed = urlparse.urlsplit(base_url)
        self.base_path = parsed.path

    def set_contents(self, from_filepath, to_filepath):
        """
        Store the content from local_filepath in the local filesystem
        at self.path
        """
        final_filepath = os.path.join(self.base_path, to_filepath)
        final_directory, final_filename = os.path.split(final_filepath)
        try:
            os.makedirs(final_directory)
        except: 
            print sys.exc_info()
        
        shutil.move(from_filepath, final_filepath)

class S3Uploader(object):
    """
    Upload files to specified S3 locations
    """
    def __init__(self, base_url):
        parsed = urlparse.urlsplit(base_url)
        self.bucket = parsed.netloc.split(".", 1)[0]
        self.base_path = parsed.path
        self.s3 = object()

    def set_contents(self, local_filepath, remote_filepath):
        """
        Upload content to S3 in self.bucket at self.path
        """

