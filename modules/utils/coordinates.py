from mathutils import Vector


class Coordinates:
    """Helper class for converting between IIIF and Blender coordinates
    
    This implementation is intended to be compatible with the conversion
    that is by default carried out when a glTF model is imported with a call 
    such as:
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    The conversion performed internally -- that is, in the coordinates of the 
    points of the mesh as they are stored in Blender data, can be described by the
    relation between the XB, YB, ZB vectors that defined the Blender coordinate system
    and the XI, YI, ZI vectors which define the IIIF coordinate system in IIIF
    
    Those relations are:
    XI =  XB : # the X axis vector is the same in both coordinate systems
    YI =  ZB : # this is the vector which conventionally points UP in each system
    ZI = -YB : # this is the vectors which points "forward"  in the IIIF (and glTF)
               # usage of the term forward, for a humanoid model such as an astronaut
               # this is the conventoional front of the model, the direction in which
               # the astronaut is looking. 
               # Blender however, uses a different semantics of the term forward, in
               # Blender "forward" means the direction in which a defaulte camera or
               # UI viewpoint is looking, in this Blender usage "forward" is +YB
               
    From these relations can derive the relations between xi,yi,zi coordinates in
    IIIF system with xb,yb,zb coordinates in 
    
    in following, dot(A,B) denoted the conventional vector dot-product between
    two 3D vectors A,B
    
    For a vector P interpreted as location of a point in space with Coordinates
    (xi,yi,zi) in IIIF system and (xb,yb,zb) in Blender
    
    xi = dot(P,XI) = dot(P,XB) =   xb
    yi = dot(P,YI) = dot(P,ZB) =   zb
    zi = dot(P,ZI) = dot(P,-YB) = -yb
    
    or in reverse
    xb =  i
    yb = -zi
    zb =  yi
    
    During the import of a IIIF manifest a typical calculation will be to
    convert the (xi,yi,zi) coordinates of a PointSelectore resource into 
    the (xb,yb,zb) coordinated of where to "locate" a mesh in Blender scene.
    
    This is the conversion implemented by function iiif_to_blender
    """

    

    @staticmethod
    def iiif_to_blender(iiif_coords):
        return (iiif_coords[0], -iiif_coords[2], iiif_coords[1])

    @staticmethod
    def blender_to_iiif(blender_coords):
        return (blender_coords[0], blender_coords[2], -blender_coords[1])

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
