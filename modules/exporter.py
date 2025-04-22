import json
from typing import Set

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ExportHelper

from .metadata import IIIFMetadata
from .utils.color import hex_to_rgba
from .utils.coordinates import Coordinates
from .utils.json_patterns import (
    force_as_object,
    force_as_singleton,
    force_as_list,
    axes_named_values,
    create_axes_named_values,
    get_source_resource
)

import math

import logging
logger = logging.getLogger("export")

class ExportIIIF3DManifest(Operator, ExportHelper):
    """Export IIIF 3D Manifest"""

    bl_idname = "export_scene.iiif_manifest"
    bl_label = "Export IIIF 3D Manifest"

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

    def get_scene_data(self, context: Context, collection: bpy.types.Collection) -> dict | None:
        """Get scene data from metadata or create new
           Collection should be the Blender Collection corresponding to the IIIF Scene
        """
        # sanity check
        iiif_type = collection.get("iiif_type", None)
        if  iiif_type.lower() == "Scene".lower():
            scene_id = collection.get("iiif_id",None)
            if not scene_id:
                logger.warning("invalid id for exporting scene %r" % (scene_id,))
            else:
                logger.info("creating json data for IIIF scene %s" % scene_id )
        else:
            logger.warning("invalid collection passed to get_scene_data : %r" % (iiif_type,))
            
        metadata = IIIFMetadata(collection)
        scene_data = metadata.get_scene()
        
        

        if scene_data:
            # Only update background color if it was originally present
            if "backgroundColor" in scene_data and context.scene.world and context.scene.world.use_nodes:
                background_node = context.scene.world.node_tree.nodes.get("Background")
                if background_node:
                    color = background_node.inputs[0].default_value
                    scene_data["backgroundColor"] = rgba_to_hex(color)

            # Replace existing annotation page or add new one
            annotation_page = self.get_annotation_page(scene_data, collection)

            # Replace or add items array
            if 'items' not in scene_data:
                scene_data['items'] = []

            # Update existing annotation page or add new one
            found = False
            for i, item in enumerate(scene_data['items']):
                if item.get('type').lower() == 'AnnotationPage'.lower():
                    scene_data['items'][i] = annotation_page
                    found = True
                    break

            if not found:
                scene_data['items'].append(annotation_page)

            return scene_data
        return None

    def get_manifest_data(self, context: Context) -> dict:
        """Get manifest data from metadata or create new"""
        scene = context.scene

        # Fallback to new manifest
        fallback_manifest = {
            "@context": "http://iiif.io/api/presentation/4/context.json",
            "id": getattr(scene, "iiif_manifest_id"),
            "type": "Manifest",
            "label": {"en": [getattr(scene, "iiif_manifest_label")]},
            "summary": {"en": [getattr(scene, "iiif_manifest_summary")]},
            "items": []
        }

        for collection in bpy.data.collections:
            metadata = IIIFMetadata(collection)
            manifest_data = metadata.get_manifest()
            if manifest_data:
                # Merge existing manifest on top of fallback manifest
                merged_manifest = {**fallback_manifest, **manifest_data}
                merged_manifest["items"] = []  # Clear items to rebuild
                merged_manifest["id"] = getattr(scene, "iiif_manifest_id")
                merged_manifest["label"] = {
                    **merged_manifest["label"],
                    "en": [getattr(scene, "iiif_manifest_label")]
                }
                merged_manifest["summary"] = {
                    **merged_manifest["summary"],
                    "en": [getattr(scene, "iiif_manifest_summary")]
                }
                return merged_manifest

        return fallback_manifest

    def get_light_annotation(self, obj: bpy.types.Object) -> dict:
        """Get annotation data for a light object"""
        light = obj.data

        # Use original IDs if available
        annotation_id = obj.get('original_annotation_id', f"https://example.org/iiif/3d/light_{obj.name}")
        body_id = obj.get('original_body_id', f"https://example.org/iiif/3d/lights/{obj.name}")

        if light.type == 'SUN':
            light_type = 'DirectionalLight'
        else:
            light_type = 'AmbientLight'

        annotation = {
            "id": annotation_id,
            "type": "Annotation",
            "motivation": ["painting"],
            "body": {
                "id": body_id,
                "type": light_type,
                "label": {"en": [obj.name]},
            }
        }

        # Add color if not default
        if obj.get('original_color'):
            annotation["body"]["color"] = rgba_to_hex((*light.color, 1.0)).upper()  # Force uppercase for hex values

        # Add intensity if not default
        original_intensity = obj.get('original_intensity')
        if original_intensity:
            try:
                annotation["body"]["intensity"] = json.loads(original_intensity)
            except json.JSONDecodeError:
                self.report({'WARNING'}, f"Could not decode intensity data for {obj.name}")

        original_lookAt = obj.get('original_lookAt')
        if original_lookAt:
            try:
                annotation["body"]["lookAt"] = json.loads(original_lookAt)
            except json.JSONDecodeError:
                self.report({'WARNING'}, f"Could not decode lookAt data for {obj.name}")

        original_target = obj.get('original_target')
        if original_target:
            try:
                annotation["target"] = json.loads(original_target)
            except json.JSONDecodeError:
                self.report({'WARNING'}, f"Could not decode target data for {obj.name}")

        return annotation

    def get_model_annotation(self, obj: bpy.types.Object) -> dict:
        """Get annotation data from metadata or create new"""
        metadata = IIIFMetadata(obj)
        annotation_data = metadata.get_annotation()

        if annotation_data:
            return annotation_data

        # Fall back to new annotation
        return {
            "id": f"https://example.org/iiif/3d/anno_{obj.name}",
            "type": "Annotation",
            "motivation": ["painting"],
            "body": {
                "id": obj.get('iiif_source_url', f"local://models/{obj.name}"),
                "type": "Model"
            },
            "target": "https://example.org/iiif/scene1/page/p1/1"
        }
        
    def new_camera_annotation(self, blender_camera: bpy.types.Object ) -> dict:
        camera_data = {
            "id" : f"https://example.org/iiif/3d/camera_{blender_camera.name}",
            "type" : "PerspectiveCamera"
        }
        
        annotation_data = {
            "id" : f"https://example.org/iiif/3d/anno_{blender_camera.name}",
            "type" : "Annotation",
            "motivation" : ["painting"],            
        }
        
        annotation_data["target"] = {
            "id" : "https://example.org/iiif/scene1/page/p1/1",
            "type" : "Scene"
        }
        
        annotation_data["body"] = camera_data
        return annotation_data

        
    def new_model_annotation(self, blender_model: bpy.types.Object ) -> dict: 
        
        model_id = blender_model.get("iiif_id", "https://example.com/model_id_unknown")
        model_format = blender_model.get("iiif_format", "application/binary")
        
        model_data = {
            "id" : model_id,
            "type" : "Model",
            "format" : model_format
        }
        
        annotation_data = {
            "id" : f"https://example.org/iiif/3d/anno_{blender_model.name}",
            "type" : "Annotation",
            "motivation" : ["painting"],            
        }
        
        annotation_data["target"] = {
            "id" : "https://example.org/iiif/scene1/page/p1/1",
            "type" : "Scene"
        }
        
        annotation_data["body"] = camera_data
        return annotation_data
    
    def get_camera_annotation(self, blender_camera: bpy.types.Object, scene_collection: bpy.types.Collection ) -> dict:
        """Get annotation data from metadata or create new"""
        metadata = IIIFMetadata(blender_camera)
        annotation_data = metadata.get_annotation()
        
        if annotation_data is None:
            annotation_data = self.new_camera_annotation(blender_camera)
        

        try:
            saved_mode = blender_camera.rotation_mode
            blender_camera.rotation_mode = "QUATERNION"
            quat = blender_camera.rotation_quaternion
            blender_camera.rotation_mode = saved_mode
            vec  = blender_camera.location
            
            iiif_rotation = Coordinates.blender_rotation_to_camera_transform_angles(quat)
            iiif_position = Coordinates.blender_vector_to_iiif_position(vec)
            logger.info("iiif: position: %r  rotation %r" % (iiif_position, iiif_rotation ))
        except Exception as exc:
            logger.exception("failed camera ", exc)

        target = force_as_object(force_as_singleton(annotation_data.get("target")))
        target_source = get_source_resource( target )
        target_source["id"] = scene_collection.get("iiif_id", "https://example.com/not_available")
        
        body = force_as_singleton(annotation_data.get("body"))
        iiif_camera = get_source_resource( body )
        
        # this will remove a camera "lookAt" property if it exists
        old_lookAt = iiif_camera.pop("lookAt", None)
        
        blender_y_angle = blender_camera.data.angle_y
        logger.info("blender vertical FoV %.3e radians" % blender_y_angle)
        iiif_camera["fieldOfView"] =  math.degrees(blender_y_angle)
        
        annotation_data["body"] = {
            "type" : "SpecificResource",
            "source" : iiif_camera,
            "transform" : [create_axes_named_values("RotateTransform", iiif_rotation)]
        }
             
        annotation_data["target"]= {
            "type" : "SpecificResource",
            "source" : target_source,
            "selector" : create_axes_named_values("PointSelector", iiif_position)
        }           

        return annotation_data
        
    def get_model_annotation(self, blender_model: bpy.types.Object, scene_collection: bpy.types.Collection ) -> dict:
        """Get annotation data from metadata or create new"""
        metadata = IIIFMetadata(blender_model)
        annotation_data = metadata.get_annotation()
        
        if annotation_data is None:
            annotation_data = self.new_model_annotation(blender_model)
        

        try:
            saved_mode = blender_model.rotation_mode
            blender_model.rotation_mode = "QUATERNION"
            quat = blender_model.rotation_quaternion
            blender_model.rotation_mode = saved_mode
            vec  = blender_model.location
            scale_vector = blender_model.scale
            
            iiif_rotation = Coordinates.blender_rotation_to_model_transform_angles (quat)
            iiif_position = Coordinates.blender_vector_to_iiif_position(vec)
            logger.info("iiif: position: %r  rotation %r" % (iiif_position, iiif_rotation ))
        except Exception as exc:
            logger.exception("failed model ", exc)

        target = force_as_object(force_as_singleton(annotation_data.get("target")))
        target_source = get_source_resource( target )
        target_source["id"] = scene_collection.get("iiif_id", "https://example.com/not_available")
        
        if  iiif_position  == (0.0, 0.0,0.0):
            new_target = target_source
        else:
            new_target= {
                            "type" : "SpecificResource",
                            "source" : target_source,
                            "selector" : create_axes_named_values("PointSelector", iiif_position)
                        }
        annotation_data["target"]   = new_target 
                      
        body = force_as_singleton(annotation_data.get("body"))
        iiif_model = get_source_resource( body )

        iiif_transforms = list()
        if scale_vector.to_tuple() != (1.0 , 1.0, 1.0):
            iiif_transforms.append( create_axes_named_values("ScaleTransform", scale_vector.to_tuple()))
        if  iiif_rotation != (0.0, 0.0, 0.0):
            iiif_transforms.append( create_axes_named_values("RotateTransform", iiif_rotation ))
        
        if len(iiif_transforms) == 0:
            new_body =  iiif_model
        else:
            new_body = {
                "type" : "SpecificResource",
                "source" : iiif_model,
                "transform" : iiif_transforms
            }
        annotation_data["body"] = new_body
             
        return annotation_data


    def get_annotation_page(self, scene_data: dict, scene_collection: bpy.types.Collection) -> dict:
        """Build annotation page for a scene"""
        # Get the first annotation page from scene data if it exists
        existing_pages = [item for item in scene_data.get('items', [])
                         if item.get('type') == 'AnnotationPage']

        page_id = (existing_pages[0].get('id') if existing_pages
                   else f"{scene_data['id']}/annotations")

        annotation_page = {
            "id": page_id,
            "type": "AnnotationPage",
            "items": []
        }

        # Look for objects in the collection and its children
        def process_collection(col):
            for obj in col.objects:
                if obj.type == 'MESH':
                    anno_data = self.get_model_annotation( obj, scene_collection )
                    if anno_data:
                        annotation_page["items"].append(anno_data)
                elif obj.type == 'LIGHT':
                    annotation_page["items"].append(self.get_light_annotation(obj))
                elif obj.type == 'CAMERA':
                    anno_data = self.get_camera_annotation(obj, scene_collection)
                    if anno_data:
                        annotation_page["items"].append(anno_data)

            # Process child collections recursively
            for child in col.children:
                process_collection(child)

        process_collection(scene_collection)
        return annotation_page

    def execute(self, context: Context) -> Set[str]:
        """Export scene as IIIF manifest"""
        manifest_data = self.get_manifest_data(context)

        # Process scenes
        for collection in bpy.data.collections:            
            if collection.get("iiif_type",None).lower() == "Scene".lower():
                scene_data = self.get_scene_data(context, collection)
                if scene_data:
                    manifest_data["items"].append(scene_data)

        # Write manifest
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return {"FINISHED"}
