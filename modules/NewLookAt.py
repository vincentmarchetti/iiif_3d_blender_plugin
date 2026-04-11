from typing import Set
from mathutils import Vector

from .editing.transforms import Placement , get_object_placement, Translation
from .editing.collections import getCameraObject , getPointSelectorObject, move_object_into_collection
from .editing.pointselectors import configure_pointselector

import bpy
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
        
        if annotation_collection is None:
            logger.warning("annotation_collection is None")
            return {"CANCELLED"}  
            
        if  annotation_collection is not None and \
            annotation_collection.get("iiif_type","") != "Annotation":
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
            # the orginal direction of camera
            camera_direction : Vector = Vector( (0.0,0.0,-1.0))
            camera_direction.rotate(cameraPlacement.rotation.data)
            lookat_distance = 10.0
            lookat_location: Vector = cameraPlacement.translation.data + \
                                      lookat_distance * camera_direction
            
            
            placement:Placement = Placement(translation = Translation(lookat_location))
            configure_pointselector(    new_pointselector,
                                        {},
                                        placement)
            new_pointselector.name = "%s/pointselector" % annotation_collection.name 
            move_object_into_collection(new_pointselector, annotation_collection)
        
        return {"FINISHED"}
