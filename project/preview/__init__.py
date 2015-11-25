import os
import urllib
import mimetypes
from project import app
from flask import render_template
from project.models import FilesystemObject



def guess_mimetype(filename):
    """
    Gets the mimetype of the specified file
    """
    url = urllib.pathname2url(filename)
    mimes = mimetypes.guess_type(url)[0]
    if mimes is None:
        return ''
    else:
        return mimes

class ObjectPreview(object):
    name = "Unknown"
    content = "No preview!"
    icon = "question"
    id = "unknown"
    js = []
    css = []
    def __init__(self, name="(none)", content="", icon="unknown", id="unknown", js=[], css=[]):
        self.name = name
        self.content = content
        self.icon = icon
        self.id=id
        self.js = js
        self.css = []


class PreviewBase(object):
    
    @staticmethod
    def can_preview(fsObject):
        return False
    
    @staticmethod
    def generate_preview(fsObject):
        """
        """
        return ObjectPreview() 

from .image import ImagePreview,ExifPreview
from .code import  CodePreview
from .document import MarkdownPreview

__previewers = ( ImagePreview, ExifPreview, MarkdownPreview, CodePreview, PreviewBase )

def get_previews(fsObject):
    previews = []
    for previewer in __previewers:
        if previewer.can_preview(fsObject):
            previews.append(previewer.generate_preview(fsObject))
    return previews

