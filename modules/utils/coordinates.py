from mathutils import Vector


class Coordinates:
    """Helper class for converting between IIIF and Blender coordinates."""

    # TODO: Implement conversion methods

    @staticmethod
    def iiif_to_blender(iiif_coords):
        return (iiif_coords[0], iiif_coords[1], iiif_coords[2])

    @staticmethod
    def blender_to_iiif(blender_coords):
        return (blender_coords[0], blender_coords[1], blender_coords[2])

    @staticmethod
    def get_iiif_coords_from_pointselector(selector: dict) -> Vector:
        return Vector((
            float(selector.get('x', 0)),
            float(selector.get('y', 0)),
            float(selector.get('z', 0))
        ))

    @staticmethod
    def convert_to_vector(coords: dict | tuple[float, float, float] | Vector) -> Vector:
        if isinstance(coords, dict):
            return Coordinates.get_iiif_coords_from_pointselector(coords)
        return Vector(coords)
