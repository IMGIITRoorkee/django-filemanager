from io import BytesIO
import json
import mimetypes
import os
import re
import shutil
import tarfile

from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.files import File
from django.core.files.storage import default_storage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils._os import safe_join
from django.utils.six.moves.urllib.parse import urljoin
from django.views.generic import View

from PIL import Image

from . import settings

KB = 1024

ActionChoices = (
    ('upload', 'upload'),
    ('rename', 'rename'),
    ('delete', 'delete'),
    ('add', 'add'),
    ('move', 'move'),
    ('copy', 'copy'),
)


class FileManagerForm(forms.Form):
    ufile = forms.FileField(required=False)
    action = forms.ChoiceField(choices=ActionChoices)
    path = forms.CharField(max_length=200, required=False)
    name = forms.CharField(max_length=32, required=False)
    current_path = forms.CharField(max_length=200, required=False)
    file_or_dir = forms.CharField(max_length=4)


class FileManager(View):
    """
    maxspace,maxfilesize in KB
    """
    basepath = None
    ckeditor_baseurl = ''
    maxfolders = 50
    maxspace = 5 * KB
    maxfilesize = 1 * KB
    extensions = None
    public_url_base = None

    def dispatch(self, request, path):
        self.idee = 0

        if 'download' in request.GET:
            return self.download(path, request.GET['download'])
        if path:
            return self.media(path)
        CKEditorFuncNum = request.GET.get('CKEditorFuncNum', '')
        messages = []
        self.current_path = '/'
        self.current_id = 1
        if request.method == 'POST':
            form = FileManagerForm(request.POST, request.FILES)
            if form.is_valid():
                messages = self.handle_form(form, request.FILES)
        if settings.FILEMANAGER_CHECK_SPACE:
            space_consumed = self.get_size(self.basepath)
        else:
            space_consumed = 0
        return render(request, 'filemanager/index.html', {
            'dir_structure': json.dumps(self.directory_structure()),
            'messages': [str(m) for m in messages],
            'current_id': self.current_id,
            'CKEditorFuncNum': CKEditorFuncNum,
            'ckeditor_baseurl': self.ckeditor_baseurl,
            'public_url_base': self.public_url_base,
            'space_consumed': space_consumed,
            'max_space': self.maxspace,
            'show_space': settings.FILEMANAGER_SHOW_SPACE,
        })

    # XXX Replace with with using storage API
    def rename_if_exists(self, folder, filename):
        if os.path.exists(safe_join(folder, filename)):
            root, ext = os.path.splitext(filename)
            if not ext:
                fmt = '{root}.{i}'
            else:
                fmt = '{root}.{i}.{ext}'
            for i in range(1000):
                filename = fmt.format(root=root, i=i, ext=ext)
                if not os.path.exists(safe_join(folder, filename)):
                    break
        return filename

    def get_size(self, start_path):
        total_size = 0
        for dirpath, dirnames, filenames, dir_fd in os.fwalk(start_path):
            total_size += sum(os.stat(f, dir_fd=dir_fd).st_size for f in filenames)
        return total_size

    def next_id(self):
        self.idee = self.idee + 1
        return self.idee

    def handle_form(self, form, files):
        action = form.cleaned_data['action']
        path = form.cleaned_data['path']
        name = form.cleaned_data['name']
        file_or_dir = form.cleaned_data['file_or_dir']
        self.current_path = form.cleaned_data['current_path']
        messages = []
        if name and file_or_dir == 'dir' and not re.match(r'[\w\d_ -]+', name).group(0) == name:
            messages.append("Invalid folder name : "+name)
            return messages
        if name and file_or_dir == 'file' and (re.search('\.\.', name) or not re.match(r'[\w\d_ -.]+', name).group(0) == name):
            messages.append("Invalid file name : " + name)
            return messages
        if not re.match(r'[\w\d_ -/]+', path).group(0) == path:
            messages.append("Invalid path : " + path)
            return messages
        if action == 'upload':
            for f in files.getlist('ufile'):
                if re.search('\.\.', f.name) or not re.match('[\w\d_ -/.]+', f.name).group(0) == f.name:
                    messages.append("File name is not valid : " + f.name)
                elif f.size > self.maxfilesize * KB:
                    messages.append("File size exceeded {} KB : {}".format(self.maxfilesize, f.name))
                elif settings.FILEMANAGER_CHECK_SPACE and (self.get_size(self.basepath) + f.size) > self.maxspace * KB:
                    messages.append("Total Space size exceeded {} KB: {}".format(self.maxspace, f.name))
                elif self.extensions and len(f.name.split('.')) > 1 and f.name.split('.')[-1] not in self.extensions:
                    messages.append("File extension not allowed (.{}) : {}".format(f.name.split('.')[-1], f.name))
                elif self.extensions and len(f.name.split('.')) == 1 and f.name.split('.')[-1] not in self.extensions:
                    messages.append("No file extension in uploaded file : " + f.name)
                else:
                    full_path = safe_join(self.basepath, path)
                    filepath = safe_join(full_path, self.rename_if_exists(full_path, f.name))
                    with open(filepath, 'wb') as dest:
                        for chunk in f.chunks():
                            dest.write(chunk)
                    f.close()
            if len(messages) == 0:
                messages.append('All files uploaded successfully')
        elif action == 'add':
            os.chdir(self.basepath)
            no_of_folders = len(list(os.walk('.')))
            if (no_of_folders + 1) <= self.maxfolders:
                try:
                    os.chdir(safe_join(self.basepath, path))
                    os.mkdir(name)
                    messages.append('Folder created successfully : {}'.format(name))
                except:
                    messages.append("Folder couldn't be created : {}".format(name))
            else:
                messages.append("Folder couldn' be created because maximum number of folders exceeded : {}".format(self.maxfolders))
        elif action == 'rename' and file_or_dir == 'dir':
            path, oldname = os.path.split(path)
            try:
                os.chdir(safe_join(self.basepath, path))
                os.rename(oldname, name)
                messages.append('Folder renamed successfully from {} to {}'.format(oldname, name))
            except:
                messages.append("Folder couldn't renamed to {}".format(name))
        elif action == 'delete' and file_or_dir == 'dir':
            if path == '/':
                messages.append("root folder can't be deleted")
            else:
                path, name = os.path.split(path)
                try:
                    os.chdir(safe_join(self.basepath, path))
                    shutil.rmtree(name)
                    messages.append('Folder deleted successfully : {}'.format(name))
                except:
                    messages.append("Folder couldn't deleted : {}".format(name))
        elif action == 'rename' and file_or_dir == 'file':
            path, oldname = os.path.split(path)
            _, old_ext = os.path.splitext(oldname)
            _, new_ext = os.path.splitext(name)
            if old_ext == new_ext:
                try:
                    os.chdir(safe_join(self.basepath, path))
                    os.rename(oldname, name)
                    messages.append('File renamed successfully from {} to {}'.format(oldname, name))
                except:
                    messages.append("File couldn't be renamed to {}".format(name))
            else:
                if old_ext:
                    messages.append('File extension should be same : .{}'.format(old_ext))
                else:
                    messages.append("New file extension didn't match with old file extension")
        elif action == 'delete' and file_or_dir == 'file':
            if path == '/':
                messages.append("root folder can't be deleted")
            else:
                name = path.split('/')[-1]
                path = '/'.join(path.split('/')[:-1])
                try:
                    os.chdir(safe_join(self.basepath, path))
                    os.remove(name)
                    messages.append('File deleted successfully : ' + name)
                except:
                    messages.append("File couldn't deleted : " + name)
        elif action == 'move' or action == 'copy':
            # from path to current_path
            if self.current_path.find(path) == 0:
                messages.append('Cannot move/copy to a child folder')
            else:
                path = os.path.normpath(path)  # strip trailing slash if any
                if os.path.exists(safe_join(self.basepath, self.current_path, os.path.basename(path))):
                    messages.append('ERROR: A file/folder with this name already exists in the destination folder.')
                else:
                    if action == 'move':
                        method = shutil.move
                    else:
                        if file_or_dir == 'dir':
                            method = shutil.copytree
                        else:
                            method = shutil.copy
                    try:
                        method(safe_join(self.basepath, path),
                               safe_join(self.basepath, self.current_path, os.path.basename(path)))
                    except:
                        messages.append("File/folder couldn't be moved/copied.")
        return messages

    def directory_structure(self):
        self.idee = 0
        dir_structure = {
            '': {
                'id': self.next_id(),
                'open': True,
                'dirs': {},
                'files': [],
            },
        }
        os.chdir(self.basepath)
        for directory, directories, files in os.walk('.'):
            directory_list = directory[1:].split('/')
            current_dir = None
            nextdirs = dir_structure
            for d in directory_list:
                current_dir = nextdirs[d]
                nextdirs = current_dir['dirs']
            if directory[1:] + '/' == self.current_path:
                self.current_id = current_dir['id']
            current_dir['dirs'].update({
                d: {
                    'id': self.next_id(),
                    'open': False,
                    'dirs': {},
                    'files': [],
                }
                for d in directories
            })
            current_dir['files'] = files
        return dir_structure

    def media(self, path):
        filename = os.path.basename(path)
        root, ext = os.path.splitext(filename)
        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype and mimetype.startswith('image/'):
            if not path.startswith(settings.THUMBNAIL_PREFIX):
                # Generate target filename
                target_name = os.path.join(settings.THUMBNAIL_PREFIX, path)
                if not default_storage.exists(target_name):
                    # Generate the thumbnail
                    img = Image.open(default_storage.open(path))
                    w, h = width, height = img.size
                    mx = max(width, height)
                    if mx > 60:
                        w = width * 60 // mx
                        h = height * 60 // mx
                    img = img.resize((w, h), Image.ANTIALIAS)
                    ifile = BytesIO()
                    # Thanks, SmileyChris
                    fmt = Image.EXTENSION.get(ext.lower(), 'JPEG')
                    img.save(ifile, fmt)
                    default_storage.save(target_name, File(ifile))
                url = urljoin(settings.settings.MEDIA_URL, default_storage.url(target_name))
            else:
                url = urljoin(settings.settings.MEDIA_URL, default_storage.url(path))
        else:
            # Use generic image for file type, if we have one
            try:
                url = static('filemanager/images/icons/{}.png'.format(ext.strip('.')))
            except ValueError:
                url = static('filemanager/images/icons/default.png')
        return HttpResponseRedirect(url)

    def download(self, path, file_or_dir):
        full_path = safe_join(self.basepath, path)
        base_name = os.path.basename(path)
        if not re.match(r'[\w\d_ -/]*', path).group(0) == path:
            return HttpResponse('Invalid path')
        if file_or_dir == 'file':
            response = HttpResponse(open(full_path), content_type=mimetypes.guess_type(full_path)[0])
            response['Content-Length'] = os.path.getsize(full_path)
            response['Content-Disposition'] = 'attachment; filename={}'.format(base_name)
            return response
        elif file_or_dir == 'dir':
            response = HttpResponse(content_type='application/x-gzip')
            response['Content-Disposition'] = 'attachment; filename={}.tar.gz'.format(base_name)
            tarred = tarfile.open(fileobj=response, mode='w:gz')
            tarred.add(full_path, arcname=base_name)
            tarred.close()
            return response
