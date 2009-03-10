#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "grid3D.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  
 # ###################################################################
 ##

__docformat__ = 'restructuredtext'

from fipy.tools import numerix

from fipy.meshes.numMesh.mesh import Mesh
from fipy.tools import vector
from fipy.tools.dimensions.physicalField import PhysicalField


class Grid3D(Mesh):
    """
    3D rectangular-prism Mesh

    X axis runs from left to right.
    Y axis runs from bottom to top.
    Z axis runs from front to back.

    Numbering System:

    Vertices: Numbered in the usual way. X coordinate changes most quickly, then Y, then Z.

    Cells: Same numbering system as vertices.

    Faces: XY faces numbered first, then XZ faces, then YZ faces. Within each subcategory, it is numbered in the usual way.
    """
    def __init__(self, dx = 1., dy = 1., dz = 1., nx = None, ny = None, nz = None):
        self.nx = nx
        self.ny = ny
        self.nz = nz
        
        self.dx = PhysicalField(value = dx)
        scale = PhysicalField(value = 1, unit = self.dx.getUnit())
        self.dx /= scale
        
        self.nx = self._calcNumPts(d = self.dx, n = nx, axis = "x")
        
        self.dy = PhysicalField(value = dy)
        if self.dy.getUnit().isDimensionless():
            self.dy = dy
        else:
            self.dy /= scale

        self.ny = self._calcNumPts(d = self.dy, n = ny, axis = "y")
        
        self.dz = PhysicalField(value = dz)
        if self.dz.getUnit().isDimensionless():
            self.dz = dz
        else:
            self.dz /= scale
        
        self.nz = self._calcNumPts(d = self.dz, n = nz, axis = "z")
        
        self.numberOfVertices = (self.nx + 1) * (self.ny + 1) * (self.nz + 1)
        
        vertices = self._createVertices()
        faces = self._createFaces()
        cells = self._createCells()
        Mesh.__init__(self, vertices, faces, cells)
        
        self.setScale(value = scale)
        
    def __repr__(self):
        return "%s(dx=%s, dy=%s, dz=%s, nx=%d, ny=%d, nz=%d)" \
            % (self.__class__.__name__, `self.dx`, `self.dy`, `self.dz`, self.nx, self.ny, self.nz)

    def _createVertices(self):
        x = self._calcVertexCoordinates(self.dx, self.nx)
        x = numerix.resize(x, (self.numberOfVertices,))
        
        y = self._calcVertexCoordinates(self.dy, self.ny)
        y = numerix.repeat(y, self.nx + 1)
        y = numerix.resize(y, (self.numberOfVertices,))
        
        z = self._calcVertexCoordinates(d = self.dz, n = self.nz)
        z = numerix.repeat(z, (self.nx + 1) * (self.ny + 1))
        
        return numerix.array((x, y, z))
    
    def _createFaces(self):
        """
        XY faces are first, then XZ faces, then YZ faces
        """
        ## do the XY faces
        v1 = numerix.arange((self.nx + 1) * (self.ny))
        v1 = vector.prune(v1, self.nx + 1, self.nx)
        v1 = self._repeatWithOffset(v1, (self.nx + 1) * (self.ny + 1), self.nz + 1) 
        v2 = v1 + 1
        v3 = v1 + (self.nx + 2)
        v4 = v1 + (self.nx + 1)
        XYFaces = numerix.array((v1, v2, v3, v4))

        ## do the XZ faces
        v1 = numerix.arange((self.nx + 1) * (self.ny + 1))
        v1 = vector.prune(v1, self.nx + 1, self.nx)
        v1 = self._repeatWithOffset(v1, (self.nx + 1) * (self.ny + 1), self.nz)
        v2 = v1 + 1
        v3 = v1 + ((self.nx + 1)*(self.ny + 1)) + 1
        v4 = v1 + ((self.nx + 1)*(self.ny + 1))
        XZFaces = numerix.array((v1, v2, v3, v4))
        
        ## do the YZ faces
        v1 = numerix.arange((self.nx + 1) * self.ny)
        v1 = self._repeatWithOffset(v1, (self.nx + 1) * (self.ny + 1), self.nz)
        v2 = v1 + (self.nx + 1)
        v3 = v1 + ((self.nx + 1)*(self.ny + 1)) + (self.nx + 1)                                  
        v4 = v1 + ((self.nx + 1)*(self.ny + 1))
        YZFaces = numerix.array((v1, v2, v3, v4))

        ## reverse some of the face orientations to obtain the correct normals
        ##tmp = horizontalFaces.copy()
        ##horizontalFaces[:self.nx, 0] = tmp[:self.nx, 1]
        ##horizontalFaces[:self.nx, 1] = tmp[:self.nx, 0]
        ##tmp = verticalFaces.copy()
        ##verticalFaces[:, 0] = tmp[:, 1]
        ##verticalFaces[:, 1] = tmp[:, 0]
        ##verticalFaces[::(self.nx + 1), 0] = tmp[::(self.nx + 1), 0]
        ##verticalFaces[::(self.nx + 1), 1] = tmp[::(self.nx + 1), 1]

        self.numberOfXYFaces = (self.nx * self.ny * (self.nz + 1))
        self.numberOfXZFaces = (self.nx * (self.ny + 1) * self.nz)
        self.numberOfYZFaces = ((self.nx + 1) * self.ny * self.nz)
        self.numberOfFaces = self.numberOfXYFaces + self.numberOfXZFaces + self.numberOfYZFaces
        
        return numerix.concatenate((XYFaces, XZFaces, YZFaces), axis=1)
    
    def _createCells(self):
        """
        cells = (front face, back face, left face, right face, bottom face, top face)
        front and back faces are YZ faces
        left and right faces are XZ faces
        top and bottom faces are XY faces
        """
        self.numberOfCells = self.nx * self.ny * self.nz
        
        ## front and back faces
        frontFaces = numerix.arange(self.numberOfYZFaces)
        frontFaces = vector.prune(frontFaces, self.nx + 1, self.nx)
        frontFaces = frontFaces + self.numberOfXYFaces + self.numberOfXZFaces
        backFaces = frontFaces + 1

        ## left and right faces
        leftFaces = numerix.arange(self.nx * self.ny)
        leftFaces = self._repeatWithOffset(leftFaces, self.nx * (self.ny + 1), self.nz)
        leftFaces = numerix.ravel(leftFaces)
        leftFaces = leftFaces + self.numberOfXYFaces
        rightFaces = leftFaces + self.nx

        ## bottom and top faces
        bottomFaces = numerix.arange(self.nx * self.ny * self.nz)
        topFaces = bottomFaces + (self.nx * self.ny)

        return numerix.array((frontFaces, backFaces, leftFaces, rightFaces, bottomFaces, topFaces))
         
    def getScale(self):
        return self.scale['length']
        
    def getPhysicalShape(self):
        """Return physical dimensions of Grid3D.
        """
        return PhysicalField(value = (self.nx * self.dx * self.getScale(), self.ny * self.dy * self.getScale(), self.nz * self.dz * self.getScale()))

    def _getMeshSpacing(self):
        return numerix.array((self.dx, self.dy, self.dz))[...,numerix.newaxis]
    
    def getShape(self):
        return (self.nx, self.ny, self.nz)

    def _repeatWithOffset(self, array, offset, reps):
        a = numerix.fromfunction(lambda rnum, x: array + (offset * rnum), (reps, numerix.size(array))).astype('l')
        return numerix.ravel(a)

