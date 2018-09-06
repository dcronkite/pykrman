import os

import pytest
import requests
from pykrman.pykrfy import get_text


def get_ext_dir(ext):
    ext_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ext
    )
    os.makedirs(ext_dir, exist_ok=True)
    return ext_dir


def download_file(url, fn, ext):
    fp = os.path.join(get_ext_dir(ext), fn)
    if not os.path.exists(fp):
        # stream the request to make sure it works correctly
        # http://stackoverflow.com/a/16696317/564709
        response = requests.get(url, stream=True)
        with open(fp, 'wb') as stream:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    stream.write(chunk)
                    stream.flush()
    return fp


@pytest.fixture
def annual_report_pdf():
    return download_file(
        r'https://openknowledge.worldbank.org/bitstream/handle/10986/16091/9780821399378.pdf',
        'annual-report.pdf',
        'pdf'
    )


@pytest.fixture
def get_tiff1():
    return download_file(
        None,
        'image1.tiff',
        'tiff'
    )


@pytest.fixture
def get_tiff2():
    return download_file(
        None,
        'image2.tiff',
        'tiff'
    )


def test_text_pdf():
    text = get_text(annual_report_pdf(), ext='pdf')
    assert 200000 > len(text) > 100000


def test_tiff():
    text = get_text(get_tiff1(), ext='tiff')
    assert 50 > len(text) > 40
