import imghdr
import json
import os
import shutil
import sys
from collections import Counter
from io import BytesIO

import pytesseract
import yaml
from PIL import Image, ImageFilter, ImageEnhance
from jsonschema import validate
from loguru import logger

from pykrman.schema import SCHEMA
from pykrman.util import convert_pdf_to_image, read_pdf
from pykrman.names import FileType


logger.add("output.log", backtrace=True, diagnose=True)


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
    logger.basicConfig(filename='log.txt')
    c = Counter()
    for ifp in collect_input_files(**data):
        ft, success = read_file(ifp, workspace, default_ext, force_convert)
        if success:
            c[ft] += 1


def read_file(ifp, workspace='.', default_ext='pdf', force_convert=True):
    img_dir = os.path.join(workspace, 'out')
    txt_dir = os.path.join(workspace, 'text')
    p, ext = os.path.splitext(ifp)
    name = os.path.basename(p)
    if ext:
        ext = ext[1:]  # remove leading '.'
    else:
        ext = imghdr.what(ifp) or default_ext
    # cases
    if ext == 'pdf':
        # try to read text
        try:
            result = read_pdf(ifp)
        except Exception as e:
            logger.warning(f'Not a pdf: {ifp}, {e}')
            result = None
        if result and len(result) > 20:
            with open(os.path.join(txt_dir, f'{name}.txt'), 'w', encoding='utf8') as out:
                out.write(result)
            return FileType.TEXT_PDF, True
        else:
            # does it have embedded image?
            ofp = os.path.join(img_dir, f'{name}.png')
            try:
                ofp = convert_pdf_to_image(ifp, ofp, force=force_convert)
            except Exception as e:
                logger.info(f'Failed to convert: {name}')
                logger.exception(e)
                return FileType.SCANNED_PDF, False
            ft = FileType.SCANNED_PDF
    else:
        ofp = os.path.join(img_dir, f'{name}.{ext}')
        shutil.copy(ifp, ofp)
        ft = FileType.IMAGE
        logger.info(f'Doing nothing to: "{ifp}" with extension "{ext}"')
    # convert to text
    if ofp:
        try:
            text = convert_to_text(ofp)
        except Exception as e:
            logger.error(f'Failed to extract text: {ifp}, {ofp}')
            logger.exception(e)
            return ft, False
        if text:
            with open(ofp + '.txt', 'w', encoding='utf8') as out:
                out.write(text)
            return ft, True
    return ft, False


def image_to_string(im):
    exc = None
    try:
        return pytesseract.image_to_string(im)
    except Exception as ex:
        logger.exception('pytesseract failed to parse file')
        print(ex)
        exc = ex
    return f'Pytesseract Failed to Parse: {exc}'


def convert_to_text(ofp, ext=None, force_convert=True):
    """

    :param ofp:
    :return:
    """
    if ext == 'pdf' or ofp.endswith('.pdf'):
        result = read_pdf(ofp)
        if result and result.strip():  # one pdf just had "\f\f\f\f\f\f\f"?!?
            return result
        # embedded image?
        im = BytesIO()
        im = convert_pdf_to_image(ofp, im, force=force_convert)
        # im = Image.open(im)
    else:
        try:
            im = Image.open(ofp)
        except Exception as ex:
            logger.exception('PIL failed to open image')
            return str(ex)
    if hasattr(im, 'n_frames'):
        res = []
        for i in range(im.n_frames):  # handle number of frames
            im.seek(i)
            cim = im.convert('RGBA')
            cim = cim.filter(ImageFilter.MedianFilter())
            enhancer = ImageEnhance.Contrast(cim)
            cim = enhancer.enhance(2)
            cim = cim.convert('1')
            try:
                text = image_to_string(cim)
            except Exception as e:
                logger.error(f'frame{i}@{ofp}:{imghdr.what(ofp)}:{type(im)}', exc_info=True)
                continue
            res.append(text)
        return '\n'.join(res)
    else:  # jpeg can't have frames
        cim = im.convert('RGBA')
        cim = cim.filter(ImageFilter.MedianFilter())
        enhancer = ImageEnhance.Contrast(cim)
        cim = enhancer.enhance(2)
        cim = cim.convert('1')
        return image_to_string(cim)


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
    return pytesseract.image_to_string(Image.open(img).convert('RGBA'))


def main():
    if len(sys.argv) <= 1:
        raise ValueError('Missing configuration json or yaml file.')
    else:
        config_parser(sys.argv[1])


if __name__ == '__main__':
    main()
