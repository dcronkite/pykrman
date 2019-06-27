import os
import shutil
import subprocess
import sys

from pytesseract import pytesseract


RESOURCE_PATH = os.path.abspath(__file__).split('src')[0] + 'res'
JAVA_PATH = r'H:\exe\java\openjdk-12.0.1_windows-x64_bin\jdk-12.0.1\bin'


def pdfs_to_text(d):
    cmd = f'{JAVA_PATH}/java -jar {RESOURCE_PATH}/pdfbox-app-2.0.15.jar ExtractImages {{pdf}}'
    for fo in os.scandir(d):
        if fo.is_file() and fo.name.endswith('.pdf'):
            outdir = os.path.splitext(fo.path)[0]
            os.makedirs(outdir, exist_ok=True)
            shutil.copy(fo.path, outdir)
            dest = os.path.join(outdir, fo.name)
            os.chdir(outdir)
            p = subprocess.Popen(cmd.format(pdf=dest), cwd=outdir)
            p.communicate()
            os.remove(dest)
            images_to_text(outdir, f'{outdir}.txt')


def images_to_text(d, ofp):
    with open(ofp, 'w', encoding='utf8') as out:
        for fn in sorted(os.listdir(d), key=lambda x: int(x.split('.')[0].split('-')[-1])):
            s = pytesseract.image_to_string(os.path.join(d, fn))
            out.write(s + '\n')


if __name__ == '__main__':
    pdfs_to_text(sys.argv[1])
