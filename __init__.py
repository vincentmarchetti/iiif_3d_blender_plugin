from bpy.types import (
    TOPBAR_MT_file_export,
    TOPBAR_MT_file_import,
    OBJECT_PT_custom_props,
    COLLECTION_PT_collection_custom_props
)
from bpy.utils import register_class, unregister_class

from .modules.exporter import ExportIIIF3DManifest
from .modules.importer import ImportIIIF3DManifest
from .modules.custom_props import (
    AddIIIF3DObjProperties,
    AddIIIF3DCollProperties,
    IIIF3DObjMetadataPanel,
    IIIF3DCollMetadataPanel
)
from .modules.ui import (
    IIIFManifestPanel,
    register_ui_properties,
    unregister_ui_properties,
)

classes = (
    ImportIIIF3DManifest,
    ExportIIIF3DManifest,
    IIIFManifestPanel,
    AddIIIF3DObjProperties,
    AddIIIF3DCollProperties,
    IIIF3DObjMetadataPanel,
    IIIF3DCollMetadataPanel
)

def menu_func_import(self, context):
    self.layout.operator(
        ImportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )

def menu_func_export(self, context):
    self.layout.operator(
        ExportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )

def register():
    for cls in classes:
        register_class(cls)

    register_ui_properties()

    TOPBAR_MT_file_import.append(menu_func_import)
    TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    TOPBAR_MT_file_import.remove(menu_func_import)
    TOPBAR_MT_file_export.remove(menu_func_export)

    unregister_ui_properties()

    for cls in classes:
        unregister_class(cls)

if __name__ == "__main__":
    try:
        register()
    except Exception as e:
        print(e)
        unregister()
        raise e
