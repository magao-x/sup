from setuptools import setup
from os import path
import os
import setuptools.command.build_py
import distutils.cmd
import distutils.log
import setuptools
import subprocess


HERE = path.abspath(path.dirname(__file__))
PROJECT = 'sup'

with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

with open(path.join(HERE, PROJECT, 'VERSION'), encoding='utf-8') as f:
    VERSION = f.read().strip()


class NpmBuildCommand(distutils.cmd.Command):
    """Build/update the frontend JS/CSS/HTML files and
    place them in the module tree for install"""

    description = 'Build/update the frontend JS/CSS/HTML files'

    def run(self):
        """Run command."""
        frontend_dir = path.join(HERE, 'frontend')
        new_env = os.environ.copy()
        install_command = ['npm', 'install']
        self.announce(f'Running command: {" ".join(install_command)}', level=distutils.log.INFO)
        install_result = subprocess.run(install_command, env=new_env, cwd=frontend_dir)
        install_result.check_returncode()
        build_command = ['npm', 'run', 'build']
        self.announce(f'Running command: {" ".join(build_command)}', level=distutils.log.INFO)
        build_result = subprocess.run(build_command, env=new_env, cwd=frontend_dir)
        build_result.check_returncode()

class BuildPyCommand(setuptools.command.build_py.build_py):
    """Custom build command."""

    def run(self):
        self.run_command('npm_build')
        setuptools.command.build_py.build_py.run(self)

setup(
    cmdclass={
        'npm_build': NpmBuildCommand,
        'build_py': BuildPyCommand,
    },
    name=PROJECT,
    version=VERSION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=[PROJECT],
    python_requires='>=3.6, <4',
    install_requires=[
        'starlette>=0.19.0',
        'uvicorn',
        'orjson>=3.6.7',
        'astroplan>=0.8',
        'uvloop>=0.16',
        'purepyindi2>=0.0.0',
        'xconf>=0.0.0',
        'toml>=0.10.2',
        'websockets>=10.2',
        'blosc>=1.11.1',
        'watchdog>=6.0.0',
        'psutil>=5.9.8,<6',
    ],
    include_package_data=True,
    package_data={
        PROJECT: ['light_path_ex.toml'],  # Ensure this file is included
    },
    entry_points={
        'console_scripts': [
            f'{PROJECT}={PROJECT}.core:WebInterface.run',
        ],
    },
    project_urls={
        'Bug Reports': f'https://github.com/magao-x/{PROJECT}/issues',
    },
)
