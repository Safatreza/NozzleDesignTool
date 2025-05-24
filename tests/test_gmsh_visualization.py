"""Unit tests for Gmsh visualization."""

import pytest
import numpy as np
from pathlib import Path
import tempfile
from nozzle_design.gmsh_visualization import GmshVisualizer
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
            angle=15.0,
            length=0.1,
            area_ratio=1.0,
            mach_number=0.5,
            pressure=10e6,
            temperature=3000.0,
            wall_temperature=1000.0,
            heat_flux=1e6
        ),
        NozzleSegment(
            start_x=0.1,
            start_radius=0.03,
            end_x=0.2,
            end_radius=0.03,
            angle=0.0,
            length=0.1,
            area_ratio=1.0,
            mach_number=1.0,
            pressure=5e6,
            temperature=2500.0,
            wall_temperature=800.0,
            heat_flux=2e6
        ),
        NozzleSegment(
            start_x=0.2,
            start_radius=0.03,
            end_x=0.4,
            end_radius=0.06,
            angle=15.0,
            length=0.2,
            area_ratio=4.0,
            mach_number=2.0,
            pressure=1e6,
            temperature=2000.0,
            wall_temperature=600.0,
            heat_flux=3e6
        )
    ]

@pytest.fixture
def visualizer(nozzle_segments):
    """Create a Gmsh visualizer instance for testing."""
    return GmshVisualizer(nozzle_segments)

def test_generate_geometry(visualizer):
    """Test geometry generation."""
    visualizer.generate_geometry(resolution=20)
    assert visualizer.geometry is not None
    assert visualizer.mesh is not None

def test_export_mesh(visualizer):
    """Test mesh export."""
    visualizer.generate_geometry(resolution=20)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "nozzle.msh"
        visualizer.export_mesh(str(filename))
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_get_mesh_data(visualizer):
    """Test mesh data retrieval."""
    visualizer.generate_geometry(resolution=20)
    vertices, faces = visualizer.get_mesh_data()
    
    assert isinstance(vertices, np.ndarray)
    assert isinstance(faces, np.ndarray)
    assert vertices.shape[1] == 3  # x, y, z coordinates
    assert faces.shape[1] == 3  # triangular faces
    assert len(vertices) > 0
    assert len(faces) > 0

def test_calculate_mesh_quality(visualizer):
    """Test mesh quality calculation."""
    visualizer.generate_geometry(resolution=20)
    quality = visualizer.calculate_mesh_quality()
    
    assert 'min_quality' in quality
    assert 'max_quality' in quality
    assert 'avg_quality' in quality
    assert 'std_quality' in quality
    
    assert 0 < quality['min_quality'] <= 1
    assert 0 < quality['max_quality'] <= 1
    assert 0 < quality['avg_quality'] <= 1
    assert quality['std_quality'] >= 0

def test_refine_mesh(visualizer):
    """Test mesh refinement."""
    visualizer.generate_geometry(resolution=20)
    initial_vertices, initial_faces = visualizer.get_mesh_data()
    
    # Refine mesh
    visualizer.refine_mesh(target_size=0.01)
    refined_vertices, refined_faces = visualizer.get_mesh_data()
    
    # Check that refinement increased number of elements
    assert len(refined_vertices) > len(initial_vertices)
    assert len(refined_faces) > len(initial_faces)

def test_mesh_quality_improvement(visualizer):
    """Test mesh quality improvement after refinement."""
    visualizer.generate_geometry(resolution=20)
    initial_quality = visualizer.calculate_mesh_quality()
    
    # Refine mesh
    visualizer.refine_mesh(target_size=0.01)
    refined_quality = visualizer.calculate_mesh_quality()
    
    # Check that refinement improved mesh quality
    assert refined_quality['min_quality'] >= initial_quality['min_quality']
    assert refined_quality['avg_quality'] >= initial_quality['avg_quality']

def test_geometry_consistency(visualizer):
    """Test geometry consistency."""
    visualizer.generate_geometry(resolution=20)
    vertices, faces = visualizer.get_mesh_data()
    
    # Check vertex distribution
    x_coords = vertices[:, 0]
    assert np.min(x_coords) >= 0.0  # start at x=0
    assert np.max(x_coords) <= 0.4  # end at x=0.4
    
    # Check radius distribution
    yz_coords = vertices[:, 1:]
    radii = np.sqrt(np.sum(yz_coords**2, axis=1))
    assert np.min(radii) >= 0.03  # minimum radius at throat
    assert np.max(radii) <= 0.06  # maximum radius at exit

def test_resolution_effects(visualizer):
    """Test effects of different resolutions on mesh quality."""
    resolutions = [10, 20, 40]
    vertex_counts = []
    face_counts = []
    
    for resolution in resolutions:
        visualizer.generate_geometry(resolution=resolution)
        vertices, faces = visualizer.get_mesh_data()
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