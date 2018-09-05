import io
import logging
import os
import struct

import PyPDF2
from PIL import Image
from cronkd.util.lists import defaultlist


def convert_pdf_to_image(ifp, ofp, force=True):
    """

    :param ifp:
    :param ofp:
    :param force: ensure that some image is obtained
    :return:
    """
    try:
        images = get_images_from_scanned_pdf(ifp)
    except PyPDF2.utils.PdfReadError:
        images = None
    if images:
        merge_images(images, out=ofp)
    else:
        logging.warning(f'Failed to parse scanned pdf: "{ifp}"')
        if force:
            logging.warning(f'Forcing conversion of scanned pdf.')
            ofp = os.path.splitext(ofp)[0] + '.force' + os.path.splitext(ofp)[-1]
            if not force_pdf_to_image(ifp, ofp):
                return None
    return ofp


def tiff_header_for_ccitt(width, height, img_size, ccitt_group=4):
    tiff_header_struct = '<' + '2s' + 'h' + 'l' + 'h' + 'hhll' * 8 + 'h'
    return struct.pack(tiff_header_struct,
                       b'II',  # Byte order indication: Little indian
                       42,  # Version number (always 42)
                       8,  # Offset to first IFD
                       8,  # Number of tags in IFD
                       256, 4, 1, width,  # ImageWidth, LONG, 1, width
                       257, 4, 1, height,  # ImageLength, LONG, 1, lenght
                       258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
                       259, 3, 1, ccitt_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
                       262, 3, 1, 0,  # Threshholding, SHORT, 1, 0 = WhiteIsZero
                       273, 4, 1, struct.calcsize(tiff_header_struct),  # StripOffsets, LONG, 1, len of header
                       278, 4, 1, height,  # RowsPerStrip, LONG, 1, lenght
                       279, 4, 1, img_size,  # StripByteCounts, LONG, 1, size of image
                       0  # last IFD
                       )


def get_images_from_scanned_pdf(pdf_filepath):
    """
    Built for collecting images from a pdf produced by scanning,
    so it assumes that all images contribute to a single image.

    :param pdf_filepath: path to pdf file
    :return:
    """
    with open(pdf_filepath, 'rb') as pdf_file:
        cond_scan_reader = PyPDF2.PdfFileReader(pdf_file)
        images = defaultlist()  # images not read in correct order
        for i in range(0, cond_scan_reader.getNumPages()):
            page = cond_scan_reader.getPage(i)
            x_object = page['/Resources']['/XObject'].getObject()
            for obj in x_object:
                if x_object[obj]['/Subtype'] == '/Image':
                    """
                    The  CCITTFaxDecode filter decodes image data that has been encoded using
                    either Group 3 or Group 4 CCITT facsimile (fax) encoding. CCITT encoding is
                    designed to achieve efficient compression of monochrome (1 bit per pixel) image
                    data at relatively low resolutions, and so is useful only for bitmap image data, not
                    for color images, grayscale images, or general data.
    
                    K < 0 --- Pure two-dimensional encoding (Group 4)
                    K = 0 --- Pure one-dimensional encoding (Group 3, 1-D)
                    K > 0 --- Mixed one- and two-dimensional encoding (Group 3, 2-D)
                    """
                    if x_object[obj]['/Filter'] == '/CCITTFaxDecode':
                        if x_object[obj]['/DecodeParms']['/K'] == -1:
                            ccitt_group = 4
                        else:
                            ccitt_group = 3
                        width = x_object[obj]['/Width']
                        height = x_object[obj]['/Height']
                        data = x_object[obj]._data  # sorry, getData() does not work for CCITTFaxDecode
                        img_size = len(data)
                        tiff_header = tiff_header_for_ccitt(width, height, img_size, ccitt_group)
                        images[int(obj[3:])] = Image.open(io.BytesIO(tiff_header + data))
                    elif x_object[obj]['/Filter'] == '/DCTDecode':
                        data = x_object[obj]._data  # jpg
                        images[int(obj[3:])] = Image.open(io.BytesIO(data))
                    elif x_object[obj]['/Filter'] == '/JPXDecode':
                        data = x_object[obj]._data  # jp2
                        images[int(obj[3:])] = Image.open(io.BytesIO(data))
    return images


def merge_images(images, horizontal=False, out=None):
    if horizontal:
        width = sum(x.size[0] for x in images if x)
        height = max(x.size[1] for x in images if x)
    else:
        width = max(x.size[0] for x in images if x)
        height = sum(x.size[1] for x in images if x)
    result = Image.new('RGB', (width, height))
    prev = 0
    for im in images:
        if not im:
            continue
        if horizontal:
            result.paste(im=im, box=(prev, 0))
            prev += im.size[0]  # add width
        else:
            result.paste(im=im, box=(0, prev))
            prev += im.size[1]  # add height
    if out:
        result.save(out)
    return result


def force_pdf_to_image(pdf, outfile):
    """
    Uses ImageMagick to convert pdf file into an image. The quality
        of the image will be poor, but at least there will be an image.

    :param outfile:
    :param pdf: path to pdf file
    :return: PythonMagick Image
    """
    try:
        from PythonMagick import Image as PMImage
    except ImportError:
        logging.exception('PythonMagick library not detected.')
        logging.warning('Unable to convert pdf to image: {}'.format(pdf))
        return None

    if 'MAGICK_HOME' not in os.environ:
        logging.exception('PythonMagick environment variable not set.')
        logging.warning('Set MAGICK_HOME to something like "C:\Program Files\ImageMagick-x.y.z-w."')
        logging.warning('Unable to convert pdf to image: {}'.format(pdf))
        return None

    img = PMImage(outfile)
    img.write(outfile)
    return True