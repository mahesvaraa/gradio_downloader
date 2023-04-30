import os
import threading
from urllib.request import Request, urlopen

from tqdm import tqdm


def download_chunk(start: int, end: int, url: str, pbar: tqdm) -> None:
    """Скачивает часть файла и сохраняет ее в отдельный файл.

    Аргументы:
    start -- начальная позиция части файла
    end -- конечная позиция части файла
    url -- URL-адрес файла для скачивания
    pbar -- индикатор загрузки для обновления прогресса
    """
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            # Отправляем HTTP-запрос с заголовком Range для скачивания части файла
            req = Request(url)
            req.headers['Range'] = f'bytes={start}-{end}'
            response = urlopen(req)
            # Сохраняем скачанные данные в файле
            with open(f'chunk_{start}_{end}', 'wb') as f:
                while True:
                    chunk = response.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    pbar.update(len(chunk))
            break
        except Exception as e:
            print(f'Error downloading chunk {start}-{end}: {e}')
            attempts += 1


def download_file(url: str, num_threads: int) -> None:
    """Скачивает файл многопоточно и сохраняет его на диске.

    Аргументы:
    url -- URL-адрес файла для скачивания
    num_threads -- количество потоков для скачивания файла
    """
    # Отправляем HTTP-запрос HEAD для получения размера файла
    req = Request(url)
    req.method = 'HEAD'
    response = urlopen(req)
    file_size = int(response.headers['Content-Length'])
    chunk_size = file_size // num_threads

    # Создаем общий индикатор загрузки для всех потоков
    pbar = tqdm(total=file_size, unit='B', unit_scale=True)

    # Создаем потоки для скачивания файла
    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = start + chunk_size - 1
        if i == num_threads - 1:
            end = file_size - 1
        thread = threading.Thread(target=download_chunk, args=(start, end, url, pbar))
        thread.start()
        threads.append(thread)

    # Ожидаем завершения всех потоков
    for thread in threads:
        thread.join()

    # Закрываем индикатор загрузки
    pbar.close()

    # Объединяем все части файла в один файл и удаляем временные файлы
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


if __name__ == '__main__':
    url = 'https://build1.axxonsoft.dev/bamboo/plugins/servlet/sftp-artifact/ASIP-AN33/ASIP-AN33/shared/build-10960/Installer-x64/AxxonNext-4.6.3.10960-x64-full.zip'
    num_threads = 16
    download_file(url, num_threads)
