import os
from concurrent.futures import as_completed, ThreadPoolExecutor
from contextlib import ExitStack
from functools import partial
from urllib.parse import urlparse

import gradio as gr
import pandas as pd
import wget as wget
from chunk_download_gradio import download_file, open_folder
from urlextract import URLExtract

from helpers import get_file, get_folder_path, timeout


def find_links(text):
    extractor = URLExtract()
    links = extractor.find_urls(text)
    links = [url.replace(',', '') for url in links if '.' in urlparse(url).path.split('/')[-1]]
    return '\n'.join(sorted(set(links), key=links.index))


def download_from_text(text_field, output_path, threads=4,
                       progress=gr.Progress(track_tqdm=True)):
    extractor = URLExtract()
    links = extractor.find_urls(text_field)
    print(links)
    results = []

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    download_files = partial(wget.download, out=output_path)
    download_files = timeout(100)(download_files)
    with ExitStack() as stack:
        executor = stack.enter_context(ThreadPoolExecutor(max_workers=int(threads)))
        futures = [executor.submit(download_files, url) for url in links]
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append([result, 'Success'])
            except Exception as e:
                results.append(['Timeout_error', f'Failed:\n {e}'])
                future.done()

    df = pd.DataFrame(results, columns=['File', 'Status'])
    return df


if os.path.exists('./style.css'):
    css = ''
    with open(os.path.join('./style.css'), 'r', encoding='utf8') as file:
        print('Load CSS...')
        css += file.read() + '\n'


def open_file(file_path):
    os.startfile(file_path)


def open_in_explorer(file_path):
    os.startfile(file_path)


with gr.Blocks(css=css) as demo:
    with gr.Tab("Downloader from list of links"):
        with gr.Row():
            select_file_button = gr.Button('📂', elem_id='open_file_small')
            file_links_input = gr.Textbox(
                label='Links',
                placeholder='Enter the links in the field or select a text file with links. '
                            'E.g https://img1.goodfon.ru/wallpaper/nbig/a/69/kartinka-3d-dikaya-koshka.jpg'
            )
            find_links_button = gr.Button('Find url in text', elem_id='number_input')
            find_links_button.click(
                find_links,
                inputs=file_links_input,
                outputs=file_links_input
            )
            select_file_button.click(
                get_file,
                outputs=file_links_input,
                show_progress=False,
            )

        with gr.Row():
            train_data_dir_input_folder = gr.Button(
                '📂', elem_id='open_folder_small'
            )
            output_dir_input = gr.Textbox(
                label='Output directory',
                placeholder=f'Path to download. Default: {os.path.join(os.path.expandvars("%userprofile%"), "downloads")}'
            )
            train_data_dir_input_folder.click(
                get_folder_path,
                outputs=output_dir_input,
                show_progress=False,
            )
            number_threads = gr.Dropdown(
                list(range(1, os.cpu_count() + 1)),
                label='Threads',
                elem_id='number_input'
            )
            number_threads.value = number_threads.choices[0]

        with gr.Row():
            text_button = gr.Button("Start download")

        with gr.Accordion(
                "Results",
                open=False
        ):
            with gr.Row():
                text_output = gr.Dataframe(headers=['File', 'Status'])

        with gr.Row():
            open_in_explorer_button = gr.Button("Open in Explorer")

        text_button.click(
            download_from_text,
            inputs=[file_links_input, output_dir_input, number_threads],
            outputs=text_output
        )
        open_in_explorer_button.click(
            open_in_explorer,
            inputs=output_dir_input
        )

    with gr.Tab("Multithreaded download"):
        # Создаем строку для ввода ссылок на файлы
        with gr.Row():
            file_links_input = gr.Textbox(
                label='Links',
                placeholder='Enter the links in the field or select a text file with links. '
                            'E.g https://img1.goodfon.ru/wallpaper/nbig/a/69/kartinka-3d-dikaya-koshka.jpg'
            )

        # Создаем строку для выбора папки для сохранения файлов
        with gr.Row():
            train_data_dir_input_folder = gr.Button(
                '📂', elem_id='open_folder_small'
            )
            output_dir_input = gr.Textbox(
                label='Output directory',
                placeholder=f'Path to download. Default: {os.path.join(os.path.expandvars("%userprofile%"), "downloads")}'
            )
            train_data_dir_input_folder.click(
                get_folder_path,
                outputs=output_dir_input,
                show_progress=False,
            )
            # Создаем выпадающий список для выбора количества потоков для скачивания файлов
            number_threads = gr.Dropdown(
                list(range(1, os.cpu_count() + 1)),
                label='Threads',
                elem_id='number_input'
            )
            number_threads.value = number_threads.choices[0]

        # Создаем строку с кнопкой для запуска скачивания файлов
        with gr.Row():
            text_button = gr.Button("Start download")

        # Создаем аккордеон для отображения результатов скачивания файлов
        with gr.Accordion(
                "Results",
                open=False
        ):
            with gr.Row():
                text_output = gr.Textbox(show_label=False)

        # Создаем строку с кнопкой для открытия папки с сохраненными файлами в проводнике
        with gr.Row():
            open_in_explorer_button = gr.Button("Open in Explorer")

        # Назначаем функцию для обработки нажатия на кнопку "Start download"
        text_button.click(
            download_file,
            inputs=[file_links_input, number_threads, output_dir_input],
            outputs=text_output
        )
        # Назначаем функцию для обработки нажатия на кнопку "Open in Explorer"
        open_in_explorer_button.click(
            open_folder,
            inputs=output_dir_input
        )

if __name__ == "__main__":
    print(gr.__version__)
    print(os.cpu_count())
    print(os.path.expandvars('%userprofile%\downloads'))
    demo.queue().launch()
