from models import Root, FilesystemObject
from helpers import get_sha512,get_fileinfo
from project import app, db
import os
import sys
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)
scan_logger = logging.getLogger(__name__)

def scan(root):
    """
    Scans a root for files, updating as needed.
    """
    scan_logger.debug("Beginning scan of root %s", root.id)
    root_fspath = root.path
    walker = os.walk(root_fspath)
    for elem in walker:
        for folder_name in elem[1]:
            update_object(root, elem[0], folder_name)
        for file_name in elem[2]:
            update_object(root, elem[0], file_name)
    # Clean up any object within the database that no longer exists.
    cleanup()
    db.session.commit()

def cleanup():
    db.session.commit()
    scan_logger.info("Beginning Database Cleanup")
    for obj in FilesystemObject.query.all():
        # scan_logger.debug("Object %s root %s ( %s ) has real path %s ", obj.id, obj.root.id, obj.root.path, obj.get_real_path())
        path = obj.get_real_path()
        if path is None:
            db.session.delete(obj)
        elif not os.path.exists(obj.get_real_path()):
            scan_logger.info("Cleansing object %s (doesn't exist anymore", obj.id)
            db.session.delete(obj) 
    db.session.commit()

def update_object(root, path, filename):
    """
    takes a path to a file (directory or real) and updates its element in the object listing.
    """

    scan_logger.debug("Inspecting object at "+os.path.join(path, filename))

    file_info = get_fileinfo(os.path.join(root.path, path, filename), get_hash=True, root=root)
    
    search_object = None
    
    # Our first pass is to see if the file that exists on disk also exists on the database
    #scan_logger.debug("Looking for objects with path='%s' filename='%s'", db_path, filename )
    try:
        search_object = FilesystemObject.find(root, file_info)
    except Exception as e:
        scan_logger.warn("Multiple objects with same filename? -- what?")
        print "***************** EXCEPTION *******************"
        traceback.print_exc(e)
        print "***************** TRACEBACK *******************"
        traceback.print_stack(e)
        print "***********************************************"
        return None
        
    if search_object is None:

        search_object = FilesystemObject.create(root, os.path.join(path, filename))
        scan_logger.info("NEW object "+search_object.id+" at "+search_object.get_real_path())
        db.session.add(search_object)
        return
    else:
        scan_logger.debug("Object: %d:%d -> %s ", search_object.device, search_object.inode, search_object.get_real_path())
        # update the object if needed.
        
        # Check if the object we found exists.
        
        obj_real_path = search_object.get_real_path()
        if obj_real_path is None:
            print "WTF????"
            print search_object.id
            print search_object.root.path
            print search_object.path
            print search_object.filename
        chk_real_path = os.path.join(root.path, file_info['path'], file_info['filename'])

        if  os.path.exists(obj_real_path) and \
            os.path.exists(chk_real_path) and \
            obj_real_path != chk_real_path :
            # They are duplicates of each other, but the new file needs
            # to exist in the database as well. Dead files get cleaned up during
            # the checkout process.
            scan_logger.info("Explictly duplicate objects among %s and %s",
                os.path.join(file_info['path'], file_info['filename']),
                os.path.join(search_object.path, search_object.filename))
            new_object = FilesystemObject.create(root, os.path.join(path, filename))
            db.session.add(new_object)
            return
        
        changed = False
        
        mobject = FilesystemObject.query.get(search_object.id)
        if not mobject.inode == file_info['inode']:
            scan_logger.debug("Object inode doesn't match")
            mobject.inode = file_info['inode']
            changed = True
        if not mobject.device == file_info['device']:
            scan_logger.debug("Object device doesn't match")
            mobject.device = file_info['device']
            changed = True
        if not mobject.filename == file_info['filename']:
            scan_logger.debug("Object filename doesn't match")
            mobject.filename = file_info['filename']
            changed = True
        if not mobject.path == file_info['path']:
            scan_logger.debug("Object path doesn't match")
            mobject.path = file_info['path']
            changed = True
        if 'checksum' in file_info.keys() and not mobject.checksum == file_info['checksum']:
            scan_logger.debug("Object checksum doesn't match")
            mobject.checksum = file_info['checksum']
            changed = True
        if not mobject.mtime == file_info['mtime']:
            scan_logger.debug("Object modify time is out of date")
            mobject.mtime = file_info['mtime']
            changed = True
            
        if changed:
            scan_logger.info("Update object %s -> %s", mobject.id, mobject.get_real_path())
            db.session.commit()



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="scanner",description="Scan 9track roots")
    parser.add_argument('roots', metavar='root',type=str, nargs='*',
        help="Roots to scan")
    parser.add_argument('--all', dest='do_all', action='store_const',const=True, default=False,
        help="Scan all roots in the database.")
    parser.add_argument('--quiet', dest='loglevel',
        action='store_const', const=logging.ERROR, default=logging.INFO,
        help="Suppress logging messages")
    parser.add_argument('--debug', dest='loglevel',
        action='store_const', const=logging.DEBUG, default=logging.INFO,
        help="Debug ALL the things!")
    parser.add_argument('--refresh', dest="delall",
        action='store_const', const=True, default=False,
        help="Destroy all objects before scan")
    parser.add_argument('--list', dest='list_roots',
     action='store_const',const=True, default=False,
     help='List the roots (and owners) in the database.')
    
    args = parser.parse_args()
    
    # Set log level
    scan_logger.setLevel(args.loglevel)
    
    # if we're told to list them (--list) do so and exit.
    if args.list_roots:
        for root in Root.query.all():
            print( "{0}: {1}\n\t{2}".format(root.owner.name, root.id, root.path) )
        sys.exit(0)
    
    # if the option --all was given, scan everyone.
    scanning_roots = []
    if args.do_all:
        scanning_roots = Root.query.all()
    else:
        scanning_roots = []
        for root in args.roots:
            # Gonna be a string
            scanning_roots.append(Root.query.get(root))
    
    # Now, for each of those roots, scan the little bastard
    for root in scanning_roots:
        if args.delall:
            for x in FilesystemObject.query.filter_by(root_uuid=root.id):
                db.session.delete(x)
            db.session.commit()
        else:
            scan(root)
    
