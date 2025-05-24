from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.optimize import minimize
from .thermodynamics import GasProperties
from .combustion import CombustionState
from .engineering_calculations import NozzleGeometryCalculator, NozzleSegment

@dataclass
class NozzleGeometry:
    """Represents optimized nozzle geometry parameters"""
    area_ratio: float
    length: float
    divergence_angle: float  # degrees
    throat_radius: float
    exit_radius: float
    contour_points: List[Tuple[float, float]]  # (x, y) coordinates
    performance_metrics: Dict[str, float]
    segments: List[NozzleSegment]

class NozzleOptimizer:
    """Handles nozzle geometry optimization calculations"""
    
    def __init__(self):
        self.calculator = NozzleGeometryCalculator()
    
    def optimize_for_thrust(self,
                          target_thrust: float,
                          chamber_state: CombustionState,
                          back_pressure: float) -> NozzleGeometry:
        """Optimize nozzle geometry for target thrust"""
        # Calculate required exit Mach number
        exit_mach = self._calculate_required_mach(
            target_thrust, chamber_state, back_pressure)
        
        # Optimize geometry for this Mach number
        return self.optimize_for_mach(exit_mach, chamber_state, back_pressure)
    
    def optimize_for_mach(self,
                         target_mach: float,
                         chamber_state: CombustionState,
                         back_pressure: float) -> NozzleGeometry:
        """Optimize nozzle geometry for target Mach number"""
        # Calculate required area ratio
        area_ratio = self.calculator.calculate_area_ratio(
            target_mach, chamber_state.gas_properties)
        
        # Calculate throat radius from mass flow
        throat_radius = self.calculator.calculate_throat_radius(chamber_state)
        
        # Optimize divergence angle and length
        divergence_angle, length = self._optimize_divergence_and_length(
            area_ratio, throat_radius, chamber_state.gas_properties)
        
        # Calculate exit radius
        exit_radius = throat_radius * np.sqrt(area_ratio)
        
        # Generate contour points
        contour_points = self._generate_contour(
            throat_radius, exit_radius, length, divergence_angle)
        
        # Calculate segments
        segments = self.calculator.calculate_segments(
            throat_radius, exit_radius, length, divergence_angle, chamber_state)
        
        # Calculate performance metrics
        performance = self.calculator.calculate_performance_metrics(
            chamber_state, back_pressure, area_ratio, divergence_angle)
        
        return NozzleGeometry(
            area_ratio=area_ratio,
            length=length,
            divergence_angle=divergence_angle,
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            contour_points=contour_points,
            performance_metrics=performance,
            segments=segments
        )
    
    def _calculate_required_mach(self,
                               target_thrust: float,
                               chamber_state: CombustionState,
                               back_pressure: float) -> float:
        """Calculate required exit Mach number for target thrust"""
        def thrust_error(mach):
            # Calculate exit conditions
            flow_props = self.calculator.calculate_flow_properties(mach, chamber_state)
            exit_pressure = flow_props['pressure']
            exit_temp = flow_props['temperature']
            
            # Calculate exit velocity
            exit_velocity = mach * np.sqrt(chamber_state.gas_properties.gamma * 8.314 * exit_temp / 
                                         chamber_state.gas_properties.molecular_weight)
            
            # Calculate exit area
            area_ratio = self.calculator.calculate_area_ratio(mach, chamber_state.gas_properties)
            throat_area = np.pi * (self.calculator.calculate_throat_radius(chamber_state))**2
            exit_area = throat_area * area_ratio
            
            # Calculate thrust
            thrust = chamber_state.mass_flow * exit_velocity + (
                exit_pressure - back_pressure) * exit_area
            
            return abs(thrust - target_thrust)
        
        # Optimize for Mach number
        result = minimize(thrust_error, x0=2.0, bounds=[(1.0, 10.0)])
        return result.x[0]
    
    def _optimize_divergence_and_length(self,
                                      area_ratio: float,
                                      throat_radius: float,
                                      gas_properties: GasProperties) -> Tuple[float, float]:
        """Optimize divergence angle and length for given area ratio"""
        # Objective function to minimize losses
        def loss_function(params):
            divergence, length_ratio = params
            
            # Calculate length
            length = length_ratio * throat_radius * 2
            
            # Calculate losses
            # 1. Divergence losses (increases with angle)
            divergence_loss = (divergence / self.calculator.MAX_DIVERGENCE_ANGLE)**2
            
            # 2. Length losses (increases with length)
            length_loss = (length_ratio / self.calculator.MAX_LENGTH_RATIO)**2
            
            # 3. Wall friction losses (increases with length)
            friction_loss = length_ratio * 0.1
            
            return divergence_loss + length_loss + friction_loss
        
        # Constraints
        bounds = [
            (self.calculator.MIN_DIVERGENCE_ANGLE, self.calculator.MAX_DIVERGENCE_ANGLE),
            (self.calculator.MIN_LENGTH_RATIO, self.calculator.MAX_LENGTH_RATIO)
        ]
        
        # Optimize
        result = minimize(
            loss_function,
            x0=[10.0, 2.0],  # Initial guess
            bounds=bounds,
            method='L-BFGS-B'
        )
        
        divergence_angle, length_ratio = result.x
        length = length_ratio * throat_radius * 2
        
        return divergence_angle, length
    
    def _generate_contour(self,
                         throat_radius: float,
                         exit_radius: float,
                         length: float,
                         divergence_angle: float) -> List[Tuple[float, float]]:
        """Generate nozzle contour points using Rao's method"""
        # Number of points for contour
        n_points = 100
        
        # Generate x coordinates
        x = np.linspace(0, length, n_points)
        
        # Calculate y coordinates using Rao's method
        y = []
        for xi in x:
            y.append(self.calculator.calculate_radius_at_x(
                xi, throat_radius, exit_radius, length, divergence_angle))
        
        return list(zip(x, y)) 