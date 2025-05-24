"""Module for exporting nozzle designs to various formats."""

from typing import List, Dict, Optional, Tuple
import numpy as np
from stl import mesh
import trimesh
from pathlib import Path
import os
import zipfile
from datetime import datetime
import json

from .nozzle_geometry import NozzleSegment

class NozzleExporter:
    """Exporter for nozzle designs to various formats."""
    
    def __init__(self, nozzle_geometry):
        """Initialize exporter.
        
        Args:
            nozzle_geometry: Nozzle geometry object
        """
        self.nozzle = nozzle_geometry
    
    def export_stl(self, filename: str, resolution: int = 100) -> None:
        """Export nozzle to STL format.
        
        Args:
            filename: Output filename
            resolution: Number of points around circumference
        """
        # Generate points along nozzle
        x = np.linspace(0, self.nozzle.length, resolution)
        theta = np.linspace(0, 2*np.pi, resolution)
        
        # Generate mesh points
        vertices = []
        for xi in x:
            r = self.nozzle.get_radius(xi)
            for thetai in theta:
                vertices.append([
                    xi,
                    r * np.cos(thetai),
                    r * np.sin(thetai)
                ])
        
        # Create faces
        faces = []
        for i in range(resolution - 1):
            for j in range(resolution - 1):
                # Calculate vertex indices
                v1 = i * resolution + j
                v2 = i * resolution + j + 1
                v3 = (i + 1) * resolution + j
                v4 = (i + 1) * resolution + j + 1
                
                # Add two triangular faces
                faces.append([v1, v2, v3])
                faces.append([v2, v4, v3])
        
        # Create STL mesh
        nozzle_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
        for i, face in enumerate(faces):
            for j in range(3):
                nozzle_mesh.vectors[i][j] = vertices[face[j]]
        
        # Save STL file
        nozzle_mesh.save(filename)
    
    def export_json(self, filename: str, resolution: int = 100) -> None:
        """Export nozzle to JSON format.
        
        Args:
            filename: Output filename
            resolution: Number of points along nozzle
        """
        # Generate points along nozzle
        x = np.linspace(0, self.nozzle.length, resolution)
        r = [self.nozzle.get_radius(xi) for xi in x]
        
        # Create data dictionary
        data = {
            'type': self.nozzle.__class__.__name__,
            'parameters': {
                'throat_radius': self.nozzle.throat_radius,
                'exit_radius': self.nozzle.exit_radius,
                'length': self.nozzle.length,
                'expansion_ratio': self.nozzle.expansion_ratio,
                'wall_angle': self.nozzle.wall_angle
            },
            'contour': {
                'x': x.tolist(),
                'r': r
            }
        }
        
        # Save JSON file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def export_csv(self, filename: str, resolution: int = 100) -> None:
        """Export nozzle to CSV format.
        
        Args:
            filename: Output filename
            resolution: Number of points along nozzle
        """
        # Generate points along nozzle
        x = np.linspace(0, self.nozzle.length, resolution)
        r = [self.nozzle.get_radius(xi) for xi in x]
        
        # Save CSV file
        np.savetxt(filename, np.column_stack((x, r)), delimiter=',', header='x,r', comments='')
    
    def export_step(self, filename: str) -> None:
        """Export nozzle to STEP format.
        
        Args:
            filename: Output filename
        """
        # This would require a CAD library like FreeCAD or OpenCascade
        # For now, we'll just create a placeholder file
        with open(filename, 'w') as f:
            f.write('STEP file export not implemented yet')
    
    def export_dxf(self, filename: str, resolution: int = 100) -> None:
        """Export nozzle to DXF format.
        
        Args:
            filename: Output filename
            resolution: Number of points along nozzle
        """
        # This would require a DXF library like ezdxf
        # For now, we'll just create a placeholder file
        with open(filename, 'w') as f:
            f.write('DXF file export not implemented yet')
    
    def generate_mesh(self, resolution: int = 32) -> tuple:
        """Generate 3D mesh from nozzle segments.
        
        Args:
            resolution: Number of points around circumference
            
        Returns:
            Tuple of (vertices, faces) arrays
        """
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
    
    def export_obj(self, filename: str, resolution: int = 32) -> None:
        """Export nozzle geometry to OBJ format.
        
        Args:
            filename: Output filename
            resolution: Number of points around circumference
        """
        vertices, faces = self.generate_mesh(resolution)
        
        # Create trimesh object
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Export to OBJ
        mesh.export(filename)
    
    def export_iges(self, filename: str, resolution: int = 32) -> None:
        """Export nozzle geometry to IGES format.
        
        Args:
            filename: Output filename
            resolution: Number of points around circumference
        """
        vertices, faces = self.generate_mesh(resolution)
        
        # Create trimesh object
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Export to IGES
        mesh.export(filename, file_type='iges')
    
    def export_all_formats(self, output_dir: str, base_name: str, resolution: int = 32) -> None:
        """Export nozzle geometry to all supported formats.
        
        Args:
            output_dir: Output directory
            base_name: Base filename
            resolution: Number of points around circumference
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export to different formats
        self.export_stl(str(output_path / f"{base_name}.stl"), resolution)
        self.export_obj(str(output_path / f"{base_name}.obj"), resolution)
        self.export_step(str(output_path / f"{base_name}.step"), resolution)
        self.export_iges(str(output_path / f"{base_name}.iges"), resolution)
    
    def export_zip(self, output_dir: str, base_name: str, resolution: int = 32) -> str:
        """Export nozzle geometry to all formats in a zip file.
        
        Args:
            output_dir: Output directory
            base_name: Base filename
            resolution: Number of points around circumference
            
        Returns:
            Path to the zip file
        """
        # Create temporary directory
        temp_dir = Path(output_dir) / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Export all formats
            self.export_all_formats(str(temp_dir), base_name, resolution)
            
            # Create zip file
            zip_path = Path(output_dir) / f"{base_name}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for ext in ['stl', 'obj', 'step', 'iges']:
                    file_path = temp_dir / f"{base_name}.{ext}"
                    zipf.write(file_path, f"{base_name}.{ext}")
            
            return str(zip_path)
        
        finally:
            # Clean up temporary directory
            for file in temp_dir.glob("*"):
                file.unlink()
            temp_dir.rmdir()
    
    def generate_manufacturing_drawing(self, filename: str) -> None:
        """Generate manufacturing drawing with dimensions.
        
        Args:
            filename: Output filename
            
        Note:
            This is a placeholder for future implementation using a CAD library.
        """
        # TODO: Implement manufacturing drawing generation
        # This would require a CAD library like FreeCAD or similar
        pass 