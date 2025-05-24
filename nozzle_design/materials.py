"""Module for material properties and thermal analysis."""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Material:
    """Material properties for thermal analysis."""
    name: str
    density: float  # kg/m³
    thermal_conductivity: float  # W/(m·K)
    specific_heat: float  # J/(kg·K)
    yield_strength: float  # Pa
    thermal_expansion: float  # 1/K
    melting_point: float  # K
    gamma: float  # Specific heat ratio
    
    @property
    def thermal_diffusivity(self) -> float:
        """Calculate thermal diffusivity.
        
        Returns:
            Thermal diffusivity in m²/s
        """
        return self.thermal_conductivity / (self.density * self.specific_heat)

# Common materials for rocket nozzles
MATERIALS = {
    'copper': Material(
        name='Copper',
        density=8960.0,
        thermal_conductivity=401.0,
        specific_heat=385.0,
        yield_strength=250e6,
        thermal_expansion=16.5e-6,
        melting_point=1357.77,
        gamma=1.4
    ),
    'steel': Material(
        name='Steel',
        density=7850.0,
        thermal_conductivity=50.0,
        specific_heat=490.0,
        yield_strength=250e6,
        thermal_expansion=12.0e-6,
        melting_point=1811.0,
        gamma=1.4
    ),
    'titanium': Material(
        name='Titanium',
        density=4500.0,
        thermal_conductivity=21.9,
        specific_heat=520.0,
        yield_strength=825e6,
        thermal_expansion=8.6e-6,
        melting_point=1941.0,
        gamma=1.4
    ),
    'inconel': Material(
        name='Inconel',
        density=8440.0,
        thermal_conductivity=11.4,
        specific_heat=434.0,
        yield_strength=1034e6,
        thermal_expansion=13.0e-6,
        melting_point=1723.0,
        gamma=1.4
    )
}

def get_material(name: str) -> Material:
    """Get material properties by name.
    
    Args:
        name: Material name (case-insensitive)
        
    Returns:
        Material object with properties
        
    Raises:
        KeyError: If material name is not found
    """
    return MATERIALS[name.lower()]

def calculate_thermal_stress(material: Material,
                           temperature_gradient: float,
                           length: float) -> float:
    """Calculate thermal stress in a material.
    
    Args:
        material: Material properties
        temperature_gradient: Temperature gradient in K/m
        length: Length scale in meters
        
    Returns:
        Thermal stress in Pascals
    """
    return material.thermal_expansion * material.thermal_conductivity * temperature_gradient * length

def calculate_safety_factor(material: Material,
                          stress: float) -> float:
    """Calculate safety factor for a given stress.
    
    Args:
        material: Material properties
        stress: Applied stress in Pascals
        
    Returns:
        Safety factor (yield_strength / stress)
    """
    return material.yield_strength / stress

def calculate_heat_capacity(material: Material,
                          volume: float) -> float:
    """Calculate heat capacity for a given volume.
    
    Args:
        material: Material properties
        volume: Volume in cubic meters
        
    Returns:
        Heat capacity in J/K
    """
    return material.density * material.specific_heat * volume

def calculate_thermal_resistance(material: Material,
                               length: float,
                               area: float) -> float:
    """Calculate thermal resistance.
    
    Args:
        material: Material properties
        length: Length in meters
        area: Cross-sectional area in square meters
        
    Returns:
        Thermal resistance in K/W
    """
    return length / (material.thermal_conductivity * area) 