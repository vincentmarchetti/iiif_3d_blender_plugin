from typing import Set
import bpy
from bpy.types import Collection, Context, Object, Operator

class AddIIIF3DObjProperties(Operator):
    """Add IIIF3D manifest required object properties"""

    bl_idname = "add_obj_properties.iiif_manifest"
    bl_label = "Add IIIF 3D Properties"

    def execute(self, context: Context) -> Set[str]:
        try:
            obj = context.view_layer.objects.active
            print(dir(obj))
            #if not hasattr(obj, "annotation_id"):
            if "annotation_id" not in obj:
                obj["annotation_id"] = obj.name
            if "iiif_source_url" not in obj:
                obj["iiif_source_url"] = "https://example.org/iiif/3d/manifest.json"

            return {"FINISHED"}
        except Exception as e:
            import traceback

            self.report({"ERROR"}, f"Error adding IIIF properties: {str(e)}")
            traceback.print_exc()
            return {"CANCELLED"}

class AddIIIF3DCollProperties(Operator):
    """Add IIIF3D manifest required collection properties"""

    bl_idname = "add_coll_properties.iiif_manifest"
    bl_label = "Add IIIF 3D Properties"

    def execute(self, context: Context) -> Set[str]:
        try:
            coll = context.collection
            if "annotation_id" not in coll:
                coll["annotation_id"] = coll.name
            if "iiif_source_url" not in coll:
                coll["iiif_source_url"] = "https://example.org/iiif/3d/manifest.json"

            return {"FINISHED"}
        except Exception as e:
            import traceback

            self.report({"ERROR"}, f"Error adding IIIF properties: {str(e)}")
            traceback.print_exc()
            return {"CANCELLED"}
