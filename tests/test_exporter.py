"""Unit tests for nozzle design export functionality."""

import pytest
import numpy as np
import os
import tempfile
from pathlib import Path
from nozzle_design.exporter import NozzleExporter
from nozzle_design.nozzle_geometry import NozzleSegment

@pytest.fixture
def nozzle_segments():
    """Create sample nozzle segments for testing."""
    return [
        NozzleSegment(
            start_x=0.0,
            start_radius=0.05,
            end_x=0.1,
            end_radius=0.03,
            type='converging'
        ),
        NozzleSegment(
            start_x=0.1,
            start_radius=0.03,
            end_x=0.2,
            end_radius=0.03,
            type='throat'
        ),
        NozzleSegment(
            start_x=0.2,
            start_radius=0.03,
            end_x=0.4,
            end_radius=0.06,
            type='diverging'
        )
    ]

@pytest.fixture
def exporter(nozzle_segments):
    """Create a nozzle exporter instance for testing."""
    return NozzleExporter(nozzle_segments)

def test_generate_mesh(exporter):
    """Test mesh generation."""
    resolution = 20
    vertices, faces = exporter.generate_mesh(resolution)
    
    # Check vertices
    assert isinstance(vertices, np.ndarray)
    assert vertices.shape[1] == 3  # x, y, z coordinates
    assert len(vertices) > 0
    
    # Check faces
    assert isinstance(faces, np.ndarray)
    assert faces.shape[1] == 3  # triangular faces
    assert len(faces) > 0
    
    # Check mesh connectivity
    assert np.all(faces >= 0)  # no negative indices
    assert np.all(faces < len(vertices))  # indices within bounds

def test_export_stl(exporter):
    """Test STL export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "nozzle.stl"
        exporter.export_stl(str(filename), resolution=20)
        
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_export_obj(exporter):
    """Test OBJ export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "nozzle.obj"
        exporter.export_obj(str(filename), resolution=20)
        
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_export_step(exporter):
    """Test STEP export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "nozzle.step"
        exporter.export_step(str(filename), resolution=20)
        
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_export_iges(exporter):
    """Test IGES export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "nozzle.iges"
        exporter.export_iges(str(filename), resolution=20)
        
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_export_all_formats(exporter):
    """Test export to all formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_filename = "nozzle"
        exporter.export_all_formats(tmpdir, base_filename, resolution=20)
        
        # Check that all files were created
        assert (Path(tmpdir) / f"{base_filename}.stl").exists()
        assert (Path(tmpdir) / f"{base_filename}.obj").exists()
        assert (Path(tmpdir) / f"{base_filename}.step").exists()
        assert (Path(tmpdir) / f"{base_filename}.iges").exists()

def test_export_zip(exporter):
    """Test zip file export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_filename = Path(tmpdir) / "nozzle.zip"
        exporter.export_zip(str(zip_filename), resolution=20)
        
        assert zip_filename.exists()
        assert zip_filename.stat().st_size > 0

def test_mesh_quality(exporter):
    """Test mesh quality metrics."""
    resolution = 20
    vertices, faces = exporter.generate_mesh(resolution)
    
    # Check vertex distribution
    x_coords = vertices[:, 0]
    assert np.min(x_coords) >= 0.0  # start at x=0
    assert np.max(x_coords) <= 0.4  # end at x=0.4
    
    # Check radius distribution
    yz_coords = vertices[:, 1:]
    radii = np.sqrt(np.sum(yz_coords**2, axis=1))
    assert np.min(radii) >= 0.03  # minimum radius at throat
    assert np.max(radii) <= 0.06  # maximum radius at exit
    
    # Check face normals
    def calculate_face_normal(face):
        v1 = vertices[face[1]] - vertices[face[0]]
        v2 = vertices[face[2]] - vertices[face[0]]
        return np.cross(v1, v2)
    
    face_normals = np.array([calculate_face_normal(face) for face in faces])
    assert np.all(np.linalg.norm(face_normals, axis=1) > 0)  # no degenerate faces

def test_resolution_effects(exporter):
    """Test effects of different resolutions on mesh quality."""
    resolutions = [10, 20, 40]
    vertex_counts = []
    face_counts = []
    
    for resolution in resolutions:
        vertices, faces = exporter.generate_mesh(resolution)
        vertex_counts.append(len(vertices))
        face_counts.append(len(faces))
    
    # Check that higher resolution produces more vertices and faces
    assert vertex_counts[2] > vertex_counts[1] > vertex_counts[0]
    assert face_counts[2] > face_counts[1] > face_counts[0]
    
    # Check that the increase is roughly quadratic
    ratio1 = vertex_counts[1] / vertex_counts[0]
    ratio2 = vertex_counts[2] / vertex_counts[1]
    assert 3.5 < ratio1 < 4.5
    assert 3.5 < ratio2 < 4.5 