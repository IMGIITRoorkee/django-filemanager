from filemanager import FileManager
from settings import MEDIA_ROOT


def view(request, path):
    extensions = ['html', 'htm', 'zip', 'py', 'css', 'js', 'jpeg', 'jpg', 'png']
    fm = FileManager(MEDIA_ROOT, extensions=extensions)
    return fm.render(request, path)
