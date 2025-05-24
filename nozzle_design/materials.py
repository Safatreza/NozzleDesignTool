"""Module for material properties and thermal analysis."""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Material:
    """Class for material properties."""
    name: str
    density: float  # kg/m^3
    thermal_conductivity: float  # W/(m·K)
    specific_heat: float  # J/(kg·K)
    thermal_expansion: float  # 1/K
    elastic_modulus: float  # Pa
    yield_strength: float  # Pa
    melting_point: float  # K
    gamma: float = 1.4  # Specific heat ratio, default 1.4

    @property
    def thermal_diffusivity(self) -> float:
        """Thermal diffusivity in m^2/s."""
        return self.thermal_conductivity / (self.density * self.specific_heat)

# Material properties database
MATERIALS = {
    'copper': Material(
        name='copper',
        density=8960.0,
        thermal_conductivity=401.0,
        specific_heat=385.0,
        thermal_expansion=16.5e-6,
        elastic_modulus=110e9,
        yield_strength=33e6,
        melting_point=1357.77,
        gamma=1.4
    ),
    'steel': Material(
        name='steel',
        density=7850.0,
        thermal_conductivity=50.0,
        specific_heat=490.0,
        thermal_expansion=12.0e-6,
        elastic_modulus=200e9,
        yield_strength=250e6,
        melting_point=1811.0,
        gamma=1.4
    ),
    'titanium': Material(
        name='titanium',
        density=4500.0,
        thermal_conductivity=21.9,
        specific_heat=520.0,
        thermal_expansion=8.6e-6,
        elastic_modulus=116e9,
        yield_strength=140e6,
        melting_point=1941.0,
        gamma=1.4
    ),
    'inconel': Material(
        name='inconel',
        density=8440.0,
        thermal_conductivity=11.4,
        specific_heat=434.0,
        thermal_expansion=13.0e-6,
        elastic_modulus=214e9,
        yield_strength=1034e6,
        melting_point=1673.0,
        gamma=1.4
    )
}

def get_material(name: str) -> Material:
    """Get material properties by name.
    
    Args:
        name: Material name (case-insensitive)
    Returns:
        Material object
    Raises:
        ValueError: If material not found
    """
    material = MATERIALS.get(name.lower())
    if material is None:
        raise ValueError(f"Material '{name}' not found")
    return material

def calculate_thermal_stress(material: Material,
                           temperature_gradient: float,
                           length: float) -> float:
    """Calculate thermal stress.
    
    Args:
        material: Material object
        temperature_gradient: Temperature gradient in K/m
        length: Length in m
    Returns:
        Thermal stress in Pa
    """
    return material.thermal_expansion * material.elastic_modulus * temperature_gradient * length

def calculate_safety_factor(material: Material,
                          stress: float) -> float:
    """Calculate safety factor.
    
    Args:
        material: Material object
        stress: Applied stress in Pa
    Returns:
        Safety factor
    """
    return material.yield_strength / stress

def calculate_heat_capacity(material: Material,
                          volume: float) -> float:
    """Calculate heat capacity.
    
    Args:
        material: Material object
        volume: Volume in m^3
    Returns:
        Heat capacity in J/K
    """
    return material.density * material.specific_heat * volume

def calculate_thermal_resistance(material: Material,
                               length: float,
                               area: float) -> float:
    """Calculate thermal resistance.
    
    Args:
        material: Material object
        length: Length in m
        area: Cross-sectional area in m^2
    Returns:
        Thermal resistance in K/W
    """
    return length / (material.thermal_conductivity * area)

def calculate_thermal_diffusivity(material: Material) -> float:
    """Calculate thermal diffusivity.
    
    Args:
        material: Material object
    Returns:
        Thermal diffusivity in m^2/s
    """
    return material.thermal_conductivity / (material.density * material.specific_heat) 