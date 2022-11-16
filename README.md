# Python Intelligent Character Recognition Manager

Script for extract text from documents of unknown type. 

## About
Manage ICR/OCR on a variety of inputs, primarily tiff and scanned pdfs.

## Running

## Prerequisites

* Install tesseract: https://github.com/tesseract-ocr/tesseract
* Install ImageMagick: https://imagemagick.org/
* Install this package: `pip install .`

## Run Text Extraction

There are two methods to run:
1. From a separate Python script:
2. 
```python
from pathlib import Path
from pykrman.pykrfy import get_text

path = Path(r'/path/to')
text = get_text(path)
```
2. From command line:
    * Create a config
   
```yaml
data:
  directories:  # or `files` to list specific files
    * /path/to
workspace: /path/to/workspace
```

    * Run `pykrfy config.yaml`

## License
MIT: https://dcronkite.mit-license.org/
