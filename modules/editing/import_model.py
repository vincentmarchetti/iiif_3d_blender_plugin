import datetime
import os
import urllib.request
from typing import Set

import bpy
from bpy.props import StringProperty
from bpy.types import Collection, Context, Object, Operator
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

from .initialize_collections import initialize_annotation

import math

import logging

logger = logging.getLogger("import-model")


class ImportModel(Operator, ImportHelper):
    """Import IIIF 3D Model"""

    bl_idname = "iiif.import_model"
    bl_label = "Import IIIF Model Resource"

    filename_ext = ""
    filter_glob: StringProperty(  # type: ignore
        default="*.glb;*.gltf", options={"HIDDEN"}
    )
    
    filepath: StringProperty(  # type: ignore
        name="File Path",
        description="Path to the input file",
        maxlen=0,
        subtype="FILE_PATH",
    )

    model_url: StringProperty(  # type: ignore
        name="URL / IIIF id",
        description="URL to external 3D resource",
        maxlen=0,
        subtype="NONE",
    )


    def import_model(self, filepath: str) -> None:
        """Import the model file using the appropriate Blender importer"""
        file_ext = os.path.splitext(filepath)[1].lower()

        if file_ext == ".glb" or file_ext == ".gltf":
            bpy.ops.import_scene.gltf(filepath=filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

        
    def execute(self, context: Context) -> Set[str]:

        annotation_page_collection = context.collection
        if not annotation_page_collection.get("iiif_type","") == "AnnotationPage":
            logger.warning("invalid context.collection: %r" % (annotation_page_collection,))
            return {"CANCELLED"}
            
        if not self.filepath:
            logger.warning("ImportModel.execute : no filepath set" )
            return {"CANCELLED"}
        
        logger.info("call to import model at %s" % self.filepath)
        # logging.getLogger('glTFImporter')
        #storedLevel = logging.getLogger('glTFImporter').level
        #logging.getLogger('glTFImporter').setLevel(logger.level)
        try:
            retCode = bpy.ops.import_scene.gltf(filepath=self.filepath, loglevel=2)
            logger.info("gltf import returned %r" % (retCode,))
        except Exception as exc:
            logger.error("glTF import error", exc)
            return {"FINISHED"}
        #finally:
        #    logging.getLogger('glTFImporter').setLevel(storedLevel)
        
        new_model = bpy.context.active_object
        logger.info("new_model: %r" % (new_model,))
        
        import pathlib
        iiif_id = pathlib.Path(self.filepath).as_uri()
        new_model["iiif_id"] = iiif_id
        
        import os.path
        file_ext = os.path.splitext( self.filepath )[1].lower()
        
        ext_to_mime = {
            ".glb" : "model/gltf-binary",
            ".gltf": "model/gltf+json"
        }
        
        new_model["iiif_format"] = ext_to_mime.get(file_ext, "n/a")
        new_model["iiif_type"] = "Model"
        
        annotation_collection=bpy.data.collections.new("Annotation")
        initialize_annotation( annotation_collection )    
        annotation_page_collection.children.link(annotation_collection) 
        
        if new_model.users_collection:
            for col in new_model.users_collection:
                col.objects.unlink(new_model)
        annotation_collection.objects.link(new_model)       
        
        
        return {"FINISHED"}

            
class ImportLocalModel(ImportModel, ImportHelper):
    bl_idname = "iiif.import_local_model"
    bl_label = "Import local file as model"    
    
    # developer note VM 2025-04-19 : just put this here as a reminder
    # of how UI works with the operator, Not needed for production
    def invoke(self, context, event):
        logger.info("ImportLocalModel.execute entered")
        rv = ImportHelper.invoke(self, context,event)
        return rv

