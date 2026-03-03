from typing import Set
import mathutils
import math

from .editing.models import  mimetype_from_extension , configure_model, walk_object_tree
from .editing.transforms import Placement , get_object_placement
from .editing.collections import getCameraObject , getPointSelectorObject
from .editing.fileops import path_to_uri
from .editing.pointselectors import configure_pointselector

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator


import logging
logger = logging.getLogger("iiif.new_lookat")



            
class NewLookAt(Operator):
    """
    Operator that imports a 3D model into blender
    """

    bl_idname = "iiif.new_lookat"
    bl_label = "Add LookAt for Camera"    

        
    def execute(self, context: Context) -> Set[str]:

        annotation_collection = context.collection
        if not annotation_collection.get("iiif_type","") == "Annotation":
            logger.warning("invalid context.collection: %r" % (annotation_collection,))
            return {"CANCELLED"}

        camera =  getCameraObject(annotation_collection)
        if camera is None:
            logger.warning("No camera found in annotation")
            return {"CANCELLED"}
        cameraPlacement = get_object_placement(camera)
        
        lookat = getPointSelectorObject(annotation_collection)
        if lookat is not None:
            logger.warning("PointSelector already in annotation")
            return {"CANCELLED"}
            
        
        # https://docs.blender.org/api/current/bpy.ops.object.html
        try:
            retCode = bpy.ops.object.empty_add()
            logger.info("obj.empty_add %r" % (retCode,))
        except Exception as exc:
            logger.error("add empty error", exc)
            return {"FINISHED"}
        
        new_pointselector = bpy.context.active_object
        if new_pointselector is not None:
            
            placement:Placement = Placement(translation = cameraPlacement.translation)
            configure_pointselector(    new_pointselector,
                                        {},
                                        placement)
            new_pointselector.name = "%s/pointselector" % annotation_collection.name 
            move_object_into_collection(new_pointselector, annotation_collection)
                                        
            
        
        return {"FINISHED"}
