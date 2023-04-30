import os
import threading
from urllib.request import Request, urlopen

from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QThread, pyqtSignal

from tqdm import tqdm


class DownloadThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, start: int, end: int, url: str):
        super().__init__()
        self.start = start
        self.end = end
        self.url = url

    def run(self):
        max_attempts = 3
        attempts = 0
        while attempts < max_attempts:
            try:
                req = Request(self.url)
                req.headers['Range'] = f'bytes={self.start}-{self.end}'
                response = urlopen(req)
                with open(f'chunk_{self.start}_{self.end}', 'wb') as f:
                    while True:
                        chunk = response.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        self.progress.emit(len(chunk))
                break
            except Exception as e:
                print(f'Error downloading chunk {self.start}-{self.end}: {e}')
                attempts += 1


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('mainwindow.ui', self)

        self.download_button.clicked.connect(self.download_file)
        self.open_button.clicked.connect(self.open_file)

    def download_file(self):
        url = self.url_input.text()
        num_threads = int(self.thread_input.text())

        req = Request(url)
        req.method = 'HEAD'
        response = urlopen(req)
        file_size = int(response.headers['Content-Length'])
        chunk_size = file_size // num_threads

        self.pbar.setMaximum(file_size//1024)

        threads = []
        for i in range(num_threads):
            start = i * chunk_size
            end = start + chunk_size - 1
            if i == num_threads - 1:
                end = file_size - 1
            thread = DownloadThread(start, end, url)
            thread.progress.connect(self.update_progress)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.wait()

        filename = os.path.basename(url)
        with open(filename, 'wb') as f:
            for i in range(num_threads):
                start = i * chunk_size
                end = start + chunk_size - 1
                if i == num_threads - 1:
                    end = file_size - 1
                chunk_filename = f'chunk_{start}_{end}'
                with open(chunk_filename, 'rb') as chunk_file:
                    f.write(chunk_file.read())
                os.remove(chunk_filename)

    def update_progress(self, value: int):
        self.pbar.setValue(self.pbar.value() + value)

    def open_file(self):
        url = self.url_input.text()
        filename = os.path.basename(url)
        os.startfile(filename)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()