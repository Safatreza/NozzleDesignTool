from dataclasses import dataclass
from typing import List, Tuple
from .thermodynamics import GasProperties

@dataclass
class NozzleProfile:
    """Represents the complete nozzle design profile"""
    shape: str
    length: float
    pressure_gradient: List[float]
    temperature_gradient: List[float]
    gas_properties: GasProperties
    geometry: List[Tuple[float, float]] 