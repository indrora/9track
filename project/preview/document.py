from . import ObjectPreview
from . import PreviewBase
import markdown

class MarkdownPreview(PreviewBase):
    @staticmethod
    def can_preview(fsobject):
        return fsobject.filename.endswith(".md")
    @staticmethod
    def generate_preview(fsobject):
        doc = open(fsobject.get_real_path(), 'r')
        doc_contents = doc.read()
        doc.close()
        doc_md = markdown.markdown(doc_contents)
        return ObjectPreview(
            "Markdown",
            doc_md,
            "file-text",
            "markdown"
        )