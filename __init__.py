import datetime
import json
import os
import urllib.request
from typing import Set

import bpy
import mathutils
from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper


class ImportIIIF3DManifest(Operator, ImportHelper):
    """Import IIIF 3D Manifest"""

    bl_idname = "import.iiif_manifest"
    bl_label = "Import IIIF 3D Manifest"

    filename_ext = ".json"
    filter_glob: StringProperty( # type: ignore
        default="*.json",
        options={"HIDDEN"}
    )
    filepath: StringProperty( # type: ignore
        name="File Path",
        description="Path to the input file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    manifest_data: dict

    def download_model(self, url: str) -> str:
        """Download the model file from the given URL"""
        temp_dir = bpy.app.tempdir
        time_string = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        model_name = os.path.basename(url)
        model_extension = os.path.splitext(model_name)[1]
        temp_file = os.path.join(temp_dir, f"temp_model_{time_string}_{model_name}{model_extension}")

        try:
            self.report({'INFO'}, f"Downloading model from {url} to {temp_file}")
            urllib.request.urlretrieve(url, temp_file)
            self.report({'INFO'}, f"Successfully downloaded model to {temp_file}")
            return temp_file
        except Exception as e:
            self.report({'ERROR'}, f"Error downloading model: {str(e)}")
            raise

    def import_model(self, filepath: str) -> None:
        """Import the model file using the appropriate Blender importer"""
        file_ext = os.path.splitext(filepath)[1].lower()

        if file_ext == '.glb' or file_ext == '.gltf':
            bpy.ops.import_scene.gltf(filepath=filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def get_annotation_bounds_center(self, annotation_id: str) -> mathutils.Vector:
        """Calculate the center point of all objects belonging to an annotation"""
        annotation_objects = [obj for obj in bpy.data.objects
                            if obj.get('annotation_id') == annotation_id]

        if not annotation_objects:
            return mathutils.Vector((0, 0, 0))

        # Calculate combined bounds
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')

        for obj in annotation_objects:
            # Get world space corners
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ mathutils.Vector(corner)
                min_x = min(min_x, world_corner.x)
                min_y = min(min_y, world_corner.y)
                min_z = min(min_z, world_corner.z)
                max_x = max(max_x, world_corner.x)
                max_y = max(max_y, world_corner.y)
                max_z = max(max_z, world_corner.z)

        # Calculate center
        center = mathutils.Vector((
            (min_x + max_x) / 2,
            (min_y + max_y) / 2,
            (min_z + max_z) / 2
        ))

        return center

    def create_camera(self, camera_data: dict, parent_collection: bpy.types.Collection) -> bpy.types.Object:
        """Create a camera with the specified parameters"""
        # Create camera data block
        cam_data = bpy.data.cameras.new(name=camera_data.get('label', {}).get('en', ['Camera'])[0])

        # Create camera object
        cam_obj = bpy.data.objects.new(camera_data.get('label', {}).get('en', ['Camera'])[0], cam_data)

        # Link camera to collection
        parent_collection.objects.link(cam_obj)

        # Set camera type (perspective is default in Blender)
        if camera_data.get('type') == 'PerspectiveCamera':
            cam_data.type = 'PERSP'

        return cam_obj

    def position_camera(self, cam_obj: bpy.types.Object, target_data: dict) -> None:
        """Position the camera based on target data"""
        # Get camera position from selector
        selector = target_data.get('selector', [{}])[0]
        if selector.get('type') == 'PointSelector':
            cam_obj.location.x = float(selector.get('x', 0))
            cam_obj.location.y = float(selector.get('z', 0))  # Blender uses Y as up, IIIF uses Z as up
            cam_obj.location.z = float(selector.get('y', 0))

    def set_camera_target(self, cam_obj: bpy.types.Object, look_at_data: dict) -> None:
        """Set the camera's look-at target"""
        if look_at_data.get('type') == 'Annotation':
            # Look at referenced annotation
            target_id = look_at_data.get('id')
            center = self.get_annotation_bounds_center(target_id)
            # Find the object with matching custom property
            for obj in bpy.data.objects:
                if obj.get('annotation_id') == target_id:
                    self.point_camera_at_target(cam_obj, center)
                    break
        elif look_at_data.get('type') == 'PointSelector':
            # Look at specific point
            target_location = (
                float(look_at_data.get('x', 0)),
                float(look_at_data.get('z', 0)),  # Swap Y and Z
                float(look_at_data.get('y', 0))
            )
            self.point_camera_at_target(cam_obj, target_location)

    def point_camera_at_target(self, cam_obj: bpy.types.Object, target_location) -> None:
        """Point the camera at a specific location"""
        direction = target_location - cam_obj.location if \
                    isinstance(target_location, mathutils.Vector) else \
                    mathutils.Vector(target_location) - cam_obj.location

        # Calculate rotation to point at target
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()

    def create_or_get_collection(self, name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
        """Create a new collection or get existing one"""
        if name in bpy.data.collections:
            collection = bpy.data.collections[name]
        else:
            collection = bpy.data.collections.new(name)
            if parent:
                parent.children.link(collection)
            else:
                bpy.context.scene.collection.children.link(collection)

        return collection

    def get_iiif_id_or_label(self, data: dict) -> str:
        """Get the IIIF ID or label from the given data"""
        iiif_id = data.get('id', 'Unnamed ID')
        label = data.get('label', {}).get('en', [iiif_id])[0]
        return label

    def process_annotation_model(self, annotation_data: dict, parent_collection: bpy.types.Collection) -> None:
        # Store the current collection
        previous_collection = bpy.context.view_layer.active_layer_collection.collection

        # Set the parent collection as active
        layer_collection = bpy.context.view_layer.layer_collection
        for child in layer_collection.children:
            if child.collection == parent_collection:
                bpy.context.view_layer.active_layer_collection = child
                break

        model_id = annotation_data.get('body', {}).get('id', None)
        if not model_id:
            self.report({'ERROR'}, "Model ID not found in annotation data")
            return
        self.report({'INFO'}, f"Processing model: {model_id}")
        temp_file = self.download_model(model_id)
        self.import_model(temp_file)

        # Move newly imported objects to the parent collection
        for obj in bpy.context.selected_objects:
            obj['annotation_id'] = annotation_data.get('id')
            if obj.users_collection:  # If it's in any collection
                for col in obj.users_collection:
                    col.objects.unlink(obj)  # Unlink from all other collections
            parent_collection.objects.link(obj)  # Link to our target collection

        # Restore the previous active collection
        for child in layer_collection.children:
            if child.collection == previous_collection:
                bpy.context.view_layer.active_layer_collection = child
                break

    def process_annotation(self, annotation_data: dict, parent_collection: bpy.types.Collection) -> None:
        body = annotation_data.get('body', {})
        if body.get('type') == 'Model':
            self.process_annotation_model(annotation_data, parent_collection)
        elif body.get('type') == 'PerspectiveCamera':
            # Create camera
            cam_obj = self.create_camera(body, parent_collection)

            # Position camera
            target_data = annotation_data.get('target', {})
            self.position_camera(cam_obj, target_data)

            # Set camera target
            look_at_data = body.get('lookAt')
            if look_at_data:
                self.set_camera_target(cam_obj, look_at_data)

            # Store annotation ID
            cam_obj['annotation_id'] = annotation_data.get('id')
        else:
            self.report({'WARNING'}, f"Unknown annotation body type: {body.get('type')}")

    def process_annotation_page(self, annotation_page_data: dict, scene_collection: bpy.types.Collection) -> None:
        page_collection = self.create_or_get_collection(self.get_iiif_id_or_label(annotation_page_data), scene_collection)

        for item in annotation_page_data.get('items', []):
            if item.get('type') == 'Annotation':
                self.process_annotation(item, page_collection)
            else:
                self.report({'WARNING'}, f"Unknown item type: {item.get('type')}")

    def process_scene(self, scene_data: dict) -> None:
        """Process annotation pages in a scene"""
        scene_collection = self.create_or_get_collection(self.get_iiif_id_or_label(scene_data))

        for item in scene_data.get('items', []):
            if item.get('type') == 'AnnotationPage':
                self.process_annotation_page(item, scene_collection)
            elif item.get('type') == 'Annotation':
                self.process_annotation(item, scene_collection)
            else:
                self.report({'WARNING'}, f"Unknown item type: {item.get('type')}")

    def process_manifest(self, manifest_data: dict) -> None:
        """Process the manifest data and import the model"""
        scenes = list()
        for item in manifest_data.get('items', []):
            if item.get('type') == 'Scene':
                scenes.append(item)
            else:
                self.report({'WARNING'}, f"Unknown item type: {item.get('type')}")

        if len(scenes) == 0:
            self.report({'ERROR'}, "No scenes found in manifest")
            return

        for scene in scenes:
            self.process_scene(scene)

    def execute(self, context: Context) -> Set[str]:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.manifest_data = json.load(f)

            self.report({'INFO'}, f"Successfully read manifest from {self.filepath}")
            self.report({'INFO'}, f"Manifest data: {self.manifest_data}")
            self.process_manifest(self.manifest_data)
            self.report({'INFO'}, f"Successfully imported manifest from {self.filepath}")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error reading manifest: {str(e)}")
            return {'CANCELLED'}

class ExportIIIF3DManifest(Operator, ExportHelper):
    """Export scene information as JSON"""

    bl_idname = "export.scene_json"
    bl_label = "Export Scene JSON"

    filename_ext = ".json"
    filter_glob: StringProperty( # type: ignore
        default="*.json",
        options={"HIDDEN"}
    )
    filepath: StringProperty( # type: ignore
        name="File Path",
        description="Path to the output file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    def execute(self, context: Context) -> Set[str]:
        manifest_data = {
            "@context": "http://iiif.io/api/presentation/4/context.json",
            "id": "https://example.org/iiif/3d/model_origin.json",
            "type": "Manifest",
            "label": {"en": ["Example Manifest"]},
            "summary": {"en": ["An example manifest"]},
            "items": [],
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=4)
        except Exception as e:
            self.report({"ERROR"}, f"Error writing JSON file: {str(e)}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Successfully exported JSON to {self.filepath}")
        return {"FINISHED"}

def menu_func_import(self, context):
    self.layout.operator(
        ImportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )

def menu_func_export(self, context):
    self.layout.operator(
        ExportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )


def register():
    bpy.utils.register_class(ImportIIIF3DManifest)
    bpy.utils.register_class(ExportIIIF3DManifest)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportIIIF3DManifest)
    bpy.utils.unregister_class(ExportIIIF3DManifest)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
