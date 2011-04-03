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
            pass #print sys.exc_info()
        
        shutil.move(from_filepath, final_filepath)

class S3Uploader(object):
    """
    Upload files to specified S3 locations
    """
    s3 = None
    def __init__(self, base_url):
        parsed = urlparse.urlsplit(base_url)
        self.bucket = parsed.netloc.split(".", 1)[0]
        self.base_path = parsed.path

    def set_contents(self, local_filepath, remote_filepath):
        """
        Upload content to S3 in self.bucket at self.path
        """
        from boto.s3.connection import S3Connection
        from boto.s3.key import Key

        if self.s3 is None:
            self.aws_api_key = pylons.config['aws_api_key'].strip()
            self.aws_secret_key = pylons.config['aws_secret_key'].strip()
            self.bucket_name = pylons.config['aws_s3_bucket'].strip()
            self.s3 = S3Connection(aws_access_key_id=self.aws_api_key,
                                   aws_secret_access_key=self.aws_secret_key)
        bucket = self.s3.get_bucket(self.bucket_name)

        headers = {}
        headers['Content-Type'] = "application/octet-stream"

        if remote_filepath.startswith("/"):
            remote_filepath = remote_filepath[1:]
        k = Key(self.bucket)
        k.key = remote_filepath
        k.set_contents_from_filename(local_filepath, headers, replace=True)
        k.set_acl('public-read')
