from filemanager import FileManager
from settings import MEDIA_ROOT


def view(request, path):
  fm = FileManager(MEDIA_ROOT)
  return fm.render(request, path)
