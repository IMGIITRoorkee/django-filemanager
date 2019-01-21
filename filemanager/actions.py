import mimetypes
import os
import re
import shutil
import zipfile

import magic

from .utils import get_size, rename_if_exists


class Action:
    def __init__(self, action, path, name, is_directory, files, current_path, config):
        self.action = action
        self.path = path
        self.name = name
        self.is_directory = is_directory
        self.files = files
        self.current_path = current_path
        self.config = config
        self.messages = []

    def process_action(self):
        pass

    def get_file_path(self):
        return '/'.join(self.path.split('/')[:-1])

    def get_directory_path(self):
        return '/'.join(self.path.split('/')[:-2])

    def get_file_name(self):
        return self.path.split('/')[-1]

    def get_directory_name(self):
        return self.path.split('/')[-2]

    def get_name_and_path(self):
        if self.is_directory:
            return self.get_directory_name(), self.get_directory_path()
        return self.get_file_name(), self.get_file_path()

    def get_message_with_prefix(self, message):
        prefix = 'Folder ' if self.is_directory else 'File '
        message = "{}{}".format(prefix, message)
        return message

    def add_message(self, message, name='', dir_prefix=False):
        if dir_prefix:
            message = self.get_message_with_prefix(message)

        if name:
            self.messages.append("{} {}".format(message, name))
        else:
            self.messages.append(message)

    @staticmethod
    def handle_action(action, path, name, is_directory, files, current_path, config):
        action_classes = {
            'upload': UploadAction,
            'add': AddAction,
            'delete': DeleteAction,
            'rename': RenameAction,
            'move': MoveAction,
            'copy': CopyAction,
            'unzip': UnzipAction,
        }

        action_class = action_classes.get(action)
        action_class_instance = action_class(action, path, name, is_directory, files, current_path, config)
        messages = action_class_instance.process_action()

        return messages


class UploadAction(Action):
    def process_action(self):
        for f in self.files.getlist('ufile'):

            self.validate_file(f)
            if len(self.messages) == 0:
                filename = f.name.replace(' ', '_')  # replace spaces to prevent fs error
                filepath = (
                        self.config['basepath']
                        + self.path
                        + rename_if_exists(self.config['basepath'] + self.path, filename)
                )
                with open(filepath, 'wb') as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                f.close()
                mimetype = magic.from_file(filepath, mime=True)
                guessed_exts = mimetypes.guess_all_extensions(mimetype)
                guessed_exts = [ext[1:] for ext in guessed_exts]
                common = [ext for ext in guessed_exts if ext in self.config['extensions']]
                if not common:
                    os.remove(filepath)
                    self.messages.append(
                        "File type not allowed : "
                        + f.name
                    )
        if len(self.messages) == 0:
            self.messages.append('All files uploaded successfully')

        return self.messages

    def validate_file(self, f):
        file_name_invalid = (
                re.search(r'\.\.', f.name)
                or not re.match(r'[\w\d_ -/.]+', f.name).group(0) == f.name
        )
        if file_name_invalid:
            self.messages.append("File name is not valid : " + f.name)
        elif f.size > self.config['maxfilesize'] * 1024:
            self.messages.append("File size exceeded " + str(self.config['maxfilesize']) + " KB : " + f.name)
        elif (
                self.config['FILEMANAGER_CHECK_SPACE'] and
                ((get_size(self.config['basepath']) + f.size) > self.config['maxspace'] * 1024)
        ):
            self.messages.append("Total Space size exceeded " + str(self.config['maxspace']) +
                                 " KB : " + f.name)
        elif (
                self.config['extensions']
                and len(f.name.split('.')) > 1
                and f.name.split('.')[-1] not in self.config['extensions']
        ):
            self.messages.append("File extension not allowed (." + f.name.split('.')[-1] + ") : " + f.name)
        elif (
                self.config['extensions']
                and len(f.name.split('.')) == 1
                and f.name.split('.')[-1]
                not in self.config['extensions']
        ):
            self.messages.append("No file extension in uploaded file : " + f.name)