## The following method is broken when dx, dy or dz are not scalar. Simpler to use the generic
## _calcFaceAreas rather than do the required type checking, resizing and outer product.
##
##     def _calcFaceAreas(self):
##         XYFaceAreas = numerix.ones(self.numberOfXYFaces)
##         XYFaceAreas = XYFaceAreas * self.dx * self.dy
##         XZFaceAreas = numerix.ones(self.numberOfXZFaces)
##         XZFaceAreas = XZFaceAreas * self.dx * self.dz        
##         YZFaceAreas = numerix.ones(self.numberOfYZFaces)
##         YZFaceAreas = YZFaceAreas * self.dy * self.dz
##         self.faceAreas =  numerix.concatenate((XYFaceAreas, XZFaceAreas, YZFaceAreas))

    def _calcFaceNormals(self):
        XYFaceNormals = numerix.zeros((3, self.numberOfXYFaces))
        XYFaceNormals[2, (self.nx * self.ny):] = 1
        XYFaceNormals[2, :(self.nx * self.ny)] = -1
        XZFaceNormals = numerix.zeros((3, self.numberOfXZFaces))
        xzd = numerix.arange(self.numberOfXZFaces)
        xzd = xzd % (self.nx * (self.ny + 1))
        xzd = (xzd < self.nx)
        xzd = 1 - (2 * xzd)
        XZFaceNormals[1, :] = xzd
        YZFaceNormals = numerix.zeros((3, self.numberOfYZFaces))
        YZFaceNormals[0, :] = 1
        YZFaceNormals[0, ::self.nx + 1] = -1
        self.faceNormals = numerix.concatenate((XYFaceNormals, 
                                                XZFaceNormals, 
                                                YZFaceNormals), 
                                               axis=-1)
        
    def _calcFaceTangents(self):
        ## need to see whether order matters.
        faceTangents1 = numerix.zeros((3, self.numberOfFaces), 'd')
        faceTangents2 = numerix.zeros((3, self.numberOfFaces), 'd')
        ## XY faces
        faceTangents1[0, :self.numberOfXYFaces] = 1.
        faceTangents2[1, :self.numberOfXYFaces] = 1.
        ## XZ faces
        faceTangents1[0, self.numberOfXYFaces:self.numberOfXYFaces + self.numberOfXZFaces] = 1.
        faceTangents2[2, self.numberOfXYFaces:self.numberOfXYFaces + self.numberOfXZFaces] = 1.
        ## YZ faces
        faceTangents1[1, self.numberOfXYFaces + self.numberOfXZFaces:] = 1.
        faceTangents2[2, self.numberOfXYFaces + self.numberOfXZFaces:] = 1.
        self.faceTangents1 = faceTangents1
        self.faceTangents2 = faceTangents2

    def _calcHigherOrderScalings(self):
        self.scale['area'] = self.scale['length']**2
        self.scale['volume'] = self.scale['length']**3

    def _isOrthogonal(self):
        return True
        
