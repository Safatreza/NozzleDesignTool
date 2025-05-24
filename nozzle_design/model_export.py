import numpy as np
from stl import mesh
import trimesh
from typing import List, Tuple, Optional
import os
from pathlib import Path

from .engineering_calculations import NozzleSegment

class NozzleModelExporter:
    """Export nozzle geometry to various 3D formats"""
    
    def __init__(self, segments: List[NozzleSegment]):
        self.segments = segments
        self.vertices = []
        self.faces = []
    
    def generate_mesh(self, resolution: int = 32):
        """Generate 3D mesh from nozzle segments"""
        # Clear previous data
        self.vertices = []
        self.faces = []
        
        # Generate vertices and faces for each segment
        for i in range(len(self.segments) - 1):
            s1, s2 = self.segments[i], self.segments[i + 1]
            
            # Generate points around the circumference
            angles = np.linspace(0, 2*np.pi, resolution, endpoint=False)
            
            # Generate vertices for this segment
            for angle in angles:
                # Start point
                x1 = s1.start_x
                y1 = s1.start_radius * np.cos(angle)
                z1 = s1.start_radius * np.sin(angle)
                self.vertices.append([x1, y1, z1])
                
                # End point
                x2 = s2.start_x
                y2 = s2.start_radius * np.cos(angle)
                z2 = s2.start_radius * np.sin(angle)
                self.vertices.append([x2, y2, z2])
            
            # Generate faces
            for j in range(resolution):
                # Calculate vertex indices
                v1 = i * resolution * 2 + j * 2
                v2 = v1 + 1
                v3 = v1 + 2
                v4 = v1 + 3
                
                # Handle wrap-around
                if j == resolution - 1:
                    v3 = i * resolution * 2
                    v4 = v3 + 1
                
                # Add two triangular faces
                self.faces.append([v1, v2, v3])
                self.faces.append([v2, v4, v3])
        
        return np.array(self.vertices), np.array(self.faces)
    
    def export_stl(self, filename: str, resolution: int = 32):
        """Export nozzle geometry to STL format"""
        vertices, faces = self.generate_mesh(resolution)
        
        # Create the mesh
        nozzle_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
        
        # Set vertices and faces
        for i, face in enumerate(faces):
            for j in range(3):
                nozzle_mesh.vectors[i][j] = vertices[face[j]]
        
        # Save to file
        nozzle_mesh.save(filename)
    
    def export_obj(self, filename: str, resolution: int = 32):
        """Export nozzle geometry to OBJ format"""
        vertices, faces = self.generate_mesh(resolution)
        
        # Create trimesh object
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Export to OBJ
        mesh.export(filename)
    
    def export_step(self, filename: str, resolution: int = 32):
        """Export nozzle geometry to STEP format"""
        vertices, faces = self.generate_mesh(resolution)
        
        # Create trimesh object
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Export to STEP
        mesh.export(filename, file_type='step')
    
    def export_iges(self, filename: str, resolution: int = 32):
        """Export nozzle geometry to IGES format"""
        vertices, faces = self.generate_mesh(resolution)
        
        # Create trimesh object
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Export to IGES
        mesh.export(filename, file_type='iges')
    
    def export_all_formats(self, output_dir: str, base_name: str, resolution: int = 32):
        """Export nozzle geometry to all supported formats"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export to different formats
        self.export_stl(str(output_path / f"{base_name}.stl"), resolution)
        self.export_obj(str(output_path / f"{base_name}.obj"), resolution)
        self.export_step(str(output_path / f"{base_name}.step"), resolution)
        self.export_iges(str(output_path / f"{base_name}.iges"), resolution)
    
    def generate_manufacturing_drawing(self, filename: str):
        """Generate manufacturing drawing with dimensions"""
        # TODO: Implement manufacturing drawing generation
        # This would require a CAD library like FreeCAD or similar
        pass 