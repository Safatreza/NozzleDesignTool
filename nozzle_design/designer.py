"""Module for nozzle design calculations."""

from typing import List, Dict, Optional, Tuple
import numpy as np
from .geometries import ConicalNozzle, BellNozzle, DualBellNozzle, AerospikeNozzle
from .flow_solver import FlowSolver
from .materials import get_material

class NozzleDesigner:
    """Class for nozzle design calculations."""
    
    def __init__(self,
                 chamber_pressure: float,
                 chamber_temperature: float,
                 mass_flow: float,
                 gamma: float = 1.4,
                 material: str = 'copper'):
        """Initialize nozzle designer.
        
        Args:
            chamber_pressure: Chamber pressure in Pa
            chamber_temperature: Chamber temperature in K
            mass_flow: Mass flow rate in kg/s
            gamma: Specific heat ratio
            material: Nozzle material name
        """
        self.chamber_pressure = chamber_pressure
        self.chamber_temperature = chamber_temperature
        self.mass_flow = mass_flow
        self.gamma = gamma
        self.material = get_material(material)
        self.flow_solver = FlowSolver(gamma=gamma)
    
    def design_conical_nozzle(self,
                            expansion_ratio: float,
                            length: float,
                            wall_angle: float = 15.0) -> ConicalNozzle:
        """Design a conical nozzle.
        
        Args:
            expansion_ratio: Nozzle expansion ratio
            length: Nozzle length in meters
            wall_angle: Wall angle in degrees
            
        Returns:
            ConicalNozzle object
        """
        # Calculate throat area from mass flow
        throat_area = self.flow_solver.calculate_throat_area(
            self.mass_flow,
            self.chamber_pressure,
            self.chamber_temperature
        )
        
        # Calculate throat radius
        throat_radius = np.sqrt(throat_area / np.pi)
        
        # Calculate exit radius
        exit_radius = throat_radius * np.sqrt(expansion_ratio)
        
        return ConicalNozzle(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            wall_angle=wall_angle
        )
    
    def design_bell_nozzle(self,
                          expansion_ratio: float,
                          length: float,
                          wall_angle: float = 15.0) -> BellNozzle:
        """Design a bell nozzle.
        
        Args:
            expansion_ratio: Nozzle expansion ratio
            length: Nozzle length in meters
            wall_angle: Initial wall angle in degrees
            
        Returns:
            BellNozzle object
        """
        # Calculate throat area from mass flow
        throat_area = self.flow_solver.calculate_throat_area(
            self.mass_flow,
            self.chamber_pressure,
            self.chamber_temperature
        )
        
        # Calculate throat radius
        throat_radius = np.sqrt(throat_area / np.pi)
        
        # Calculate exit radius
        exit_radius = throat_radius * np.sqrt(expansion_ratio)
        
        return BellNozzle(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            wall_angle=wall_angle
        )
    
    def design_dual_bell_nozzle(self,
                               expansion_ratio: float,
                               length: float,
                               wall_angle: float = 15.0,
                               inflection_point: float = 0.5) -> DualBellNozzle:
        """Design a dual-bell nozzle.
        
        Args:
            expansion_ratio: Nozzle expansion ratio
            length: Nozzle length in meters
            wall_angle: Initial wall angle in degrees
            inflection_point: Location of inflection point (0-1)
            
        Returns:
            DualBellNozzle object
        """
        # Calculate throat area from mass flow
        throat_area = self.flow_solver.calculate_throat_area(
            self.mass_flow,
            self.chamber_pressure,
            self.chamber_temperature
        )
        
        # Calculate throat radius
        throat_radius = np.sqrt(throat_area / np.pi)
        
        # Calculate exit radius
        exit_radius = throat_radius * np.sqrt(expansion_ratio)
        
        return DualBellNozzle(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            wall_angle=wall_angle,
            inflection_point=inflection_point
        )
    
    def design_aerospike_nozzle(self,
                               expansion_ratio: float,
                               length: float,
                               wall_angle: float = 15.0,
                               spike_angle: float = 20.0) -> AerospikeNozzle:
        """Design an aerospike nozzle.
        
        Args:
            expansion_ratio: Nozzle expansion ratio
            length: Nozzle length in meters
            wall_angle: Initial wall angle in degrees
            spike_angle: Spike angle in degrees
            
        Returns:
            AerospikeNozzle object
        """
        # Calculate throat area from mass flow
        throat_area = self.flow_solver.calculate_throat_area(
            self.mass_flow,
            self.chamber_pressure,
            self.chamber_temperature
        )
        
        # Calculate throat radius
        throat_radius = np.sqrt(throat_area / np.pi)
        
        # Calculate exit radius
        exit_radius = throat_radius * np.sqrt(expansion_ratio)
        
        return AerospikeNozzle(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            wall_angle=wall_angle,
            spike_angle=spike_angle
        )
    
    def calculate_performance(self, nozzle: ConicalNozzle) -> Dict[str, float]:
        """Calculate nozzle performance metrics.
        
        Args:
            nozzle: Nozzle geometry object
            
        Returns:
            Dictionary of performance metrics
        """
        # Calculate thrust coefficient
        thrust_coef = self.flow_solver.calculate_thrust_coefficient(
            nozzle.expansion_ratio,
            self.chamber_pressure
        )
        
        # Calculate specific impulse
        isp = self.flow_solver.calculate_specific_impulse(
            thrust_coef,
            self.chamber_temperature
        )
        
        # Calculate thrust
        thrust = thrust_coef * self.chamber_pressure * np.pi * nozzle.throat_radius**2
        
        return {
            'thrust_coefficient': thrust_coef,
            'specific_impulse': isp,
            'thrust': thrust
        }
    
    def calculate_thermal_loads(self, nozzle: ConicalNozzle) -> Dict[str, float]:
        """Calculate thermal loads on nozzle.
        
        Args:
            nozzle: Nozzle geometry object
            
        Returns:
            Dictionary of thermal loads
        """
        # Calculate heat transfer coefficient
        h = 0.026 * (self.mass_flow / (np.pi * nozzle.throat_radius**2))**0.8
        
        # Calculate wall temperature
        wall_temp = self.chamber_temperature * 0.7  # Approximate
        
        # Calculate heat flux
        q = h * (self.chamber_temperature - wall_temp)
        
        # Calculate thermal stress
        thermal_stress = self.material.thermal_expansion * self.material.elastic_modulus * (wall_temp - 300)
        
        return {
            'heat_transfer_coefficient': h,
            'wall_temperature': wall_temp,
            'heat_flux': q,
            'thermal_stress': thermal_stress
        } 