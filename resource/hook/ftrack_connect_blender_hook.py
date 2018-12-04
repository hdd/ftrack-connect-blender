# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
import sys
import pprint
import logging
import re
import os

import ftrack
import ftrack_connect.application


cwd = os.path.dirname(__file__)
dependencies = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
sys.path.append(dependencies)



class LaunchApplicationAction(object):
    '''Discover and launch blender.'''

    identifier = 'ftrack-connect-launch-blender'

    def __init__(self, application_store, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchApplicationAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.application_store = application_store
        self.launcher = launcher

    def is_valid_selection(self, selection):
        '''Return true if the selection is valid.'''
        if (
            len(selection) != 1 or
            selection[0]['entityType'] != 'task'
        ):
            return False

        entity = selection[0]
        task = ftrack.Task(entity['entityId'])

        if task.getObjectType() != 'Task':
            return False

        return True

    def register(self):
        '''Register discover actions on logged in user.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.plugin.debug-information',
            self.get_version_information
        )

    def discover(self, event):
        '''Return discovered applications.'''

        if not self.is_valid_selection(
            event['data'].get('selection', [])
        ):
            return

        items = []
        applications = self.application_store.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            application_identifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'icon': application.get('icon', 'default'),
                'variant': application.get('variant', None),
                'applicationIdentifier': application_identifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        # Prevent further processing by other listeners.
        event.stop()

        if not self.is_valid_selection(
            event['data'].get('selection', [])
        ):
            return

        application_identifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']

        application_identifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(
            application_identifier, context
        )

    def get_version_information(self, event):
        '''Return version information.'''
        return dict(
            name='ftrack connect blender',
            version=ftrack_connect_blender._version.__version__
        )


class ApplicationStore(ftrack_connect.application.ApplicationStore):

    def _checkBlenderLocation(self):
        prefix = None

        blender_location = os.getenv('BELNDER_LOCATION')

        if blender_location and os.path.isdir(blender_location):
            prefix = blender_location.split(os.sep)
            prefix[0] += os.sep

        return prefix

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name version',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        # if sys.platform == 'darwin':
        #     prefix = ['/', 'Applications']
        #     maya_location = self._checkBlenderLocation()
        #     if maya_location:
        #         prefix = maya_location

        #     applications.extend(self._searchFilesystem(
        #         expression=prefix + ['Blender+', 'blender'],
        #         label='Maya',
        #         applicationIdentifier='maya_{version}',
        #         icon='maya',
        #         variant='{version}'
        #     ))

        # elif sys.platform == 'win32':
        #     prefix = ['C:\\', 'Program Files.*']
        #     maya_location = self._checkBlenderLocation()
        #     if maya_location:
        #         prefix = maya_location

        #     applications.extend(self._searchFilesystem(
        #         expression=prefix + ['Autodesk', 'Maya.+', 'bin', 'maya.exe'],
        #         label='Maya',
        #         applicationIdentifier='maya_{version}',
        #         icon='maya',
        #         variant='{version}'
        #     ))

        if 'linux' in sys.platform:
            prefix =  ['/', 'home', 'langeli', 'bin', 'blender', 'blender-2.8-ftrack']
            blender_location = self._checkBlenderLocation()
            if blender_location:
                prefix = blender_location

            print "BLENDER LOCATION", blender_location
            applications.extend(self._searchFilesystem(
                expression=prefix + ['blender$'],
                label='Blender',
                applicationIdentifier='blender_{version}',
                icon='blender',
                variant='{version}'
            ))

        print applications
        
        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):
    '''Custom launcher to modify environment before launch.'''

    def __init__(self, application_store):
        '''.'''
        super(ApplicationLauncher, self).__init__(application_store)

    def _getApplicationEnvironment(
        self, application, context=None
    ):
        '''Override to modify environment before launch.'''

        # Make sure to call super to retrieve original environment
        # which contains the selection and ftrack API.
        environment = super(
            ApplicationLauncher, self
        )._getApplicationEnvironment(application, context)

        entity = context['selection'][0]
        task = ftrack.Task(entity['entityId'])
        taskParent = task.getParent()

        try:
            environment['FS'] = str(int(taskParent.getFrameStart()))
        except Exception:
            environment['FS'] = '1'

        try:
            environment['FE'] = str(int(taskParent.getFrameEnd()))
        except Exception:
            environment['FE'] = '1'

        environment['FTRACK_TASKID'] = task.getId()
        environment['FTRACK_SHOTID'] = task.get('parent_id')

        environment = ftrack_connect.application.appendPath(
            dependencies, 
            'BLENDER_USER_SCRIPTS', 
            environment
        )
        
        environment = ftrack_connect.application.appendPath(
            dependencies, 
            'PYTHONPATH', 
            environment
        )


        return environment


def register(registry, **kw):
    '''Register hooks.'''
    # Validate that registry is the event handler registry. If not,
    # assume that register is being called to regiter Locations or from a new
    # or incompatible API, and return without doing anything.
    if registry is not ftrack.EVENT_HANDLERS:
        return

    print "REGISTERING BLENDER"
    # Create store containing applications.
    application_store = ApplicationStore()

    # Create a launcher with the store containing applications.
    launcher = ApplicationLauncher(
        application_store
    )

    # Create action and register to respond to discover and launch actions.
    action = LaunchApplicationAction(application_store, launcher)
    action.register()