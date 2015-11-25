from project import db as db
from flask import session
from project.helpers import get_sha512 as hash_file
from project.helpers import get_fileinfo
from project.helpers import get_kwarg
import hashlib
import binascii
import os.path
import uuid
import datetime
import bcrypt
import mimetypes
import urllib
import os
import math

def get_mime(filepath):
    tmp_url = urllib.filepath2url(filepath)
    return mimetypes.guess_from_url(tmp_url)

db.create_all()

class User(db.Model):
    __tablename__="users"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True)
    pwhash = db.Column(db.String)
    roots = db.relationship("Root", backref="owner")


    def __init__(self, id , name, pwhash ):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.pwhash = pwhash

    @staticmethod
    def create(username, password):
        """ Creates a user given the specified inputs. """
        salt = bcrypt.gensalt(8)
        pork = bcrypt.hashpw(password.encode('utf-8'), salt)
        return User(None, username, pork)

    @staticmethod
    def get_current():
        if 'user' in session:
            return User.query.get(session['user'])
        else:
            return None

    @staticmethod
    def login(username, password):
        """
        Logs in a user from :username and :password

        """
        u = User.query.filter_by(name=username).one_or_none()
        if u is None:
            return None
        if not bcrypt.hashpw(password.encode('utf-8'), u.pwhash.encode('utf-8') ) == u.pwhash:
            return None
        session['user'] = u.id
        return u

    @staticmethod
    def logout():
        """
        Logs out the session's currently logged in user.
        """
        session.pop('user')
        pass


class Root(db.Model):
    __tablename__ = 'roots'
    id = db.Column(db.String, primary_key=True)
    path = db.Column(db.String)
    name = db.Column(db.String)
    owner_uuid = db.Column(db.String, db.ForeignKey('users.id') )
    visibility = db.Column(db.Enum('inherit','private', 'protected', 'public'))
    objects = db.relationship("FilesystemObject", backref="root")

    def __init__( self, id, path, name, owner , visibility='inherit' ):
        if id is None:
            self.id = str( uuid.uuid4() )
        else:
            self.id = id
        self.path = path
        self.name = name
        if isinstance(owner, User):
            self.owner_uuid = owner.id
        else:
            self.owner_uuid = owner

        self.visibility = visibility

    def get_usage_pct(self):
        stats = os.statvfs(self.path)
        used_blocks = stats.f_blocks - stats.f_bfree
        used_pct = float(used_blocks)/float(stats.f_blocks)
        used_int = int(round(100*used_pct))
        return used_int

    def obj_count(self):
        files = FilesystemObject.query.filter_by(root_uuid=self.id,type='file').all()
        dirs  = FilesystemObject.query.filter_by(root_uuid=self.id,type='directory').all()
        return ( len(dirs), len(files) )

