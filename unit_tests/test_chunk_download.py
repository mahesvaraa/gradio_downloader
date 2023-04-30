import os
from unittest.mock import ANY, MagicMock, patch
from urllib.request import Request

from chunk_download_gradio import download_chunk, download_file, interface, select_folder


def test_download_chunk():
    # Создаем фиктивный объект response с нужными атрибутами и методами
    response = MagicMock()
    response.read.side_effect = [b'test', b'']
    # Создаем фиктивный объект urlopen, который возвращает наш фиктивный объект response
    urlopen_mock = MagicMock(return_value=response)
    # Создаем фиктивный объект pbar с нужными атрибутами и методами
    pbar = MagicMock()
    # Используем библиотеку unittest.mock для подмены настоящих функций на фиктивные
    with patch('urllib.request.urlopen', urlopen_mock):
        download_chunk(0, 3, 'http://test.com', pbar)
    # Проверяем, что метод urlopen был вызван с правильными аргументами
    urlopen_mock.assert_called_once_with(Request('http://test.com', headers={'Range': 'bytes=0-3'}))
    # Проверяем, что метод update у объекта pbar был вызван с правильными аргументами
    pbar.update.assert_called_once_with(4)
    # Проверяем, что файл был создан и содержит правильные данные
    with open('chunk_0_3', 'rb') as f:
        assert f.read() == b'test'
    # Удаляем временный файл
    os.remove('chunk_0_3')


def test_download_file():
    # Создаем фиктивные объекты для имитации работы функций download_chunk и urlopen
    download_chunk_mock = MagicMock()
    response_mock = MagicMock(headers={'Content-Length': '100'})
    urlopen_mock = MagicMock(return_value=response_mock)
    # Используем библиотеку unittest.mock для подмены настоящих функций на фиктивные
    with patch('urllib.request.urlopen', urlopen_mock), patch('download_chunk', download_chunk_mock):
        download_file('http://test.com', 4, '/tmp')
    # Проверяем, что метод urlopen был вызван с правильными аргументами
    urlopen_mock.assert_called_once_with(Request('http://test.com', method='HEAD'))
    # Проверяем, что функция download_chunk была вызвана нужное количество раз с правильными аргументами
    assert download_chunk_mock.call_count == 4
    download_chunk_mock.assert_any_call(0, 24, 'http://test.com', ANY)
    download_chunk_mock.assert_any_call(25, 49, 'http://test.com', ANY)
    download_chunk_mock.assert_any_call(50, 74, 'http://test.com', ANY)
    download_chunk_mock.assert_any_call(75, 99, 'http://test.com', ANY)


def test_select_folder():
    # Создаем фиктивный объект для имитации работы функции askdirectory
    askdirectory_mock = MagicMock(return_value='/tmp')
    # Используем библиотеку unittest.mock для подмены настоящей функции на фиктивную
    with patch('tkinter.filedialog.askdirectory', askdirectory_mock):
        result = select_folder()
    # Проверяем, что функция select_folder возвращает правильный результат
    assert result == '/tmp'


def test_interface():
    # Создаем фиктивные объекты для имитации работы функций download_file и open_folder
    download_file_mock = MagicMock()
    open_folder_mock = MagicMock()
    # Используем библиотеку unittest.mock для подмены настоящих функций на фиктивные
    with patch('download_file', download_file_mock), patch('open_folder', open_folder_mock):
        interface('http://test.com', 4, '/tmp')
    # Проверяем, что функция download_file была вызвана с правильными аргументами
    download_file_mock.assert_called_once_with('http://test.com', 4, '/tmp')