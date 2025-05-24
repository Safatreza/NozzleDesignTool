"""Nozzle Design Tool - A comprehensive tool for rocket nozzle design and analysis."""

from .geometries import (
    NozzleGeometry,
    ConicalNozzle,
    BellNozzle,
    DualBellNozzle,
    AerospikeNozzle
)
from .designer import NozzleDesigner
from .flow_solver import FlowSolver
from .materials import (
    Material,
    get_material,
    calculate_thermal_stress,
    calculate_safety_factor,
    calculate_heat_capacity,
    calculate_thermal_resistance,
    calculate_thermal_diffusivity
)
from .ui import UserInterface
from .visualizer import NozzleVisualizer

__version__ = '0.1.0'
__author__ = 'Your Name'
__email__ = 'your.email@example.com'

__all__ = [
    'NozzleGeometry',
    'ConicalNozzle',
    'BellNozzle',
    'DualBellNozzle',
    'AerospikeNozzle',
    'NozzleDesigner',
    'FlowSolver',
    'Material',
    'get_material',
    'calculate_thermal_stress',
    'calculate_safety_factor',
    'calculate_heat_capacity',
    'calculate_thermal_resistance',
    'calculate_thermal_diffusivity',
    'UserInterface',
    'NozzleVisualizer'
] 