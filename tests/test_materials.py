"""Unit tests for material properties and thermal analysis."""

import pytest
from nozzle_design.materials import (
    Material,
    MATERIALS,
    get_material,
    calculate_thermal_stress,
    calculate_safety_factor,
    calculate_heat_capacity,
    calculate_thermal_resistance
)

def test_material_properties():
    """Test material property calculations."""
    # Test copper properties
    copper = MATERIALS['copper']
    assert copper.name == 'copper'
    assert copper.density > 0
    assert copper.thermal_conductivity > 0
    assert copper.specific_heat > 0
    assert copper.yield_strength > 0
    assert copper.thermal_expansion > 0
    assert copper.melting_point > 0
    assert copper.gamma > 0
    
    # Test thermal diffusivity calculation
    expected_diffusivity = copper.thermal_conductivity / (copper.density * copper.specific_heat)
    assert abs(copper.thermal_diffusivity - expected_diffusivity) < 1e-6

def test_get_material():
    """Test material retrieval function."""
    # Test existing material
    copper = get_material('copper')
    assert isinstance(copper, Material)
    assert copper.name == 'copper'
    
    # Test non-existent material
    with pytest.raises(ValueError):
        get_material('nonexistent_material')

def test_calculate_thermal_stress():
    """Test thermal stress calculation."""
    copper = get_material('copper')
    temperature_gradient = 1000.0  # K/m
    length = 0.1  # m
    
    stress = calculate_thermal_stress(copper, temperature_gradient, length)
    assert stress > 0
    
    # For given conditions, stress should be roughly 100 MPa
    assert 50e6 < stress < 150e6

def test_calculate_safety_factor():
    """Test safety factor calculation."""
    copper = get_material('copper')
    stress = 100e6  # 100 MPa
    
    safety_factor = calculate_safety_factor(copper, stress)
    assert safety_factor > 0
    
    # For given conditions, safety factor should be roughly 2
    assert 1.5 < safety_factor < 2.5

def test_calculate_heat_capacity():
    """Test heat capacity calculation."""
    copper = get_material('copper')
    volume = 0.001  # 1 liter
    
    heat_capacity = calculate_heat_capacity(copper, volume)
    assert heat_capacity > 0
    
    # For given conditions, heat capacity should be roughly 3.5 kJ/K
    assert 3.0 < heat_capacity < 4.0

def test_calculate_thermal_resistance():
    """Test thermal resistance calculation."""
    copper = get_material('copper')
    length = 0.1  # m
    area = 0.01  # m²
    
    resistance = calculate_thermal_resistance(copper, length, area)
    assert resistance > 0
    
    # For given conditions, thermal resistance should be roughly 0.1 K/W
    assert 0.05 < resistance < 0.15

def test_material_comparison():
    """Test material property comparisons."""
    copper = get_material('copper')
    steel = get_material('steel')
    titanium = get_material('titanium')
    inconel = get_material('inconel')
    
    # Compare thermal conductivity
    assert copper.thermal_conductivity > steel.thermal_conductivity
    assert steel.thermal_conductivity > titanium.thermal_conductivity
    assert titanium.thermal_conductivity > inconel.thermal_conductivity
    
    # Compare yield strength
    assert inconel.yield_strength > steel.yield_strength
    assert steel.yield_strength > titanium.yield_strength
    assert titanium.yield_strength > copper.yield_strength
    
    # Compare density
    assert steel.density > copper.density
    assert copper.density > titanium.density
    assert titanium.density > inconel.density

def test_thermal_properties_consistency():
    """Test consistency of thermal properties."""
    for material in MATERIALS.values():
        # Check that thermal diffusivity is positive
        assert material.thermal_diffusivity > 0
        
        # Check that thermal expansion is positive
        assert material.thermal_expansion > 0
        
        # Check that specific heat is positive
        assert material.specific_heat > 0
        
        # Check that thermal conductivity is positive
        assert material.thermal_conductivity > 0
        
        # Check that melting point is above room temperature
        assert material.melting_point > 293.15  # 20°C 