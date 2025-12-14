import bpy
import laspy
import numpy as np
from os import path
from mathutils import Vector
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, CollectionProperty
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

    center_vertically: BoolProperty(
        name="Center Vertically",
        description="Center the imported point cloud vertically (Z axis) at the origin of the scene",
        default=False
    )

    import_as_mesh: BoolProperty(
        name="Import as Mesh",
        description="Import the point cloud as a mesh object, otherwise as point cloud object",
        default=False,
    )

    files : CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    directory : StringProperty(
        subtype='DIR_PATH',
    )

    import_attributes: BoolProperty(
        name="Import Attributes",
        description="Import additional LiDAR attributes",
        default=True,
    )

    def execute(self, context):
        object_list = []
        for file in self.files:
            start = time.time()
            print(f"Importing {file.name}...")  
            filepath = path.join(self.directory, file.name)
            # Read LAS/LAZ file
            with laspy.open(filepath) as infile:
                # Get LAS points
                print(infile.header.x_min * infile.header.x_scale + infile.header.x_offset)
                print(infile.header.y_min * infile.header.y_scale + infile.header.y_offset)
                print(infile.header.z_min * infile.header.z_scale + infile.header.z_offset)
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
            # As Blender python API does not support point cloud creation from script yet,
            # we first create a mesh object and then convert it to point cloud if needed.
            mesh_obj = self.import_points_as_mesh(context, points)

            if self.import_attributes:
                for attr_name, attr_values in attributes.items():
                    attribute = mesh_obj.data.attributes.new(name=attr_name, type="INT", domain="POINT") #TODO: attribute type based on actual data type
                    attribute.data.foreach_set("value", attr_values)

            if not self.import_as_mesh:
                # Convert mesh to point cloud
                with context.temp_override(object=mesh_obj,
                                               active_object=mesh_obj,
                                               selected_objects=[mesh_obj],
                                               selected_editable_objects=[mesh_obj],
                                               mode='OBJECT'): # type: ignore
                    bpy.ops.object.convert(target='POINTCLOUD')

            self.store_header_attributes(infile.header, mesh_obj)

            object_list.append(mesh_obj)
            end = time.time()
            print(f"Imported {file.name} in {end - start:.2f} seconds.")

        if self.center_in_scene:
            self.finalize_centering(object_list)

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

    def store_header_attributes(self, header, object):
        '''
        Stores LAS header attributes in Blender object custom properties.
        
        :param self: the IMPORT_OT_las_data instance
        :param header: LazPy header object
        :param object: Blender object to store attributes in
        '''
        header_attributes = [
            'x_scale', 'y_scale', 'z_scale',
            'x_offset', 'y_offset', 'z_offset',
            'x_min', 'y_min', 'z_min',
            'x_max', 'y_max', 'z_max',
            'file_source_id',
            # 'uuid', UUIDs are not supported in Blender custom properties
            'system_identifier',
            'generating_software',
            # 'creation_date', Date types are not supported in Blender custom properties
            'point_count',
            'start_of_waveform_data_packet_record',
            'start_of_first_evlr',
            'number_of_evlrs',
            'major_version',
            'minor_version',
        ]
        for attr in header_attributes:
            if hasattr(header, attr):
                object[attr] = getattr(header, attr)
    
    def finalize_centering(self, imported_objects):
        '''
        Center imported objects in the scene
        
        :param self: the IMPORT_OT_las_data instance
        :param imported_objects: list of blender objects created during import
        '''
        #We look for min and max in imported objects
        minxs = []
        minys = []
        minzs = []
        maxxs = []
        maxys = []
        maxzs = []
        for obj in imported_objects:
            minxs.append(obj['x_min']* obj['x_scale'] + obj['x_offset'])
            minys.append(obj['y_min']* obj['y_scale'] + obj['y_offset'])
            minzs.append(obj['z_min']* obj['z_scale'] + obj['z_offset'])
            maxxs.append(obj['x_max']* obj['x_scale'] + obj['x_offset'])
            maxys.append(obj['y_max']* obj['y_scale'] + obj['y_offset'])
            maxzs.append(obj['z_max']* obj['z_scale'] + obj['z_offset'])

        minp = Vector((min(minxs), min(minys), min(minzs)))
        maxp = Vector((max(maxxs), max(maxys), max(maxzs)))
        center = (minp + maxp) / 2.0
        if not self.center_vertically:
            center = Vector((center.x, center.y, 0))
        for obj in imported_objects:
            obj.location -= Vector(center)

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