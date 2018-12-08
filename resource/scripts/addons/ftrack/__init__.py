import bpy
import ftrack_connect_blender
import ftrack_api

bl_info = {
	"name": "ftrack",
    "description": "Asset Manager",
    "author": "Lorenzo Angeli, Paolo Acampora",
    "version": (0,0,0),
    "blender": (2,80,0),
    "location": "",
    "category": "Asset Manager"
}


def register():
    print('registering ftrack')


def unregister():
    print('un-registering ftrack')


if __name__ == "__main__":
    register()