class RenameAction(Action):
    def process_action(self):
        oldname, path = self.get_name_and_path()

        if not self.is_directory:
            old_ext = self.get_extension_from_filename(oldname)
            new_ext = self.get_extension_from_filename(self.name)

            if old_ext != new_ext:
                if old_ext:
                    self.messages.append('File extension should be same : .' + old_ext)
                else:
                    self.messages.append('New file extension didn\'t match with old file' + ' extension')

                return self.messages

        try:
            os.chdir(self.config['basepath'] + path)
            os.rename(oldname, self.name)
            self.add_message('renamed successfully from ' + oldname + ' to ', self.name, dir_prefix=True)
        except OSError:
            self.add_message('couldn\'t be renamed to ', self.name, dir_prefix=True)
        except Exception as e:
            self.add_message('Unexpected error : ', str(e))

        return self.messages

    def get_extension_from_filename(self, filename):
        return filename.split('.')[1] if len(filename.split('.')) > 1 else None


class DeleteAction(Action):
    def process_action(self):
        if self.path == '/':
            self.add_message('root folder can\'t be deleted')
            return self.messages

        name, path = self.get_name_and_path()
        os.chdir(self.config['basepath'] + path)

        try:
            if self.is_directory:
                shutil.rmtree(name)
            else:
                os.remove(name)
            self.add_message('deleted successfully : ', name, dir_prefix=True)
        except OSError:
            self.add_message('couldn\'t be deleted : ', name, dir_prefix=True)
        except Exception as e:
            self.add_message('Unexpected error : ', str(e))

        return self.messages


class AddAction(Action):
    def process_action(self):
        os.chdir(self.config['basepath'])
        no_of_folders = len(list(os.walk('.')))
        if (no_of_folders + 1) <= self.config['maxfolders']:
            try:
                os.chdir(self.config['basepath'] + self.path)
                os.mkdir(self.name)
                self.messages.append('Folder created successfully : ' + self.name)
            except OSError:
                self.messages.append('Folder couldn\'t be created : ' + self.name)
            except Exception as e:
                self.messages.append('Unexpected error : ' + e)
        else:
            self.messages.append(
                'Folder couldn\' be created because maximum number of '
                + 'folders exceeded : '
                + str(self.config['maxfolders'])
            )

        return self.messages


class MoveAction(Action):
    def process_action(self):
        # from path to current_path
        if self.current_path.find(self.path) == 0:
            self.messages.append('Cannot move/copy to a child folder')
        else:
            self.path = os.path.normpath(self.path)  # strip trailing slash if any
            filename = (
                    self.config['basepath']
                    + self.current_path
                    + os.path.basename(self.path)
            )
            if os.path.exists(filename):
                self.messages.append(
                    'ERROR: A file/folder with this name already exists in'
                    + ' the destination folder.'
                )
            else:
                if self.action == 'move':
                    method = shutil.move
                else:
                    if self.is_directory:
                        method = shutil.copytree
                    else:
                        method = shutil.copy
                try:
                    method(self.config['basepath'] + self.path, filename)
                except OSError:
                    self.messages.append(
                        'File/folder couldn\'t be moved/copied.'
                    )
                except Exception as e:
                    self.messages.append('Unexpected error : ' + e)

        return self.messages


class CopyAction(MoveAction):
    pass


class UnzipAction(Action):
    def process_action(self):
        if self.is_directory:
            self.messages.append('Cannot unzip a directory')
        else:
            try:
                self.path = os.path.normpath(self.path)  # strip trailing slash if any
                filename = (
                        self.config['basepath']
                        + self.current_path
                        + os.path.basename(self.path)
                )
                zip_ref = zipfile.ZipFile(filename, 'r')
                directory = self.config['basepath'] + self.current_path
                for file in zip_ref.namelist():
                    if file.endswith(tuple(self.config['extensions'])):
                        zip_ref.extract(file, directory)
                        mimetype = magic.from_file(directory + file, mime=True)
                        print(directory + file)
                        guessed_exts = mimetypes.guess_all_extensions(mimetype)
                        guessed_exts = [ext[1:] for ext in guessed_exts]
                        common = [ext for ext in guessed_exts if ext in self.config['extensions']]
                        if not common:
                            os.remove(directory + file)
                            self.messages.append(
                                "File in the zip is not allowed : "
                                + file
                            )
                zip_ref.close()
            except Exception as e:
                print(e)
                self.messages.append('ERROR : Could not unzip the file.')
            if len(self.messages) == 0:
                self.messages.append('Extraction completed successfully.')

        return self.messages
