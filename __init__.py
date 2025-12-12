# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Lidar Importer",
    "author": "Henri Hebeisen",
    "description": "Easily import and visualize Lidar point cloud data in Blender.",
    "blender": (4, 5, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty

from . import operators
# from . import ui

classes = (
    # Variant_prefs,
)

addon_modules = (
    operators,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for mod in addon_modules:
        mod.register()

def unregister():
    for mod in reversed(addon_modules):
        mod.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
