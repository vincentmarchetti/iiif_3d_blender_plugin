import json
from typing import Set

import bpy
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

    def execute(self, context: Context) -> Set[str]:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)

            self.report({'INFO'}, f"Successfully imported manifest from {self.filepath}")
            self.report({'INFO'}, f"Manifest data: {manifest_data}")

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
