"""Module for Gmsh mesh generation and visualization."""

from typing import List, Dict, Optional, Tuple, Union
import numpy as np
import gmsh
import pygmsh
from pathlib import Path

class GmshVisualizer:
    """Class for Gmsh mesh generation and visualization."""
    
    def __init__(self, nozzle):
        """Initialize visualizer.
        
        Args:
            nozzle: Nozzle geometry object or list of NozzleSegment
        """
        # Accept either a geometry object (with .length) or a list of segments
        self.geometry = None
        self.mesh = None
        if hasattr(nozzle, 'length') and hasattr(nozzle, 'get_radius'):
            self.nozzle = nozzle
        elif isinstance(nozzle, list) and len(nozzle) > 0 and hasattr(nozzle[0], 'start_x'):
            # Assume list of NozzleSegment
            self.nozzle = self._make_geometry_from_segments(nozzle)
        else:
            raise ValueError("Invalid nozzle input: must be geometry object or list of NozzleSegment")
    
    def _make_geometry_from_segments(self, segments):
        # Create a simple geometry-like object from segments
        class SegGeom:
            def __init__(self, segments):
                self.segments = segments
                self.length = segments[-1].end_x
            def get_radius(self, x):
                # Find which segment x is in
                for seg in self.segments:
                    if seg.start_x <= x <= seg.end_x:
                        # Linear interpolation
                        t = (x - seg.start_x) / (seg.end_x - seg.start_x) if seg.end_x != seg.start_x else 0
                        return seg.start_radius + t * (seg.end_radius - seg.start_radius)
                # If x is out of bounds, return the closest endpoint
                if x < self.segments[0].start_x:
                    return self.segments[0].start_radius
                return self.segments[-1].end_radius
        return SegGeom(segments)
    
    def generate_geometry(self, resolution: int = 100) -> None:
        """Generate Gmsh geometry from nozzle.
        
        Args:
            resolution: Number of points around circumference
        """
        # Initialize Gmsh
        gmsh.initialize()
        
        # Create geometry
        with pygmsh.geo.Geometry() as geom:
            # Generate points along nozzle
            x = np.linspace(0, self.nozzle.length, resolution)
            theta = np.linspace(0, 2*np.pi, resolution)
            
            # Create points
            points = []
            for xi in x:
                r = self.nozzle.get_radius(xi)
                for thetai in theta:
                    points.append(geom.add_point([
                        xi,
                        r * np.cos(thetai),
                        r * np.sin(thetai)
                    ]))
            
            # Create lines
            lines = []
            for i in range(resolution - 1):
                for j in range(resolution - 1):
                    # Calculate point indices
                    p1 = i * resolution + j
                    p2 = i * resolution + j + 1
                    p3 = (i + 1) * resolution + j
                    p4 = (i + 1) * resolution + j + 1
                    
                    # Add lines
                    lines.append(geom.add_line(points[p1], points[p2]))
                    lines.append(geom.add_line(points[p2], points[p4]))
                    lines.append(geom.add_line(points[p4], points[p3]))
                    lines.append(geom.add_line(points[p3], points[p1]))
            
            # Create surfaces
            surfaces = []
            for i in range(0, len(lines), 4):
                loop = geom.add_curve_loop(lines[i:i+4])
                surfaces.append(geom.add_plane_surface(loop))
            
            # Create volume
            volume = geom.add_volume(surfaces)
            
            # Generate mesh
            self.geometry = geom
            self.mesh = geom.generate_mesh()
    
    def export_mesh(self, filename: str, format: str = 'msh') -> None:
        """Export mesh to file.
        
        Args:
            filename: Output filename
            format: Mesh format (msh, stl, vtk, etc.)
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry() first.")
        
        # Save mesh
        gmsh.write(filename)
    
    def visualize(self, interactive: bool = True) -> None:
        """Visualize mesh in Gmsh GUI.
        
        Args:
            interactive: Whether to show interactive GUI
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry() first.")
        
        # Show mesh
        gmsh.fltk.initialize()
        gmsh.fltk.run()
        gmsh.fltk.finalize()
    
    def get_mesh_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get mesh data as numpy arrays.
        
        Returns:
            Tuple of (vertices, faces) arrays
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry() first.")
        
        # Get mesh data
        vertices = np.array(self.mesh.points)
        faces = np.array(self.mesh.cells_dict['triangle'])
        
        return vertices, faces
    
    def calculate_mesh_quality(self) -> Dict[str, float]:
        """Calculate mesh quality metrics.
        
        Returns:
            Dictionary of quality metrics
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry() first.")
        
        # Calculate quality metrics
        quality = gmsh.model.mesh.getElementQualities()
        
        return {
            'min_quality': min(quality),
            'max_quality': max(quality),
            'avg_quality': np.mean(quality),
            'std_quality': np.std(quality)
        }
    
    def refine_mesh(self, target_size: float) -> None:
        """Refine mesh to target size.
        
        Args:
            target_size: Target element size
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry() first.")
        
        # Set target size
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0), target_size)
        
        # Refine mesh
        gmsh.model.mesh.refine()
    
    def __del__(self):
        """Clean up Gmsh resources."""
        gmsh.finalize() 