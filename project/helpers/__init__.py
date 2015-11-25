import hashlib
import os
import os.path

def get_sha512(filename):
    hash_func = hashlib.sha512();
    with open(filename) as handle:
        for chunk in iter(lambda: handle.read(128 * hash_func.block_size), b''):
            hash_func.update(chunk)
    return str(hash_func.hexdigest())

def get_kwarg(name, default, kwargs):
    return kwargs[name] if name in kwargs else default
    
def get_fileinfo(path, get_hash=False, root=None):

    if not os.path.exists(path):
        raise ValueError("path {0} does not exist".format(path))

    is_dir = os.path.isdir(path)
    stat = os.stat(path)
    file_hash = None
    if get_hash and not is_dir:
        file_hash = get_sha512(path)
    
    info = {}
    if is_dir:
        info['type'] = u'directory'
    else:
        info['type'] = u'file'
    info['device'] = int(stat.st_dev)
    info['inode']  = int(stat.st_ino)
    info['ctime']  = int(stat.st_ctime)
    info['mtime']  = int(stat.st_mtime)
    
    if file_hash is not None:
        info['checksum'] = str(file_hash)
    else:
        info['checksum'] = u''
        
    
    if root is not None:
        # path contains something like /a/b/foo/bar
        # root.path contains something like /a/b/
        rel_path = os.path.relpath(path, root.path)
        # rel_path contains something like foo/bar
        
        dirname, filename = os.path.split(rel_path)
        info['root'] = root
        info['root_uuid'] = u''+root.id
        info['path'] = u''+dirname
        info['filename'] = u''+filename
    
    # info is now populated.
    
    return info

def get_extension(filename):
    return os.path.splitext(filename)[1][1:]