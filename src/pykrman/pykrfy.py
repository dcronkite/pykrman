import imghdr
import json
import logging
import os
import shutil
import sys
from io import BytesIO

import pytesseract
import yaml
from PIL import Image
from jsonschema import validate

from pykrman.schema import SCHEMA
from pykrman.util import convert_pdf_to_image, read_pdf


def config_parser(config_fp):
    with open(config_fp) as fh:
        if config_fp.endswith('json'):
            config = json.load(fh)
        elif config_fp.endswith('yaml'):
            config = yaml.load(fh)
        else:
            raise ValueError('Unrecognized config file type. Expected "json" or "yaml".')

    validate(config, SCHEMA)
    run_config(**config)


def collect_input_files(files=None, directories=None, filetypes=None):
    """
    :param files:
    :param directories:
    :param filetypes:
    :return: Generator of files to process
    """
    filetypes = set(filetypes) if filetypes else set()
    for f in files or []:
        yield f
    for d in directories or []:
        for f in os.listdir(d):
            if not filetypes or os.path.splitext(f)[-1] in filetypes:
                yield os.path.join(d, f)


def run_config(data=None, workspace='.', default_ext='pdf', force_convert=True):
    """

    :param default_ext: extension to use for unidentified files
    :param data: see `schema.py`
    :param workspace: directory to do work in
    :return:
    """
    if not data:
        raise ValueError('Need to specify input data.')

    os.makedirs(workspace, exist_ok=True)
    for ifp in collect_input_files(**data):
        p, ext = os.path.splitext(ifp)
        ext = ext[1:]
        name = os.path.basename(p)
        if not ext:
            ext = imghdr.what(ifp) or default_ext
        # cases
        if ext == 'pdf':
            # try to read text
            result = read_pdf(ifp)
            if result:
                with open(os.path.join(workspace, f'{name}.txt'), 'w', encoding='utf8') as out:
                    out.write(result)
                continue
            else:
                # does it have embedded image?
                ofp = os.path.join(workspace, f'{name}.png')
                ofp = convert_pdf_to_image(ifp, ofp, force=force_convert)
        else:
            ofp = os.path.join(workspace, f'{name}.{ext}')
            shutil.copy(ifp, ofp)
            logging.info(f'Doing nothing to: "{ifp}" with extension "{ext}"')
        # convert to text
        if ofp:
            with open(ofp + '.txt', 'w', encoding='utf8') as out:
                out.write(pytesseract.image_to_string(Image.open(ofp)))


def get_text(fp, ext=None, force_convert=True):
    """

    :param force_convert: get text at any cost
    :param ext: extension to use
    :param fp: file-like object containing image or pdf
    :return:
    """
    if ext == 'pdf':
        result = read_pdf(fp)
        if result:
            return result
        # does it have embedded image?
        img = BytesIO()
        convert_pdf_to_image(fp, img, force=force_convert)
    else:
        img = fp
    # convert image to text
    return pytesseract.image_to_string(Image.open(img))


def main():
    if len(sys.argv) <= 1:
        raise ValueError('Missing configuration json or yaml file.')
    else:
        config_parser(sys.argv[1])


if __name__ == '__main__':
    main()
