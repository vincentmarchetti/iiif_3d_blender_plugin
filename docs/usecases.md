# Use cases

Below are a number of usecases that we hope to fulfill with the development of the IIIF Blender plugin:

1. Content creator starting from scratch
 * I am a content creator and I want to produce a simple 3D IIIF scene manifest document describing 4 3D models in context with a camera.
 * I am not a 3D specialist.
 * I do not have a IIIF manifest document to start with.
 * I have 4 model GLTF assets of objects
 * I want to position my objects relative to each other.
 * I want to scale my objects relative to each other.
 * I want to customize camera position relative to my objects.
 * I want the produced scene to look the same in Blender and in my downstream IIIF viewer.

2. Content creator editing a manifest
* I am a content creator and I want to modify an existing IIIF 3D scene to move objects and alter lighting.
* I am not a 3D specialist.
* I do have a pre-existing IIIF manifest to start with..
* From an imported scene, I want to re-position objects relative to each other.
* From an imported scene, I want to modify existing lights and add new lighting.
* I want the produced scene to look the same in Blender and in my downstream IIIF viewer.

3. 3D specialist
* I am a 3D specialist and/or developer who wants to use Blender interactively as part of a suite of multiple tools to add 3D annotations to an existing IIIF 3D scene. 
* I do have a pre-existing IIIF manifest to start with, and I want to import it into Blender.
* I will not use Blender to export a scene manifest at the end. 
* I want to use Blender to verify exact positions, scales, and rotations of objects in the scene. 
* I want to use Blender to "pick points" from the scene interactively. I will later use these picked coordinate points to apply annotations in non-Blender software (whether by modifying scene manifest JSON directly or using a secondary tool to apply annotations). 
* I am familiar with the differences across 3D frameworks and applications. 
* I want my imported Scene to conform to the actual IIIF axes - i.e., I want my objects in Blender to exist in "Y-up" configuration.

## Principles

Discussing these usecases we developed the following principles:

* That this is not a complete solution for realizing Blender scenes in IIIF, that Blender supports many features WebGL and IIIF will not.
* The emphasis across all use cases should be on positioning, transforming, and setting properties for models, cameras, and lights, while realizing that the way Blender renders scenes is likely to be different than the way WebGL renders scenes (with respect to lighting, materials, etc.).
* We should think of this tool as another IIIF implementation - here, implementing the ability to view IIIF manifests within Blender, use some (not all) Blender tools to edit contents of manifests, and export manifests that include (some but not all) content editable within Blender so that this content can be viewed in other applications.
