from bpy.types import TOPBAR_MT_file_export, TOPBAR_MT_file_import
from bpy.utils import register_class, unregister_class

from .modules.exporter import ExportIIIF3DManifest
from .modules.importer import ImportIIIF3DManifest
from .modules.import_model import ImportIIIFModel
from .modules.new_manifest import NewManifest

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
    ImportIIIFModel,
    IIIFManifestPanel,
    AddIIIF3DObjProperties,
    AddIIIF3DCollProperties,
    IIIF3DObjMetadataPanel,
    IIIF3DCollMetadataPanel,
    NewManifest
)

def menu_func_import(self, context):
    self.layout.operator(
        ImportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )

def menu_func_export(self, context):
    self.layout.operator(
        ExportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )
    
def menu_func_add_model(self, context):
    self.layout.operator(
        ImportIIIFModel.bl_idname, text="Import IIIF Model"
    )
        
    

def register():
    for cls in classes:
        register_class(cls)

    register_ui_properties()

    TOPBAR_MT_file_import.append(menu_func_import)
    TOPBAR_MT_file_export.append(menu_func_export)
    TOPBAR_MT_file_import.append(menu_func_add_model)

def unregister():
    TOPBAR_MT_file_import.remove(menu_func_import)
    TOPBAR_MT_file_export.remove(menu_func_export)
    TOPBAR_MT_file_import.remove(menu_func_add_model)

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
