# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import re
import shutil
from pip._internal import main as pip_main

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import setuptools

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')

RESOURCE_PATH = os.path.join(
    ROOT_PATH, 'resource'
)

HOOK_PATH = os.path.join(
    RESOURCE_PATH, 'hook'
)

ADDON_PATH = os.path.join(
    RESOURCE_PATH, 'scripts'
)

BUILD_PATH = os.path.join(
    ROOT_PATH, 'build'
)





# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_blender', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)

STAGING_PATH = os.path.join(
    BUILD_PATH, 'ftrack-connect-blender-{}'.format(VERSION)
)

class BuildPlugin(setuptools.Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy resource files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )
        
        # Copy resource files
        shutil.copytree(
            ADDON_PATH,
            os.path.join(STAGING_PATH, 'scripts')
        )

        pip_main(
            [
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies'),
                '--process-dependency-links'
            ]
        )

        result_path = shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-connect-blender-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )


# Configuration.
setup(
    name='ftrack-connect-blender',
    version=VERSION,
    description='A dialog to publish assets from Maya to ftrack',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://bitbucket.org/efestolab/ftrack-connect-blender',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
    ],
    install_requires=[
        'ftrack-python-api==1.7.0.1',
    ],
    dependency_links=[
        (
            'https://bitbucket.org/ftrack/ftrack-python-api/'
            'get/backlog/ftrack-python-api-compatibility-with-python-3.zip'
            '#egg=ftrack-python-api-1.7.0.1'
        )
    ],
    cmdclass={
        'build_plugin': BuildPlugin
    },
    zip_safe=False
)