class FilesystemObject(db.Model):
    __tablename__ = "library_objects"
    id = db.Column(db.String, primary_key=True)
    #
    # Folders will have a filename but no checksum.
    # Folders also have the type "directory" as opposed to "File"
    # 
    path = db.Column(db.String, default=u'')
    filename = db.Column(db.String, default=u'')

    checksum = db.Column(db.String, default=u'')
    device = db.Column(db.Integer, default=0)
    inode = db.Column(db.Integer,  default=0)

    ctime = db.Column(db.Integer, default=0)
    mtime = db.Column(db.Integer, default=0)

    root_uuid = db.Column(db.String, db.ForeignKey('roots.id'))

    type = db.Column(db.Enum(u'file', u'directory'), default=u'file')
    visibility = db.Column(db.Enum(u'inherit', u'private', u'protected', u'public'), default=u'inherit')
    
    def __init__(self, id, **kwargs):
        if id is None:
            self.id = str( uuid.uuid4() )
        else:
            self.id = id
        self.path = get_kwarg('path', u'', kwargs)  #  path
        if self.path is None:
            raise ValueError("Objects must have a path, even if it is emptystring!")
        self.checksum = get_kwarg('checksum', u'', kwargs)
        self.filename = get_kwarg('filename', u'', kwargs)
        self.inode = int(get_kwarg('inode', 0, kwargs))
        self.device = int(get_kwarg('device', 0, kwargs))
        self.type = get_kwarg('type', u'file', kwargs)
        
        self.mtime = get_kwarg('mtime', 0.0, kwargs)
        self.ctime = get_kwarg('ctime', 0.0, kwargs)
        
        if self.type is u'file' and self.checksum is u'':
            raise ValueError("Files must have a checksum!")
        elif self.type is u'directory' and self.checksum is not u'':
            raise ValueError("Directories must NOT have a checksum!")
        else:
            self.checksum = u''+self.checksum
        
        if self.device is 0 or self.inode is 0:
            raise ValueError("Invalid device or inode <device=%d inode=%d>".format(self.device, self.inode))
        
        # If we were stupidly passed a Root object instead of a UUID, we want
        # to make it be turned into the appropriate thing
        #
        # We also want to make sure that if we're handed a uuid that isn't a
        # string, we smash it into string form. Wooo
        
        __root = get_kwarg('root', None, kwargs)
        if __root is None:
            raise ValueError("Objects MUST have a root!")
        
        if isinstance(__root, Root):
            self.root_uuid = __root.id
        else:
            self.root_uuid = str(__root)
        self.root = Root.query.get(self.root_uuid)
        self.visibility = get_kwarg('visibility', u'private', kwargs)
    
    
    @staticmethod
    def create(root, path):
    
        obj_info = get_fileinfo(path, root=root,get_hash=True)
        obj = FilesystemObject(None, **obj_info)
        
        return obj
        

    def get_real_path(self):
        """
        Determines the real path to the file.

        simply joins the root's path, own path and own filename together using
        :os.path.join: 

        """
        return os.path.join(self.root.path, self.path, self.filename)

    def get_filesize(self, human=False):
        stat = os.stat(self.get_real_path())
        if human:
            # Human filesizes
            scales = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
            sz = stat.st_size
            index = math.floor( (len( str( sz ) )-1) / 3 )
            return "{0:.2f}{1}".format(sz/math.pow(1024, index), scales[int(index)])
        return stat.st_size

    def validate(self):
        r_path = self.get_real_path()
        if r_path is None:
            return False
        if not os.path.isdir(r_path):
            # Check to see that the file has the same hash
            check = hash_file(r_path)
            if not self.checksum == check:
                return False

    def get_children(self):
        if not self.type == u'directory':
            return None
        else:
            return FilesystemObject.query.filter_by(path=self.get_real_path()).all()
    
    def get_visibility(self):
        """
            Gets the visibility of an object. 
        """
        if not self.visibility == 'inherit':
            return self.visibility
        # Get our parent
        parent_path, parent_fname = os.path.split(self.path)
        parent_object = FilesystemObject.query.filter_by(path=parent_path, filename=parent_fname).one_or_none()
        if parent_object is None:
            # default to our root's visibility.
            return self.root.visibility
        else:
            return parent_object.get_visibility()

    def get_mimetype(self):
        return get_mime(self.get_real_path())
    
    @staticmethod
    def find(root, info):
        """
            Finds an object by a selection of attributes. 
        """
        

        found_obj_ids = []
        
        if 'root_uuid' not in info.keys():
            info['root_uuid'] = root.id
            #info['root'] = root
        
        # First pass: see if there's any objects which match the given kwargs:
        blast_find = FilesystemObject.query.filter_by(**info).all()
        if len(blast_find) == 1:
            return blast_find[0]
        else:
            for obj in blast_find:
                found_obj_ids.append(obj.id)
                
        search_dicts = (
            
            {'inode':info['inode'], 'device':info['device']},
            {'inode':info['inode'], 'device':info['device'], 'type':info['type']},
            {'path':info['path'], 'filename':info['filename']},
            {'filename':info['filename'], 'checksum':info['checksum']},
            {'filename':info['filename'], 'path':info['path'], 'checksum':info['checksum']}
            
        )

        for search in search_dicts:
            objs = FilesystemObject.query.filter_by(**search).all()
            for obj in objs:
                found_obj_ids.append(obj.id)
        
        if len(found_obj_ids) == 0:
            return None
        if len(found_obj_ids) == 1:
            return FilesystemObject.query.get(found_obj_ids[0])
        
        unique_ids = list(set(found_obj_ids))
        if len(unique_ids) == 1:
            # We only found one object. Return it.
            found_obj_id = unique_ids[0]
            return FilesystemObject.query.get(found_obj_id)
        
        # If we found *nothing* matching what that should look like, we're toasted.
        if len(unique_ids) == 0:
            return None

        
        found_id_counts = {}
        # Walk through our unique ids 
        for unique_id in found_obj_ids:
            if unique_id in found_id_counts.keys():
                found_id_counts[unique_id] += 1
            else:
                found_id_counts[unique_id] = 1
        
        
        # Find the most common object ID.
        
        match_max = max(found_id_counts.values())
        
        max_objs = []
        for k in found_id_counts.keys():
            v = found_id_counts[k]
            if v == match_max:
                max_objs.append(k)
        
        #max_objs = filter(lambda x:found_obj_ids[x]==match_max, found_id_counts.keys())
        if len(max_objs) > 1:
            raise ValueError("Ambiguous data in DB; inconsistent!")
        else:
            return FilesystemObject.query.get(max_objs[0])
            
    @staticmethod
    def find_by_inode(root, device, inode):
        """
        Finds one specific item by inode. If there are > 1 items with that inode/device pair
        it returns None
        """
        try:
            x = FilesystemObject.query.filter_by( root_uuid=root.id, inode=inode, device=device).one_or_none()
            return x
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def find_by_path(root, path):    
        pass

    @staticmethod
    def find_by_hash(root, shahash):
        try:
            x= FilesystemObject.query.filter_by(root_uuid=root.id, checksum=shahash).one_or_none()
            return x
        except:
            print("Excepted")
            return None
    
    @staticmethod
    def find_by_uuid(guid):
        return FilesystemObject.query.get(guid).one_or_none()
