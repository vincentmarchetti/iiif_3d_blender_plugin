import json
import math
from bpy.types import Object
from mathutils import Quaternion

from typing import List

from . import generate_id
from ..utils.json_patterns import force_as_singleton
from ..editing.transforms import Transform, Rotation, Placement, transformsToPlacements

import logging
logger = logging.getLogger("iiif.cameras")
logger.setLevel(logging.INFO)

def configure_pointselector(    new_pointselector : Object,                                                 
                                resource_data : dict,
                                placement : Placement ) -> None:
    if len(resource_data) == 0:
        resource_data = _initial_data()
        resource_data["id"]=generate_id(resource_data["type"])

    new_pointselector["iiif_type"] = resource_data["type"]
    new_pointselector["iiif_json"] = json.dumps(resource_data)
    
    new_pointselector.location = placement.translation.data
        
    

def _initial_data() -> dict :
    return {
        "id" : None,
        "type": "PointSelector"
    }