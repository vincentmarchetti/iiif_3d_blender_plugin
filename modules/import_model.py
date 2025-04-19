import datetime
import os
import urllib.request
from typing import Set

import bpy
from bpy.props import StringProperty
from bpy.types import Collection, Context, Object, Operator
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

import math

import logging

logger = logging.getLogger("import-model")


class ImportIIIFModel(Operator, ImportHelper):
    """Import IIIF 3D Model"""

    bl_idname = "import_scene.import_model"
    bl_label = "Import IIIF Model Resource"

    filename_ext = ""
    filter_glob: StringProperty(  # type: ignore
        default="*.glb;*.gltf", options={"HIDDEN"}
    )
    filepath: StringProperty(  # type: ignore
        name="File Path",
        description="Path to the input file",
        maxlen=1024,
        subtype="FILE_PATH",
    )



    def import_model(self, filepath: str) -> None:
        """Import the model file using the appropriate Blender importer"""
        file_ext = os.path.splitext(filepath)[1].lower()

        if file_ext == ".glb" or file_ext == ".gltf":
            bpy.ops.import_scene.gltf(filepath=filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    # developer note VM 2025-04-19 : just put this here as a reminder
    # of how UI works with the operator, Not needed for production
    def invoke(self, context, event):
        logger.debug("ImportIIIFModel.execute entered")
        rv = ImportHelper.invoke(self, context,event)
        return rv
        
    def execute(self, context: Context) -> Set[str]:
        try:
            if not self.filepath:
                logger.warning("ImportIIIFModel.execute : no filepath set" )
                return {"CANCELLED"}
            
            logger.info("call to import model at %s" % self.filepath)
            # logging.getLogger('glTFImporter')
            storedLevel = logging.getLogger('glTFImporter').level
            logging.getLogger('glTFImporter').setLevel(logger.level)
            try:
                retCode = bpy.ops.import_scene.gltf(filepath=self.filepath, loglevel=2)
                logger.info("gltf import returned %r" % (retCode,))
            except Exception as exc:
                logger.error("glTF import error", exc)
                return {"FINISHED"}
            finally:
                logging.getLogger('glTFImporter').setLevel(storedLevel)

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
            
            
            return {"FINISHED"}
        except Exception as e:
            import traceback

            self.report({"ERROR"}, f"Error reading model: {str(e)}")
            traceback.print_exc()
            return {"CANCELLED"}
