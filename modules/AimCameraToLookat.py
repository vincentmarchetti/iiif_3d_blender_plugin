from typing import Set
import mathutils
import math

from .editing.models import  mimetype_from_extension , configure_model, walk_object_tree
from .editing.transforms import Placement , get_object_placement
from .editing.collections import getCameraObject , getPointSelectorObject
from .editing.fileops import path_to_uri

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator


import logging
logger = logging.getLogger("iiif.aim_camera_to_lookat")



            
class AimCameraToLookat(Operator):
    """
    Operator that imports a 3D model into blender
    """

    bl_idname = "iiif.aim_camera_to_lookat"
    bl_label = "Aim Camera to LookAt point"    

        
    def execute(self, context: Context) -> Set[str]:

        annotation_collection = context.collection
        if not annotation_collection.get("iiif_type","") == "Annotation":
            logger.warning("invalid context.collection: %r" % (annotation_collection,))
            return {"CANCELLED"}

        camera =  getCameraObject(annotation_collection)
        if camera is None:
            logger.warning("No camera found in annotation")
            return {"CANCELLED"}
        cameraLocation = get_object_placement(camera).translation.data
        
        lookat = getPointSelectorObject(annotation_collection)
        if lookat is None:
            logger.warning("No PointSelector found in annotation")
            return {"CANCELLED"}
        lookatLocation = get_object_placement(lookat).translation.data
        
        lookDiff = lookatLocation - cameraLocation
        
        logger.info(f"camera {cameraLocation} lookat {lookatLocation} diff {lookDiff}")
        
        if lookDiff.length == 0.0:
            logger.warn("camera and lookAt at same location")
            return {"FINISHED"}
            
        hlength = lookDiff.resized(2).length
        
        angle_x = math.atan2(hlength, -lookDiff.z)
        
        if hlength == 0.0:
            angle_z = 0.0
        else:
            angle_z = math.atan2(-lookDiff.x, lookDiff.y)
        
        euler = mathutils.Euler((angle_x,0.0,angle_z), 'YXZ')
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = euler.to_quaternion()
        return {"FINISHED"}
        