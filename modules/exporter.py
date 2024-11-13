import json
from typing import Set

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ExportHelper

from .metadata import IIIFMetadata
from .utils.color import rgba_to_hex


class ExportIIIF3DManifest(Operator, ExportHelper):
    """Export IIIF 3D Manifest"""

    bl_idname = "export_scene.iiif_manifest"
    bl_label = "Export IIIF 3D Manifest"

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

    def get_scene_data(self, context: Context, collection: bpy.types.Collection) -> dict | None:
        """Get scene data from metadata or create new"""
        metadata = IIIFMetadata(collection)
        scene_data = metadata.get_scene()

        if scene_data:
            # Only update background color if it was originally present
            if "backgroundColor" in scene_data and context.scene.world and context.scene.world.use_nodes:
                background_node = context.scene.world.node_tree.nodes.get("Background")
                if background_node:
                    color = background_node.inputs[0].default_value
                    scene_data["backgroundColor"] = rgba_to_hex(color)

            # Replace existing annotation page or add new one
            annotation_page = self.get_annotation_page(scene_data, collection)

            # Replace or add items array
            if 'items' not in scene_data:
                scene_data['items'] = []

            # Update existing annotation page or add new one
            found = False
            for i, item in enumerate(scene_data['items']):
                if item.get('type') == 'AnnotationPage':
                    scene_data['items'][i] = annotation_page
                    found = True
                    break

            if not found:
                scene_data['items'].append(annotation_page)

            return scene_data
        return None

    def get_manifest_data(self, context: Context) -> dict:
        """Get manifest data from metadata or create new"""
        scene = context.scene

        # Fallback to new manifest
        fallback_manifest = {
            "@context": "http://iiif.io/api/presentation/4/context.json",
            "id": getattr(scene, "iiif_manifest_id"),
            "type": "Manifest",
            "label": {"en": [getattr(scene, "iiif_manifest_label")]},
            "summary": {"en": [getattr(scene, "iiif_manifest_summary")]},
            "items": []
        }

        for collection in bpy.data.collections:
            metadata = IIIFMetadata(collection)
            manifest_data = metadata.get_manifest()
            if manifest_data:
                # Merge existing manifest on top of fallback manifest
                merged_manifest = {**fallback_manifest, **manifest_data}
                merged_manifest["items"] = []  # Clear items to rebuild
                merged_manifest["id"] = getattr(scene, "iiif_manifest_id")
                merged_manifest["label"] = {
                    **merged_manifest["label"],
                    "en": [getattr(scene, "iiif_manifest_label")]
                }
                merged_manifest["summary"] = {
                    **merged_manifest["summary"],
                    "en": [getattr(scene, "iiif_manifest_summary")]
                }
                return merged_manifest

        return fallback_manifest

    def get_model_annotation(self, obj: bpy.types.Object) -> dict:
        """Get annotation data from metadata or create new"""
        metadata = IIIFMetadata(obj)
        annotation_data = metadata.get_annotation()

        if annotation_data:
            return annotation_data

        # Fall back to new annotation
        return {
            "id": f"https://example.org/iiif/3d/anno_{obj.name}",
            "type": "Annotation",
            "motivation": ["painting"],
            "body": {
                "id": obj.get('iiif_source_url', f"local://models/{obj.name}"),
                "type": "Model"
            },
            "target": "https://example.org/iiif/scene1/page/p1/1"
        }

    def get_annotation_page(self, scene_data: dict, collection: bpy.types.Collection) -> dict:
        """Build annotation page for a scene"""
        # Get the first annotation page from scene data if it exists
        existing_pages = [item for item in scene_data.get('items', [])
                         if item.get('type') == 'AnnotationPage']

        page_id = (existing_pages[0].get('id') if existing_pages
                   else f"{scene_data['id']}/annotations")

        annotation_page = {
            "id": page_id,
            "type": "AnnotationPage",
            "items": []
        }

        # Look for objects in the collection and its children
        def process_collection(col):
            for obj in col.objects:
                if obj.type in {'MESH', 'CAMERA'}:  # Include both mesh and camera objects
                    metadata = IIIFMetadata(obj)
                    anno_data = metadata.get_annotation()

                    if anno_data:
                        self.report({'INFO'}, f"Found annotation data for {obj.name}: {anno_data}")
                        annotation_page["items"].append(anno_data)

            # Process child collections recursively
            for child in col.children:
                process_collection(child)

        process_collection(collection)
        return annotation_page

    def execute(self, context: Context) -> Set[str]:
        """Export scene as IIIF manifest"""
        manifest_data = self.get_manifest_data(context)

        # Process scenes
        for collection in bpy.data.collections:
            scene_data = self.get_scene_data(context, collection)
            if scene_data:
                manifest_data["items"].append(scene_data)

        # Write manifest
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return {"FINISHED"}
