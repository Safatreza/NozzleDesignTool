"""Module for Gmsh mesh generation and visualization of nozzle designs."""

from typing import List, Dict, Optional, Tuple
import numpy as np
import gmsh
import pygmsh
from pathlib import Path

from .nozzle_geometry import NozzleSegment

class GmshVisualizer:
    """Visualizer for nozzle designs using Gmsh."""
    
    def __init__(self, segments: List[NozzleSegment]):
        """Initialize the visualizer with nozzle segments.
        
        Args:
            segments: List of nozzle segments
        """
        self.segments = segments
        self.geometry = None
        self.mesh = None
    
    def generate_geometry(self, resolution: int = 32) -> None:
        """Generate Gmsh geometry from nozzle segments.
        
        Args:
            resolution: Number of points around circumference
        """
        # Initialize Gmsh
        gmsh.initialize()
        
        # Create geometry
        self.geometry = pygmsh.geo.Geometry()
        
        # Generate points for each segment
        points = []
        for segment in self.segments:
            # Generate points around circumference
            angles = np.linspace(0, 2*np.pi, resolution, endpoint=False)
            
            for angle in angles:
                x = segment.start_x
                y = segment.start_radius * np.cos(angle)
                z = segment.start_radius * np.sin(angle)
                points.append(self.geometry.add_point([x, y, z]))
        
        # Create lines between points
        lines = []
        for i in range(len(points) - 1):
            lines.append(self.geometry.add_line(points[i], points[i + 1]))
        
        # Create surface
        surface = self.geometry.add_surface(lines)
        
        # Set mesh size
        self.geometry.set_mesh_size_callback(lambda dim, tag, x, y, z, lc: 0.1)
        
        # Generate mesh
        self.mesh = self.geometry.generate_mesh()
    
    def export_mesh(self, filename: str, format: str = 'msh') -> None:
        """Export mesh to file.
        
        Args:
            filename: Output filename
            format: Mesh format (msh, vtk, etc.)
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry first.")
        
        gmsh.write(filename)
    
    def visualize(self, interactive: bool = True) -> None:
        """Visualize the mesh in Gmsh GUI.
        
        Args:
            interactive: Whether to show interactive GUI
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry first.")
        
        if interactive:
            gmsh.fltk.initialize()
            gmsh.fltk.run()
    
    def get_mesh_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get mesh data as numpy arrays.
        
        Returns:
            Tuple of (vertices, faces) arrays
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry first.")
        
        # Get mesh data
        nodes = self.mesh.points
        elements = self.mesh.cells_dict['triangle']
        
        return nodes, elements
    
    def calculate_mesh_quality(self) -> Dict[str, float]:
        """Calculate mesh quality metrics.
        
        Returns:
            Dictionary of mesh quality metrics
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry first.")
        
        # Get mesh data
        nodes, elements = self.get_mesh_data()
        
        # Calculate element quality metrics
        qualities = []
        for element in elements:
            # Get element vertices
            v1, v2, v3 = nodes[element]
            
            # Calculate element area
            area = 0.5 * np.linalg.norm(np.cross(v2 - v1, v3 - v1))
            
            # Calculate element quality (ratio of inscribed to circumscribed circle)
            a = np.linalg.norm(v2 - v3)
            b = np.linalg.norm(v1 - v3)
            c = np.linalg.norm(v1 - v2)
            s = (a + b + c) / 2
            quality = 4 * np.sqrt(3) * area / (a**2 + b**2 + c**2)
            qualities.append(quality)
        
        return {
            'min_quality': min(qualities),
            'max_quality': max(qualities),
            'avg_quality': np.mean(qualities),
            'std_quality': np.std(qualities)
        }
    
    def refine_mesh(self, target_size: float) -> None:
        """Refine mesh to target size.
        
        Args:
            target_size: Target element size
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated. Call generate_geometry first.")
        
        # Set mesh size
        self.geometry.set_mesh_size_callback(lambda dim, tag, x, y, z, lc: target_size)
        
        # Regenerate mesh
        self.mesh = self.geometry.generate_mesh()
    
    def __del__(self):
        """Clean up Gmsh."""
        gmsh.finalize() 