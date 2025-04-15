import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

import json
import sys
import os
from typing import Any, Dict, List, Tuple, Callable
import subprocess
import bpy
import difflib

# Ensure the script receives the correct number of arguments
if len(sys.argv) < 4:
    print(
        "Usage: blender --background --python run_blender_with_plugin.py -- <input_manifest>"
    )
    sys.exit(1)

# Get the input and output manifest file paths from the command line arguments
input_manifest = sys.argv[sys.argv.index("--") + 1]
output_manifest = input_manifest.replace(".json", "_export.json")

context = bpy.context
if context is None:
    print("Failed to get the Blender context")
    sys.exit(1)


def get_extension_id():
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "blender_manifest.toml")
        with open(manifest_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("id = "):
                    # Extract the value between quotes
                    return line.split("=")[1].strip().strip('"').strip("'")
    except Exception as e:
        print(f"Error reading blender_manifest.toml: {e}")
        sys.exit(1)
    print("Could not find id in blender_manifest.toml")
    sys.exit(1)


# Load the plugin
needle = get_extension_id()
logger.debug("needle is %s" % (needle,))
ext_name = None
logger.debug("addons.keys is %s" % ( "\n".join( context.preferences.addons.keys()),))
for key in context.preferences.addons.keys():
    if needle in key:
        ext_name = key
        logger.debug("ext_name is %s" % (ext_name,))
        break

if not ext_name:
    print("Failed to find the plugin")
    sys.exit(1)

bpy.ops.preferences.addon_enable(module=ext_name)



if ext_name not in context.preferences.addons:
    print("Failed to load the plugin")
    sys.exit(1)


def safe_delete(file_path):
    try:
        # Check if file exists before attempting deletion
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} has been deleted successfully")
        else:
            print(f"File {file_path} does not exist")
    except Exception as e:
        print(f"Error occurred while deleting file: {e}")


RED: Callable[[str], str] = lambda text: f"\u001b[31m{text}\033\u001b[0m"
GREEN: Callable[[str], str] = lambda text: f"\u001b[32m{text}\033\u001b[0m"


def get_edits_string(old: str, new: str) -> Tuple[str, bool]:
    result = ""

    lines = difflib.ndiff(old.splitlines(keepends=True), new.splitlines(keepends=True))

    has_changes = False

    for line in lines:
        line = line.rstrip()
        if line.startswith("+"):
            has_changes = True
            result += GREEN(line) + "\n"
        elif line.startswith("-"):
            has_changes = True
            result += RED(line) + "\n"
        elif line.startswith("?"):
            continue
        else:
            result += line + "\n"

    return (result, has_changes)


def get_json_diff(file1_path: str, file2_path: str) -> Tuple[str, bool]:
    with open(file1_path) as f1:
        json1 = json.load(f1)
    with open(file2_path) as f2:
        json2 = json.load(f2)
    return get_edits_string(
        json.dumps(json1, indent=2, sort_keys=True),
        json.dumps(json2, indent=2, sort_keys=True),
    )


def get_indent(level):
    return "  " * level


def print_object_hierarchy(obj, level):
    indent = get_indent(level)
    print(f"{indent}- {obj.name} ({obj.type})")

    for child in obj.children:
        print_object_hierarchy(child, level + 1)


def print_collection_hierarchy(collection, level=0):
    indent = get_indent(level)
    print(f"{indent}{collection.name} (Collection):")

    for obj in collection.objects:
        if not obj.parent:
            print_object_hierarchy(obj, level + 1)

    for child_col in collection.children:
        print_collection_hierarchy(child_col, level + 1)


bpy.ops.import_scene.iiif_manifest(filepath=input_manifest)

print("\n\nPrinting scene hierarchy:")
print_collection_hierarchy(bpy.context.scene.collection)
print("\n\n")

bpy.ops.export_scene.iiif_manifest(filepath=output_manifest)

differences, has_changes = get_json_diff(input_manifest, output_manifest)

# Delete output manifest
safe_delete(output_manifest)

if has_changes:
    print("Imported manifest differs from exported manifest:")
    print(differences)
    sys.exit(1)
else:
    print("Imported manifest equals exported manifest")
    sys.exit(0)
