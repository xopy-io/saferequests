import os
import sys

from codecs import open

from setuptools import find_packages, setup, Command

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'saferequests', '__version__.py'),
          'r',
          'utf-8') as f:
    exec(f.read(), about)
with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()


packages = ['saferequests']
requires  = ['requests>=2.10.0']
setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=packages,
    package_data={'': ['LICENSE', 'NOTICE']},
    package_dir={'saferequests': 'saferequests'},
    include_package_data=True,
    python_requires=">=3.5",
    install_requires=requires,
    license=about['__license__'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
        ]
    )
