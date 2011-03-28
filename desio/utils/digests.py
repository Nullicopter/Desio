from hashlib import md5

def md5_file(filepath, chunk_size=2**20):
    hash = md5()
    with file(filepath, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            hash.update(data)
    return hash.hexdigest()
        
