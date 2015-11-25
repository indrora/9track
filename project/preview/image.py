from . import PreviewBase
from . import guess_mimetype
from . import ObjectPreview
#from project.previewers import guess_mimetype
#from project.previewers import ObjectPreview, PreviewBase 
from flask import url_for
import os
import os.path
import exifread

image_exts = ('jpg', 'jpe', 'png', 'bmp')

class ImagePreview(PreviewBase):
    @staticmethod
    def can_preview(fsObject):
        # first order pass: see if it looks like a picture
        end = os.path.splitext(fsObject.filename)[1][1:]
        if end in image_exts:
            return True
        # second pass: Try and guess the mimetype
        mime = guess_mimetype(fsObject.get_real_path())
        if mime.startswith("image/"):
            return True
        return False

    @staticmethod
    def generate_preview(fsObject):
        preview = ObjectPreview("Image", "(placeholder content)", "picture-o", "image")
        preview.content = '<img src="'+url_for('get_object_contents',
            object_id=fsObject.id, action='raw')+'" class="img-responsive" />'
        return preview

class ExifPreview(PreviewBase):
    @staticmethod
    def get_tags(filepath):
        f = open(filepath, 'rb')
        tags = exifread.process_file(f, details=False)
        f.close()
        return tags
    
    @staticmethod
    def can_preview(fsObject):
        return len(ExifPreview.get_tags(fsObject.get_real_path())) > 0
    @staticmethod
    def generate_preview(fsObject):
        tags = ExifPreview.get_tags(fsObject.get_real_path())
        content = '<table class="table">'
        for tag in tags:
            content += '\n<tr><td>'+str(tag)+'</td><td>'+str(tags[tag])+'</td></tr>'
        content += '</table>'
        return ObjectPreview("EXIF", content, "camera-retro", "exif")