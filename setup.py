from setuptools import setup
from os import path

HERE = path.abspath(path.dirname(__file__))
PROJECT = 'sup'

with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

with open(path.join(HERE, PROJECT, 'VERSION'), encoding='utf-8') as f:
    VERSION = f.read().strip()

setup(
    name=PROJECT,
    version=VERSION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=[PROJECT],
    python_requires='>=3.6, <4',
    install_requires=['sanic', 'python-socketio', 'jsonpatch>=1.24'],
    package_data={
        PROJECT: ['VERSION', 'static'],
    },
    entry_points={
        'console_scripts': [
            f'{PROJECT}={PROJECT}:console_entrypoint',
        ],
    },
    project_urls={
        'Bug Reports': f'https://github.com/magao-x/{PROJECT}/issues',
    },
)
