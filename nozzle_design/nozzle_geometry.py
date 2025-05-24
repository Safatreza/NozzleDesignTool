"""Module for nozzle geometry calculations and optimization."""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import minimize

from .flow_solver import FlowSolver
from .materials import Material

@dataclass
class NozzleSegment:
    """Represents a segment of the nozzle with its properties."""
    start_x: float
    end_x: float
    start_radius: float
    end_radius: float
    angle: float
    length: float
    area_ratio: float
    mach_number: float
    pressure: float
    temperature: float
    wall_temperature: float
    heat_flux: float

@dataclass
class NozzleGeometry:
    """Represents the complete nozzle geometry with performance metrics."""
    segments: List[NozzleSegment]
    performance_metrics: Dict[str, float]

class NozzleGeometryCalculator:
    """Calculator for nozzle geometry and optimization."""
    
    def __init__(self, flow_solver: FlowSolver):
        """Initialize the calculator with a flow solver.
        
        Args:
            flow_solver: FlowSolver instance for flow calculations
        """
        self.flow_solver = flow_solver
    
    def calculate_geometry(self,
                          divergence_angle: float,
                          length_ratio: float,
                          chamber_state: Dict[str, float],
                          material: Material) -> NozzleGeometry:
        """Calculate nozzle geometry based on input parameters.
        
        Args:
            divergence_angle: Nozzle divergence angle in degrees
            length_ratio: Length to diameter ratio
            chamber_state: Dictionary containing chamber conditions
            material: Material properties for thermal analysis
            
        Returns:
            NozzleGeometry object containing segments and performance metrics
        """
        # Calculate throat area
        throat_area = self._calculate_throat_area(chamber_state)
        throat_radius = np.sqrt(throat_area / np.pi)
        
        # Calculate exit area
        exit_area = throat_area * chamber_state['area_ratio']
        exit_radius = np.sqrt(exit_area / np.pi)
        
        # Calculate nozzle length
        length = throat_radius * length_ratio
        
        # Generate segments
        segments = self._generate_segments(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            divergence_angle=divergence_angle,
            chamber_state=chamber_state,
            material=material
        )
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(segments, chamber_state)
        
        return NozzleGeometry(segments=segments, performance_metrics=metrics)
    
    def optimize_for_thrust(self,
                          thrust: float,
                          chamber_state: Dict[str, float],
                          ambient_pressure: float,
                          material: Material) -> NozzleGeometry:
        """Optimize nozzle geometry for maximum thrust.
        
        Args:
            thrust: Required thrust in Newtons
            chamber_state: Dictionary containing chamber conditions
            ambient_pressure: Ambient pressure in Pascals
            material: Material properties for thermal analysis
            
        Returns:
            Optimized NozzleGeometry object
        """
        def objective(x: np.ndarray) -> float:
            """Objective function for thrust optimization."""
            divergence_angle, length_ratio = x
            geometry = self.calculate_geometry(
                divergence_angle=divergence_angle,
                length_ratio=length_ratio,
                chamber_state=chamber_state,
                material=material
            )
            return -geometry.performance_metrics['thrust_coefficient']
        
        # Initial guess and bounds
        x0 = np.array([15.0, 2.0])  # Initial divergence angle and length ratio
        bounds = [(5.0, 30.0), (1.5, 5.0)]  # Bounds for divergence angle and length ratio
        
        # Optimize
        result = minimize(
            objective,
            x0=x0,
            bounds=bounds,
            method='L-BFGS-B'
        )
        
        # Get optimized geometry
        return self.calculate_geometry(
            divergence_angle=result.x[0],
            length_ratio=result.x[1],
            chamber_state=chamber_state,
            material=material
        )
    
    def optimize_for_mach(self,
                         target_mach: float,
                         chamber_state: Dict[str, float],
                         ambient_pressure: float,
                         material: Material) -> NozzleGeometry:
        """Optimize nozzle geometry for target Mach number.
        
        Args:
            target_mach: Target exit Mach number
            chamber_state: Dictionary containing chamber conditions
            ambient_pressure: Ambient pressure in Pascals
            material: Material properties for thermal analysis
            
        Returns:
            Optimized NozzleGeometry object
        """
        def objective(x: np.ndarray) -> float:
            """Objective function for Mach number optimization."""
            divergence_angle, length_ratio = x
            geometry = self.calculate_geometry(
                divergence_angle=divergence_angle,
                length_ratio=length_ratio,
                chamber_state=chamber_state,
                material=material
            )
            exit_mach = geometry.segments[-1].mach_number
            return abs(exit_mach - target_mach)
        
        # Initial guess and bounds
        x0 = np.array([15.0, 2.0])
        bounds = [(5.0, 30.0), (1.5, 5.0)]
        
        # Optimize
        result = minimize(
            objective,
            x0=x0,
            bounds=bounds,
            method='L-BFGS-B'
        )
        
        # Get optimized geometry
        return self.calculate_geometry(
            divergence_angle=result.x[0],
            length_ratio=result.x[1],
            chamber_state=chamber_state,
            material=material
        )
    
    def _calculate_throat_area(self, chamber_state: Dict[str, float]) -> float:
        """Calculate throat area based on chamber conditions.
        
        Args:
            chamber_state: Dictionary containing chamber conditions
            
        Returns:
            Throat area in square meters
        """
        # Use isentropic flow relations
        gamma = chamber_state['gamma']
        m_dot = chamber_state['mass_flow']
        p0 = chamber_state['pressure']
        T0 = chamber_state['temperature']
        R = chamber_state['gas_constant']
        
        # Critical pressure ratio
        pr_crit = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
        
        # Throat conditions
        pt = p0 * pr_crit
        Tt = T0 * (2 / (gamma + 1))
        
        # Calculate throat area
        return m_dot * np.sqrt(R * Tt) / (pt * np.sqrt(gamma))
    
    def _generate_segments(self,
                          throat_radius: float,
                          exit_radius: float,
                          length: float,
                          divergence_angle: float,
                          chamber_state: Dict[str, float],
                          material: Material) -> List[NozzleSegment]:
        """Generate nozzle segments with flow properties.
        
        Args:
            throat_radius: Throat radius in meters
            exit_radius: Exit radius in meters
            length: Nozzle length in meters
            divergence_angle: Divergence angle in degrees
            chamber_state: Dictionary containing chamber conditions
            material: Material properties for thermal analysis
            
        Returns:
            List of NozzleSegment objects
        """
        # Number of segments
        n_segments = 50
        
        # Generate x coordinates
        x = np.linspace(0, length, n_segments)
        
        # Generate radius profile (parabolic)
        r = np.linspace(throat_radius, exit_radius, n_segments)
        
        segments = []
        for i in range(n_segments - 1):
            # Calculate segment properties
            start_x = x[i]
            end_x = x[i + 1]
            start_radius = r[i]
            end_radius = r[i + 1]
            
            # Calculate segment angle
            angle = np.arctan2(end_radius - start_radius, end_x - start_x)
            angle_deg = np.degrees(angle)
            
            # Calculate segment length
            length = np.sqrt((end_x - start_x)**2 + (end_radius - start_radius)**2)
            
            # Calculate area ratio
            area_ratio = (end_radius / throat_radius)**2
            
            # Calculate flow properties
            flow_props = self.flow_solver.calculate_flow_properties(
                area_ratio=area_ratio,
                chamber_state=chamber_state
            )
            
            # Calculate thermal properties
            thermal_props = self._calculate_thermal_properties(
                flow_props=flow_props,
                material=material,
                radius=start_radius
            )
            
            # Create segment
            segment = NozzleSegment(
                start_x=start_x,
                end_x=end_x,
                start_radius=start_radius,
                end_radius=end_radius,
                angle=angle_deg,
                length=length,
                area_ratio=area_ratio,
                mach_number=flow_props['mach'],
                pressure=flow_props['pressure'],
                temperature=flow_props['temperature'],
                wall_temperature=thermal_props['wall_temperature'],
                heat_flux=thermal_props['heat_flux']
            )
            
            segments.append(segment)
        
        return segments
    
    def _calculate_performance_metrics(self,
                                     segments: List[NozzleSegment],
                                     chamber_state: Dict[str, float]) -> Dict[str, float]:
        """Calculate nozzle performance metrics.
        
        Args:
            segments: List of nozzle segments
            chamber_state: Dictionary containing chamber conditions
            
        Returns:
            Dictionary of performance metrics
        """
        # Get exit conditions
        exit_segment = segments[-1]
        
        # Calculate thrust coefficient
        thrust_coeff = self._calculate_thrust_coefficient(
            exit_pressure=exit_segment.pressure,
            exit_mach=exit_segment.mach_number,
            chamber_pressure=chamber_state['pressure'],
            ambient_pressure=chamber_state['ambient_pressure'],
            gamma=chamber_state['gamma']
        )
        
        # Calculate specific impulse
        isp = self._calculate_specific_impulse(
            thrust_coeff=thrust_coeff,
            chamber_pressure=chamber_state['pressure'],
            throat_area=segments[0].start_radius**2 * np.pi,
            mass_flow=chamber_state['mass_flow']
        )
        
        # Calculate efficiency
        efficiency = self._calculate_efficiency(
            thrust_coeff=thrust_coeff,
            ideal_thrust_coeff=self._calculate_ideal_thrust_coefficient(
                chamber_pressure=chamber_state['pressure'],
                ambient_pressure=chamber_state['ambient_pressure'],
                gamma=chamber_state['gamma']
            )
        )
        
        return {
            'thrust_coefficient': thrust_coeff,
            'specific_impulse': isp,
            'efficiency': efficiency,
            'exit_mach': exit_segment.mach_number
        }
    
    def _calculate_thrust_coefficient(self,
                                    exit_pressure: float,
                                    exit_mach: float,
                                    chamber_pressure: float,
                                    ambient_pressure: float,
                                    gamma: float) -> float:
        """Calculate thrust coefficient.
        
        Args:
            exit_pressure: Exit pressure in Pascals
            exit_mach: Exit Mach number
            chamber_pressure: Chamber pressure in Pascals
            ambient_pressure: Ambient pressure in Pascals
            gamma: Specific heat ratio
            
        Returns:
            Thrust coefficient
        """
        # Momentum term
        momentum_term = exit_mach * np.sqrt(
            (2 / (gamma - 1)) * (1 + (gamma - 1) / 2 * exit_mach**2)
        )
        
        # Pressure term
        pressure_term = (exit_pressure - ambient_pressure) / chamber_pressure
        
        return momentum_term + pressure_term
    
    def _calculate_specific_impulse(self,
                                  thrust_coeff: float,
                                  chamber_pressure: float,
                                  throat_area: float,
                                  mass_flow: float) -> float:
        """Calculate specific impulse.
        
        Args:
            thrust_coeff: Thrust coefficient
            chamber_pressure: Chamber pressure in Pascals
            throat_area: Throat area in square meters
            mass_flow: Mass flow rate in kg/s
            
        Returns:
            Specific impulse in seconds
        """
        thrust = thrust_coeff * chamber_pressure * throat_area
        return thrust / (mass_flow * 9.81)
    
    def _calculate_efficiency(self,
                            thrust_coeff: float,
                            ideal_thrust_coeff: float) -> float:
        """Calculate nozzle efficiency.
        
        Args:
            thrust_coeff: Actual thrust coefficient
            ideal_thrust_coeff: Ideal thrust coefficient
            
        Returns:
            Nozzle efficiency (0-1)
        """
        return thrust_coeff / ideal_thrust_coeff
    
    def _calculate_ideal_thrust_coefficient(self,
                                          chamber_pressure: float,
                                          ambient_pressure: float,
                                          gamma: float) -> float:
        """Calculate ideal thrust coefficient.
        
        Args:
            chamber_pressure: Chamber pressure in Pascals
            ambient_pressure: Ambient pressure in Pascals
            gamma: Specific heat ratio
            
        Returns:
            Ideal thrust coefficient
        """
        pr = ambient_pressure / chamber_pressure
        return np.sqrt(2 * gamma**2 / (gamma - 1) * (2 / (gamma + 1))**((gamma + 1) / (gamma - 1)) * (1 - pr**((gamma - 1) / gamma)))
    
    def _calculate_thermal_properties(self,
                                    flow_props: Dict[str, float],
                                    material: Material,
                                    radius: float) -> Dict[str, float]:
        """Calculate thermal properties for a nozzle segment.
        
        Args:
            flow_props: Dictionary of flow properties
            material: Material properties
            radius: Segment radius in meters
            
        Returns:
            Dictionary of thermal properties
        """
        # Calculate wall temperature using Bartz correlation
        wall_temp = self._calculate_wall_temperature(
            flow_temp=flow_props['temperature'],
            flow_mach=flow_props['mach'],
            material=material
        )
        
        # Calculate heat flux
        heat_flux = self._calculate_heat_flux(
            flow_temp=flow_props['temperature'],
            wall_temp=wall_temp,
            flow_mach=flow_props['mach'],
            radius=radius,
            material=material
        )
        
        return {
            'wall_temperature': wall_temp,
            'heat_flux': heat_flux
        }
    
    def _calculate_wall_temperature(self,
                                  flow_temp: float,
                                  flow_mach: float,
                                  material: Material) -> float:
        """Calculate wall temperature using Bartz correlation.
        
        Args:
            flow_temp: Flow temperature in Kelvin
            flow_mach: Flow Mach number
            material: Material properties
            
        Returns:
            Wall temperature in Kelvin
        """
        # Recovery temperature
        recovery_factor = np.sqrt(flow_mach)
        recovery_temp = flow_temp * (1 + 0.5 * (material.gamma - 1) * flow_mach**2 * recovery_factor)
        
        # Wall temperature (simplified)
        return recovery_temp * 0.8  # 80% of recovery temperature
    
    def _calculate_heat_flux(self,
                            flow_temp: float,
                            wall_temp: float,
                            flow_mach: float,
                            radius: float,
                            material: Material) -> float:
        """Calculate heat flux using Bartz correlation.
        
        Args:
            flow_temp: Flow temperature in Kelvin
            wall_temp: Wall temperature in Kelvin
            flow_mach: Flow Mach number
            radius: Segment radius in meters
            material: Material properties
            
        Returns:
            Heat flux in W/m²
        """
        # Heat transfer coefficient
        h = material.thermal_conductivity / radius
        
        # Heat flux
        return h * (flow_temp - wall_temp) 