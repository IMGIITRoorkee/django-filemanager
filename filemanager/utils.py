import mimetypes
import os

from django.http import HttpResponse
from PIL import Image

from . import settings


def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def rename_if_exists(folder, file):
    if folder[-1] != os.sep:
        folder = folder + os.sep
    if os.path.exists(folder + file):
        if file.find('.') == -1:
            # no extension
            for i in range(1000):
                if not os.path.exists(folder + file + '.' + str(i)):
                    break
            return file + '.' + str(i)
        else:
            extension = file[file.rfind('.'):]
            name = file[:file.rfind('.')]
            for i in range(1000):
                full_path = folder + name + '.' + str(i) + extension
                if not os.path.exists(full_path):
                    break
            return name + '.' + str(i) + extension
    else:
        return file


def get_media(basepath, path):
    ext = path.split('.')[-1]
    try:
        mimetypes.init()
        mimetype = mimetypes.guess_type(path)[0]
        img = Image.open(basepath + '/' + path)
        width, height = img.size
        mx = max([width, height])
        w, h = width, height
        if mx > 60:
            w = width * 60 / mx
            h = height * 60 / mx
        img = img.resize((w, h), Image.ANTIALIAS)
        response = HttpResponse(content_type=mimetype or "image/" + ext)
        response['Cache-Control'] = 'max-age=3600'
        img.save(
            response,
            mimetype.split('/')[1] if mimetype else ext.upper()
        )
        return response

    except Exception:
        imagepath = (
                settings.FILEMANAGER_STATIC_ROOT
                + 'images/icons/'
                + ext
                + '.png'
        )
        if not os.path.exists(imagepath):
            imagepath = (
                    settings.FILEMANAGER_STATIC_ROOT
                    + 'images/icons/default.png'
            )
        img = Image.open(imagepath)
        width, height = img.size
        mx = max([width, height])
        w, h = width, height
        if mx > 60:
            w = int(width * 60 / mx)
            h = int(height * 60 / mx)
        img = img.resize((w, h), Image.ANTIALIAS)
        response = HttpResponse(content_type="image/png")
        response['Cache-Control'] = 'max-age:3600'
        img.save(response, 'png')

        return response