## pickling

    def __getstate__(self):
        dict = {
            'dx' : self.dx,            
            'dy' : self.dy,
            'dz' : self.dz,
            'nx' : self.nx,
            'ny' : self.ny,
            'nz' : self.nz
            }
        return dict

    def __setstate__(self, dict):
        self.__init__(dx = dict['dx'], dy = dict['dy'], dz = dict['dz'], nx = dict['nx'], ny = dict['ny'], nz = dict['nz'])


    def _test(self):
        """
        These tests are not useful as documentation, but are here to ensure
        everything works as expected.
        
            >>> dx = 0.5
            >>> dy = 2.
            >>> dz = 4.
            >>> nx = 3
            >>> ny = 2
            >>> nz = 1
            
            >>> mesh = Grid3D(nx = nx, ny = ny, nz = nz, dx = dx, dy = dy, dz = dz)
            
            >>> print mesh._getAdjacentCellIDs()
            (array([0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 1, 2, 0, 1, 2, 3, 4, 5, 0, 0,
                   1, 2, 3, 3, 4, 5]), array([0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 3, 4, 5, 0, 1,
                   2, 2, 3, 4, 5, 5]))

            >>> vertices = numerix.array(((0., 1., 2., 3., 0., 1., 2., 3., 0., 1., 2., 3., 
            ...                            0., 1., 2., 3., 0., 1., 2., 3., 0., 1., 2., 3.),
            ...                           (0., 0., 0., 0., 1., 1., 1., 1., 2., 2., 2., 2.,
            ...                            0., 0., 0., 0., 1., 1., 1., 1., 2., 2., 2., 2.),
            ...                           (0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
            ...                            1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.)))
            >>> vertices *= numerix.array([[dx], [dy], [dz]])
            
            >>> numerix.allequal(vertices, mesh._createVertices())
            1
        
            >>> faces = numerix.array(((0, 1, 2, 4,  5,  6, 12, 13, 14, 16, 17, 18,  0,  1,  2,  4,  5,  6,  8,  9, 10,  0,  1,  2,  3,  4,  5,  6,  7),
            ...                        (1, 2, 3, 5,  6,  7, 13, 14, 15, 17, 18, 19,  1,  2,  3,  5,  6,  7,  9, 10, 11,  4,  5,  6,  7,  8,  9, 10, 11),
            ...                        (5, 6, 7, 9, 10, 11, 17, 18, 19, 21, 22, 23, 13, 14, 15, 17, 18, 19, 21, 22, 23, 16, 17, 18, 19, 20, 21, 22, 23),
            ...                        (4, 5, 6, 8,  9, 10, 16, 17, 18, 20, 21, 22, 12, 13, 14, 16, 17, 18, 20, 21, 22, 12, 13, 14, 15, 16, 17, 18, 19)))
            >>> numerix.allequal(faces, mesh._createFaces())
            1

            >>> cells = numerix.array(((21, 22, 23, 25, 26, 27),
            ...                        (22, 23, 24, 26, 27, 28),
            ...                        (12, 13, 14, 15, 16, 17),
            ...                        (15, 16, 17, 18, 19, 20),
            ...                        ( 0,  1,  2,  3,  4,  5),
            ...                        ( 6,  7,  8,  9, 10, 11)))
            >>> numerix.allequal(cells, mesh._createCells())
            1

            >>> externalFaces = numerix.array((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 19, 20, 21, 24, 25, 28))
            >>> numerix.allequal(externalFaces, 
            ...                  numerix.nonzero(mesh.getExteriorFaces()))
            1

            >>> internalFaces = numerix.array((15, 16, 17, 22, 23, 26, 27))
            >>> print numerix.allequal(internalFaces, 
            ...                        numerix.nonzero(mesh.getInteriorFaces()))
            1

            >>> from fipy.tools.numerix import MA
            >>> faceCellIds = MA.masked_values((( 0,  1,  2,  3,  4,  5,  0,  1,  2,  3,  4,  5,  0,  1,  2,  0, 1, 2,  3,  4,  5,  0, 0, 1,  2,  3, 3, 4,  5),
            ...                                 (-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,  3, 4, 5, -1, -1, -1, -1, 1, 2, -1, -1, 4, 5, -1)), -1)
            >>> numerix.allequal(faceCellIds, mesh.getFaceCellIDs())
            1
            
            >>> xy = dx * dy
            >>> xz = dx * dz
            >>> yz = dy * dz
            >>> faceAreas = numerix.array((xy, xy, xy, xy, xy, xy, xy, xy, xy, xy, xy, xy,
            ...                            xz, xz, xz, xz, xz, xz, xz, xz, xz,
            ...                            yz, yz, yz, yz, yz, yz, yz, yz))
            >>> numerix.allclose(faceAreas, mesh._getFaceAreas(), atol = 1e-10, rtol = 1e-10)
            1
            
            >>> faceCoords = numerix.take(vertices, faces, axis=1)
            >>> faceCenters = (faceCoords[...,0,:] + faceCoords[...,1,:] + faceCoords[...,2,:] + faceCoords[...,3,:]) / 4.
            >>> numerix.allclose(faceCenters, mesh.getFaceCenters(), atol = 1e-10, rtol = 1e-10)
            1

            >>> faceNormals = numerix.array((( 0,  0,  0,  0,  0,  0, 0, 0, 0, 0, 0, 0,  0,  0,  0, 0, 0, 0, 0, 0, 0, -1, 1, 1, 1, -1, 1, 1, 1),
            ...                              ( 0,  0,  0,  0,  0,  0, 0, 0, 0, 0, 0, 0, -1, -1, -1, 1, 1, 1, 1, 1, 1,  0, 0, 0, 0,  0, 0, 0, 0),
            ...                              (-1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1,  0,  0,  0, 0, 0, 0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0)))
            >>> numerix.allclose(faceNormals, mesh._getFaceNormals(), atol = 1e-10, rtol = 1e-10)
            1

            >>> cellToFaceOrientations = numerix.array(((1, -1, -1, 1, -1, -1),
            ...                                         (1, 1, 1, 1, 1, 1),
            ...                                         (1, 1, 1, -1, -1, -1),
            ...                                         (1, 1, 1, 1, 1, 1),
            ...                                         (1, 1, 1, 1, 1, 1),
            ...                                         (1, 1, 1, 1, 1, 1)))
            >>> numerix.allequal(cellToFaceOrientations, mesh._getCellFaceOrientations())
            1
                                             
            >>> cellVolumes = numerix.array((dx*dy*dz, dx*dy*dz, dx*dy*dz, dx*dy*dz, dx*dy*dz, dx*dy*dz))
            >>> numerix.allclose(cellVolumes, mesh.getCellVolumes(), atol = 1e-10, rtol = 1e-10)
            1

            >>> cellCenters = numerix.array(((dx/2., 3.*dx/2., 5.*dx/2.,    dx/2., 3.*dx/2., 5.*dx/2.),
            ...                              (dy/2.,    dy/2.,    dy/2., 3.*dy/2., 3.*dy/2., 3.*dy/2.),
            ...                              (dz/2.,    dz/2.,    dz/2.,    dz/2.,    dz/2.,    dz/2.)))
            >>> numerix.allclose(cellCenters, mesh.getCellCenters(), atol = 1e-10, rtol = 1e-10)
            1
                                              
            >>> faceToCellDistances = MA.masked_values(((dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dx/2, dx/2, dx/2, dx/2, dx/2, dx/2, dx/2, dx/2),
            ...                                         (  -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1, dy/2, dy/2, dy/2,   -1,   -1,   -1,   -1, dx/2, dx/2,   -1,   -1, dx/2,   -1)), -1) 
            >>> numerix.allclose(faceToCellDistances, mesh._getFaceToCellDistances(), atol = 1e-10, rtol = 1e-10)
            1
                                              
            >>> cellDistances = numerix.array((dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2,
            ...                                dy/2, dy/2, dy/2, dy, dy, dy, dy/2, dy/2, dy/2,
            ...                                dx/2, dx, dx, dx/2, dx/2, dx, dx, dx/2))
            >>> numerix.allclose(cellDistances, mesh._getCellDistances(), atol = 1e-10, rtol = 1e-10)
            1
            
            >>> faceToCellDistanceRatios = faceToCellDistances[0] / cellDistances
            >>> numerix.allclose(faceToCellDistanceRatios, mesh._getFaceToCellDistanceRatio(), atol = 1e-10, rtol = 1e-10)
            1

            >>> areaProjections = faceNormals * faceAreas
            >>> numerix.allclose(areaProjections, mesh._getAreaProjections(), atol = 1e-10, rtol = 1e-10)
            1

            >>> tangents1 = numerix.array(((1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
            ...                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1),
            ...                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)))
            >>> numerix.allclose(tangents1, mesh._getFaceTangents1(), atol = 1e-10, rtol = 1e-10)
            1

            >>> tangents2 = numerix.array(((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ...                            (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ...                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)))
            >>> numerix.allclose(tangents2, mesh._getFaceTangents2(), atol = 1e-10, rtol = 1e-10)
            1

            >>> print mesh._getCellToCellIDs()
            [[-- 0 1 -- 3 4]
             [1 2 -- 4 5 --]
             [-- -- -- 0 1 2]
             [3 4 5 -- -- --]
             [-- -- -- -- -- --]
             [-- -- -- -- -- --]]

            >>> print mesh._getCellToCellIDsFilled()
            [[0 0 1 3 3 4]
             [1 2 2 4 5 5]
             [0 1 2 0 1 2]
             [3 4 5 3 4 5]
             [0 1 2 3 4 5]
             [0 1 2 3 4 5]]

            >>> cellToCellDistances = numerix.take(cellDistances, cells)
            >>> numerix.allclose(cellToCellDistances, mesh._getCellToCellDistances(), atol = 1e-10, rtol = 1e-10)
            1

            >>> interiorCellIDs = numerix.array(())
            >>> numerix.allequal(interiorCellIDs, mesh._getInteriorCellIDs())
            1

            >>> exteriorCellIDs = numerix.array((0, 1, 2, 3, 4, 5))
            >>> numerix.allequal(exteriorCellIDs, mesh._getExteriorCellIDs())
            1

            >>> cellNormals = numerix.array((((-1, -1, -1, -1, -1, -1),
            ...                               ( 1,  1,  1,  1,  1,  1),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0)),
            ...                              (( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               (-1, -1, -1, -1, -1, -1),
            ...                               ( 1,  1,  1,  1,  1,  1),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0)),
            ...                              (( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               (-1, -1, -1, -1, -1, -1),
            ...                               ( 1,  1,  1,  1,  1,  1))))
            >>> numerix.allclose(cellNormals, mesh._getCellNormals(), atol = 1e-10, rtol = 1e-10)
            1

            >>> cellAreaProjections = numerix.array((((-yz, -yz, -yz, -yz, -yz, -yz),
            ...                                       ( yz,  yz,  yz,  yz,  yz,  yz),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0)),
            ...                                      ((  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (-xz, -xz, -xz, -xz, -xz, -xz),
            ...                                       ( xz,  xz,  xz,  xz,  xz,  xz),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0)),
            ...                                      ((  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (  0,   0,   0,   0,   0,   0),
            ...                                       (-xy, -xy, -xy, -xy, -xy, -xy),
            ...                                       ( xy,  xy,  xy,  xy,  xy,  xy))))
            >>> numerix.allclose(cellAreaProjections, mesh._getCellAreaProjections(), atol = 1e-10, rtol = 1e-10)
            1

            >>> cellVertexIDs = numerix.array((17, 16, 13, 12, 5, 4, 1, 0))
            >>> cellVertexIDs = numerix.array((cellVertexIDs, cellVertexIDs + 1, cellVertexIDs + 2,
            ...                                cellVertexIDs + 4, cellVertexIDs + 5, cellVertexIDs + 6))
            >>> cellVertexIDs = cellVertexIDs.swapaxes(0,1)


            >>> numerix.allclose(mesh._getCellVertexIDs(), cellVertexIDs)
            1

            >>> from fipy.tools import dump
            >>> (f, filename) = dump.write(mesh, extension = '.gz')            
            >>> unpickledMesh = dump.read(filename, f)

            >>> numerix.allequal(mesh.getCellCenters(), unpickledMesh.getCellCenters())
            1

            The following test was for a bug when dx, dy or dz are arrays.
            The _calcFaceAreas() method was commented out to fix this.

            >>> Grid3D(nx=2., ny=2., nz=2., dx=(1., 2.), dy=(1., 2.), dz=(1., 2.))
            Grid3D(dx=array([ 1.,  2.]), dy=(1.0, 2.0), dz=(1.0, 2.0), nx=2, ny=2, nz=2)
        """

def _test():
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    _test()