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


class ParcelBuildCommand(distutils.cmd.Command):
    """Build/update the frontend JS/CSS/HTML files and
    place them in the module tree for install"""

    description = 'Build/update the frontend JS/CSS/HTML files'
    user_options = [
        # The format is (long option, short option, description).
        ('node-env=', None, 'Build JS for either "development" or "production" by supplying this option'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        # Each user option must be listed here with their default value.
        self.node_env = os.environ.get('NODE_ENV', 'development')

    def finalize_options(self):
        """Post-process options."""
        if self.node_env not in ('production', 'development'):
            raise RuntimeError("--node-env= / $NODE_ENV must be 'production' or 'development' for this step")

    def run(self):
        """Run command."""
        frontend_dir = path.join(HERE, 'frontend')
        new_env = os.environ.copy()
        new_env['NODE_ENV'] = self.node_env
        install_command = ['yarn', 'install']
        self.announce(f'Running command: {" ".join(install_command)}', level=distutils.log.INFO)
        install_result = subprocess.run(install_command, env=new_env, cwd=frontend_dir)
        install_result.check_returncode()
        build_command = ['yarn', 'parcel', 'build', '-d', '../sup/static/', 'index.html']
        self.announce(f'Running command: {" ".join(build_command)}', level=distutils.log.INFO)
        build_result = subprocess.run(build_command, env=new_env, cwd=frontend_dir)
        build_result.check_returncode()

class BuildPyCommand(setuptools.command.build_py.build_py):
    """Custom build command."""

    def run(self):
        self.run_command('parcel_build')
        setuptools.command.build_py.build_py.run(self)

setup(
    cmdclass={
        'parcel_build': ParcelBuildCommand,
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
        'uvicorn>=0.17.5,<0.18',
        'aiohttp>=3.8.1,<4',
        'aiodns>=3.0.0,<4',
        'aiortc>=1.3.1',
        'orjson>=3.6.7',
        'astroplan>=0.8',
        'matplotlib>=3.5.1',
        'uvloop>=0.16',
        'purepyindi2>=0.0.0',
        'toml>=0.10.2',
        'websockets>=10.2',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            f'{PROJECT}={PROJECT}:core.console_entrypoint',
            f'shmim_watcher={PROJECT}.shmim:shmim_grabber',
            f'shmim_coordinator={PROJECT}.shmim:shmim_coordinator',
        ],
    },
    project_urls={
        'Bug Reports': f'https://github.com/magao-x/{PROJECT}/issues',
    },
)
