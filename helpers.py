
import os
from tkinter import filedialog, Tk

from urlextract import URLExtract


def get_dir_and_file(file_path):
    dir_path, file_name = os.path.split(file_path)
    return (dir_path, file_name)


def get_folder_path(folder_path=''):
    current_folder_path = folder_path

    initial_dir, initial_file = get_dir_and_file(folder_path)

    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    folder_path = filedialog.askdirectory(initialdir=initial_dir)
    root.destroy()

    if folder_path == '':
        folder_path = current_folder_path

    return folder_path


def get_file(file_path=os.path.expandvars('%userprofile%\downloads')):
    current_file_path = file_path

    initial_dir, initial_file = get_dir_and_file(file_path)

    root = Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir=initial_dir)
    root.destroy()

    if file_path == '':
        file_path = current_file_path
    with open(file_path, 'r', encoding='UTF-8') as file:
        extractor = URLExtract()
        links = extractor.find_urls(file.read())

    return '\n'.join(links)


import threading

class TimeoutError(Exception):
    pass

def timeout(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = None
            exception = None
            def target():
                nonlocal result
                nonlocal exception
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    exception = e

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(seconds)
            if thread.is_alive():
                raise TimeoutError('Function timed out')
            if exception:
                raise exception
            return result
        return wrapper
    return decorator