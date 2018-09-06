from distutils.core import setup
import setuptools

setup(name='pykrman',
      version='0.0.1',
      description='Python Intelligent Character Recognition Manager',
      url='https://bitbucket.org/dcronkite/pykrman',
      author='dcronkite',
      author_email='dcronkite@gmail.com',
      license='MIT',
      classifiers=[  # from https://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3 :: Only',
      ],
      entry_points={
          'console_scripts':
              [
                  'pykrfy = pykrman.pykrfy:main',
              ]
      },
      install_requires=['pytesseract', 'PyPDF2', 'pillow', 'pycronkd',
                        'PyYAML', 'jsonschema', 'pdfminer.six', 'pytest', 'requests'],
      package_dir={'': 'src'},
      packages=setuptools.find_packages('src'),
      zip_safe=False
      )

