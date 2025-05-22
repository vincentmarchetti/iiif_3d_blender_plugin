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

from . import navigation as nav

import math

import logging
logger = logging.getLogger("iiif.export")

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


    def get_base_data(self, iiif_object):
        """
        iiif_object is withe a Blender collection or Blender object
        for which custom properties iiif_id, iiif_type, and iiif_json
        have been defined. Returns a python dict which contains information
        for the json output in Manifest.
        
        Design intent is that client will start with this base_data dict
        and then add and or modify properties which are determined by
        the Blender data structure
        """
        import json
        base_json = iiif_object.get("iiif_json",None)
        if base_json:
            base_data = json.loads( base_json )
        else:
            base_data = dict()
            
        base_data["id"] = iiif_object.get("iiif_id")
        base_data["type"] = iiif_object.get("iiif_type")
        return base_data

    def get_manifest_data(self, manifest_collection: bpy.types.Collection) -> dict:
        manifest_data = self.get_base_data(manifest_collection)
        
        for scene_collection in nav.getScenes(manifest_collection):
            manifest_data["items"].append(self.get_scene_data(scene_collection))
        return manifest_data
        
    def get_scene_data(self, scene_collection: bpy.types.Collection) -> dict:
        scene_data = self.get_base_data(scene_collection)
        
        for page_collection in nav.getAnnotationPages(scene_collection):
            scene_data["items"].append(self.get_annotation_page_data(page_collection))
        return scene_data


    def get_annotation_page_data(self, page_collection: bpy.types.Collection) -> dict:
        page_data = self.get_base_data(page_collection)
        
        for anno_collection in nav.getAnnotations(page_collection):
            page_data["items"].append(self.get_annotation_data(anno_collection))

        
        return page_data

    def get_annotation_data(self, anno_collection ):
        anno_data = self.get_base_data(anno_collection)
         
#        Developer Note:
#        The reason we need to pass the bodyObj into the function
#        to create the target is that in the Prezi 4 API for Scenes,
#        the location of the model in the Scene is represented by
#        a PointSelector-based SpecificResource considered to be
#        a refinement of the target Scene. But in Blender, the location
#        is represented in the data for the Model
        bodyObj = nav.getBodyObject(anno_collection)
        
        anno_data["target"] = self.target_data_for_object(bodyObj, anno_collection)
        
        anno_data["body"]= self.body_data_for_object(bodyObj, anno_collection)

        return anno_data



    def body_data_for_object(self, blender_obj:bpy.types.Object, anno_collection:bpy.types.Collection) -> dict:
        resource_data = self.resource_data_for_object(blender_obj, anno_collection)
        return self.specific_data_for_object(blender_obj, resource_data, anno_collection)

    def resource_data_for_object(self, blender_obj:bpy.types.Object, anno_collection:bpy.types.Collection) -> dict:
        """
        returns the IIIF data for a Model, Camera, Light that is not position or orientation
        description; this would be the body data if no Transform were needed for orientation
        and scale.
        """
        resource_type = blender_obj.get("iiif_type")
        if resource_type == "Model":
            return self.resource_data_for_model(blender_obj, anno_collection)

    def resource_data_for_model(self, blender_obj:bpy.types.Object, anno_collection:bpy.types.Collection) -> dict:
        return self.get_base_data(blender_obj)

    def specific_data_for_object(self, blender_obj:bpy.types.Object, resource_data:dict, anno_collection:bpy.types.Collection ):
        resource_type = blender_obj.get("iiif_type")
        if resource_type == "Model":
            return self.specific_data_for_model(blender_obj, resource_data , anno_collection)
        
    def specific_data_for_model(self, blender_obj:bpy.types.Object, resource_data:dict, anno_collection:bpy.types.Collection ):
        return resource_data
        
        
        
    def target_data_for_object(self, blender_obj:bpy.types.Object, anno_collection:bpy.types.Collection) -> dict:
        if blender_obj.get("iiif_type", None) in ("Model"):
            return self.target_data_for_model(blender_obj, anno_collection )
        else:
            self.warning("invalid object %r in target_data_for_object" % (blender_obj),)
            return {}
        
    def target_data_for_model(self, blender_obj:bpy.types.Object, anno_collection:bpy.types.Collection) -> dict:
        """
        Examines the Blender "location" of the blender_obj and returns a SpecificResource data
        with a PointSelector and source of the enclosing scene
        """  
        ALWAYS_USE_POINTSELECTOR=False
         
        enclosing_scene=nav.getTargetScene(anno_collection)
        scene_ref_data = {
            "id" :   enclosing_scene.get("iiif_id"),
            "type" : enclosing_scene.get("iiif_type")
        }
        
        blender_location = blender_obj.location
        iiif_position = Coordinates.blender_vector_to_iiif_position(blender_location)
        
        if iiif_position != (0.0,0.0,0.0) or ALWAYS_USE_POINTSELECTOR:
            target_data = {
            "type" : "SpecificResource",
            "source" : scene_ref_data,
            "selector" : create_axes_named_values("PointSelector", iiif_position)
            }
        else:
            target_data = scene_ref_data
        return target_data
        



    def execute(self, context: Context) -> Set[str]:
        """Export Blender scene as IIIF manifest"""
        manifests = nav.getManifests()
        
        if manifests:   # that is, not an empty list
            if len(manifests) > 1:
                logger.warning("Multiple manifests not supported")
            manifest_collection=manifests[0]
            manifest_data = self.get_manifest_data(manifest_collection)
        
            # Write manifest
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)
        else:
            logger.warning("No manifest collections identified")

        return {"FINISHED"}
