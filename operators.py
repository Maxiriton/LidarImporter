import bpy
import laspy
import numpy as np
from mathutils import Vector
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
import time

# List of additional LiDAR attributes to import.
# This is based on attributes found in french LIDAR-HD files 
ATTRIBUTE_LIST = [
    'intensity',
    'return',
    'number_of_return',
    'classification',
    'classification_flags',
    'scanner_channel',
    'scan_direction',
    'flight_line_edge',
    'user_data',
    'angle',
    'point_source_id',
    'gps_time_type',
]

def get_attribute(header, attr_name, default="N/A"):
    if hasattr(header, attr_name):
        return str(getattr(header, attr_name))
    else:
        return default
    

class IMPORT_OT_las_data(Operator, ImportHelper): # type: ignore
    bl_idname = "import_scene.las_data"
    bl_label = "Import LAS/LAZ data"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(default="*.las;*.laz", options={'HIDDEN'})
    center_in_scene: BoolProperty(
        name="Center in Scene",
        description="Center the imported point cloud at the origin of the scene",
        default=True,
    )
    import_as_mesh: BoolProperty(
        name="Import as Mesh",
        description="Import the point cloud as a mesh object, otherwise as point cloud object",
        default=False,
    )

    import_attributes: BoolProperty(
        name="Import Attributes",
        description="Import additional LiDAR attributes",
        default=True,
    )

    def execute(self, context):
        # Read LAS/LAZ file
        with laspy.open(self.filepath) as infile:
            # Get LAS points
            num_points_to_read = infile.header.point_count
            all_points = infile.read_points(n=num_points_to_read)

            x_coords = np.array(all_points.x) * infile.header.x_scale + infile.header.x_offset
            y_coords = np.array(all_points.y) * infile.header.y_scale + infile.header.y_offset
            z_coords = np.array(all_points.z) * infile.header.z_scale + infile.header.z_offset
            points = np.column_stack((x_coords, y_coords, z_coords))

            attributes = {}
            if self.import_attributes:
                for attr in ATTRIBUTE_LIST:
                    if hasattr(all_points, attr):
                        attributes[attr] = np.array(getattr(all_points, attr))


        # Import LAS points as a mesh
        mesh_obj = self.import_points_as_mesh(context, points)

        # Center the imported object in the scene
        if self.center_in_scene:
            #TODO : perhaps we shouldn't center on the Z axis and center only on X and Y.
            bbox_corners = np.array([mesh_obj.matrix_world @ Vector(corner) for corner in mesh_obj.bound_box])
            max = np.max(bbox_corners, axis=0)
            min = np.min(bbox_corners, axis=0)
            center = (max + min) / 2
            mesh_obj.location -= Vector(center)

        if self.import_attributes:
            start = time.time()
            # Store attributes in custom properties
            for attr_name, attr_values in attributes.items():
                # Convert numpy array to list for Blender property storage
                attribute = mesh_obj.data.attributes.new(name=attr_name, type="INT", domain="POINT")
                attribute.data.foreach_set("value", attr_values)
            end = time.time()
            print(f"Time taken to import attributes: {end - start:.2f} seconds")

        if not self.import_as_mesh:
            # Convert mesh to point cloud
            with context.temp_override(object=mesh_obj,
                                           active_object=mesh_obj,
                                           selected_objects=[mesh_obj],
                                           selected_editable_objects=[mesh_obj],
                                           mode='OBJECT'): # type: ignore
                bpy.ops.object.convert(target='POINTCLOUD')

        return {'FINISHED'}

    def import_points_as_mesh(self, context, points) -> bpy.types.Object:
        # Create a new mesh object
        mesh = bpy.data.meshes.new(bpy.path.basename(self.filepath))
        obj = bpy.data.objects.new(bpy.path.basename(self.filepath), mesh)

        # Link the mesh to the scene
        context.collection.objects.link(obj)
    
        # Create mesh vertices from points
        mesh.from_pydata(points, [], [])
        # Update mesh
        mesh.update()
        return obj


def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_las_data.bl_idname, text="LAS/LAZ data (.las, .laz)")

### Registration
classes = (
    IMPORT_OT_las_data,
)

def register():
    for cl in classes:
        bpy.utils.register_class(cl)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    for cl in reversed(classes):
        bpy.utils.unregister_class(cl)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)