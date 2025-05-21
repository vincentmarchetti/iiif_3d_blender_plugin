import logging
logger=logging.getLogger("iiif.init")

from bpy.types import TOPBAR_MT_file_export, TOPBAR_MT_file_import,OUTLINER_MT_collection_new, OUTLINER_MT_collection 
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

class ManifestSubMenu( bpy.types.Menu):
    """
    intent is that this menu will be added to the popup
    menu associated with any Blender bpy.type.Collection
    which has an iiif_type property value of AnnotationPage
    """
    bl_label="Manifest Editing"
    bl_idname="iiif.manifest_submenu"
    
    def draw(self,context):
        layout = self.layout
        target_collection = context.collection
        layout.operator("import_scene.import_model", text="Add Model")
        
        """
        operators for adding a camera and light will be added
        """

def menu_func_manifest_submenu(self,context):
    target_collection = context.collection
    if target_collection.get("iiif_type","") == "AnnotationPage":
        self.layout.menu(ManifestSubMenu.bl_idname, text="Edit Manifest") 

classes = (
    ImportIIIF3DManifest,
    ExportIIIF3DManifest,
    ImportIIIFModel,
    IIIFManifestPanel,
    AddIIIF3DObjProperties,
    AddIIIF3DCollProperties,
    IIIF3DObjMetadataPanel,
    IIIF3DCollMetadataPanel,
    NewManifest,
    ManifestSubMenu
)

def menu_func_import(self, context):
    self.layout.operator(
        ImportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )

def menu_func_export(self, context):
    self.layout.operator(
        ExportIIIF3DManifest.bl_idname, text="IIIF 3D Manifest (.json)"
    )
    
    
def menu_func_new_manifest(self, context):
    self.layout.operator(
        NewManifest.bl_idname, text="New IIIF Manifest"
    )
    
def register():
    for cls in classes:
        register_class(cls)

    register_ui_properties()

    TOPBAR_MT_file_import.append(menu_func_import)
    TOPBAR_MT_file_export.append(menu_func_export)
    
    OUTLINER_MT_collection_new.append(menu_func_new_manifest)
    
    OUTLINER_MT_collection.append(menu_func_manifest_submenu)

def unregister():
    TOPBAR_MT_file_import.remove(menu_func_import)
    TOPBAR_MT_file_export.remove(menu_func_export)
    
    OUTLINER_MT_collection_new.remove(menu_func_new_manifest)
    
    OUTLINER_MT_collection.append(menu_func_manifest_submenu)

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
