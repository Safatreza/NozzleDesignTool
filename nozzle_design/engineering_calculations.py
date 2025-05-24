from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.optimize import minimize
from .thermodynamics import GasProperties
from .combustion import CombustionState

@dataclass
class MaterialProperties:
    """Properties of nozzle material"""
    name: str
    yield_strength: float  # Pa
    thermal_conductivity: float  # W/m·K
    specific_heat: float  # J/kg·K
    density: float  # kg/m³
    max_temperature: float  # K
    emissivity: float  # dimensionless

@dataclass
class HeatTransferResult:
    """Results of heat transfer analysis"""
    wall_temperature: float  # K
    heat_flux: float  # W/m²
    cooling_requirement: float  # W
    safety_factor: float  # dimensionless

@dataclass
class NozzleSegment:
    """Represents a segment of the nozzle"""
    start_x: float
    end_x: float
    start_radius: float
    end_radius: float
    angle: float  # degrees
    length: float
    area_ratio: float
    mach_number: float
    pressure: float
    temperature: float
    wall_temperature: float  # Added wall temperature
    heat_flux: float  # Added heat flux

class NozzleGeometryCalculator:
    """Handles engineering calculations for nozzle geometry"""
    
    def __init__(self):
        # Constants for optimization
        self.MAX_DIVERGENCE_ANGLE = 15.0  # degrees
        self.MIN_DIVERGENCE_ANGLE = 5.0   # degrees
        self.MAX_LENGTH_RATIO = 3.0       # L/D ratio
        self.MIN_LENGTH_RATIO = 1.5       # L/D ratio
        
        # Segment parameters
        self.N_SEGMENTS = 10  # Number of segments to divide nozzle into
        self.THRROAT_SEGMENT_RATIO = 0.15  # Length ratio for throat segment
        
        # Heat transfer parameters
        self.STEFAN_BOLTZMANN = 5.67e-8  # W/m²·K⁴
        self.PRANDTL_NUMBER = 0.7  # Typical for gases
        self.WALL_THICKNESS = 0.002  # m, default wall thickness
        
        # Default materials
        self.DEFAULT_MATERIALS = {
            'copper': MaterialProperties(
                name='Copper',
                yield_strength=250e6,
                thermal_conductivity=400,
                specific_heat=385,
                density=8960,
                max_temperature=1356,
                emissivity=0.1
            ),
            'inconel': MaterialProperties(
                name='Inconel 718',
                yield_strength=1034e6,
                thermal_conductivity=11.4,
                specific_heat=435,
                density=8190,
                max_temperature=1473,
                emissivity=0.3
            ),
            'steel': MaterialProperties(
                name='Stainless Steel 304',
                yield_strength=215e6,
                thermal_conductivity=16.2,
                specific_heat=500,
                density=8000,
                max_temperature=1673,
                emissivity=0.2
            )
        }

    def calculate_area_ratio(self, mach: float, gas_properties: GasProperties) -> float:
        """Calculate area ratio for given Mach number"""
        gamma = gas_properties.gamma
        return (1/mach) * ((2/(gamma+1)) * (1 + (gamma-1)/2 * mach**2))**((gamma+1)/(2*(gamma-1)))

    def calculate_throat_radius(self, chamber_state: CombustionState) -> float:
        """Calculate throat radius from mass flow rate"""
        gamma = chamber_state.gas_properties.gamma
        R = 8.314 / chamber_state.gas_properties.molecular_weight
        
        # Calculate critical flow parameter
        critical_flow = np.sqrt(gamma/R) * (2/(gamma+1))**((gamma+1)/(2*(gamma-1)))
        
        # Calculate throat area
        throat_area = chamber_state.mass_flow / (
            chamber_state.pressure * critical_flow * np.sqrt(chamber_state.temperature))
        
        return np.sqrt(throat_area / np.pi)

    def calculate_mach_from_area(self, area_ratio: float, gamma: float) -> float:
        """Calculate Mach number from area ratio"""
        def mach_equation(m):
            return (1/m) * ((2/(gamma+1)) * (1 + (gamma-1)/2 * m**2))**((gamma+1)/(2*(gamma-1))) - area_ratio
        
        # Use Newton-Raphson method
        m = 2.0  # Initial guess
        for _ in range(10):
            f = mach_equation(m)
            if abs(f) < 1e-6:
                break
            df = (mach_equation(m + 1e-6) - f) / 1e-6
            m = m - f/df
        
        return m

    def calculate_flow_properties(self,
                                mach: float,
                                chamber_state: CombustionState) -> Dict[str, float]:
        """Calculate flow properties for given Mach number"""
        gamma = chamber_state.gas_properties.gamma
        
        pressure = chamber_state.pressure * (
            1 + (gamma-1)/2 * mach**2)**(-gamma/(gamma-1))
        temperature = chamber_state.temperature * (
            1 + (gamma-1)/2 * mach**2)**(-1)
        
        return {
            'pressure': pressure,
            'temperature': temperature,
            'mach': mach
        }

    def calculate_rao_contour(self,
                            throat_radius: float,
                            exit_radius: float,
                            length: float,
                            divergence_angle: float) -> List[Tuple[float, float]]:
        """Calculate nozzle contour using Rao's method"""
        n_points = 100
        x = np.linspace(0, length, n_points)
        y = []
        
        # Parameters for Rao's method
        theta_n = np.radians(divergence_angle)  # Nozzle angle
        theta_e = np.radians(7.5)  # Exit angle
        R1 = throat_radius * 1.5  # Radius of curvature at throat
        R2 = throat_radius * 0.382  # Radius of curvature at inflection
        
        for xi in x:
            if xi < length * self.THRROAT_SEGMENT_RATIO:
                # Throat region (circular arc)
                y.append(throat_radius + R1 - np.sqrt(R1**2 - (xi - length*self.THRROAT_SEGMENT_RATIO)**2))
            elif xi < length * 0.6:
                # First parabolic section
                t = (xi - length*self.THRROAT_SEGMENT_RATIO) / (length * 0.45)
                y.append(throat_radius + R2 * (1 - np.cos(theta_n * t)))
            else:
                # Second parabolic section
                t = (xi - length*0.6) / (length * 0.4)
                y.append(exit_radius - (exit_radius - throat_radius) * 
                        (1 - t)**2 * np.cos(theta_e))
        
        return list(zip(x, y))

    def calculate_heat_transfer(self,
                              segment: NozzleSegment,
                              chamber_state: CombustionState,
                              material: MaterialProperties) -> HeatTransferResult:
        """Calculate heat transfer for a nozzle segment"""
        # Calculate recovery temperature
        gamma = chamber_state.gas_properties.gamma
        Pr = self.PRANDTL_NUMBER
        recovery_factor = np.sqrt(Pr)
        recovery_temp = segment.temperature * (1 + recovery_factor * (gamma-1)/2 * segment.mach_number**2)
        
        # Calculate heat transfer coefficient (Bartz equation)
        D = 2 * segment.end_radius  # Diameter
        viscosity = 1.5e-5  # Approximate viscosity of combustion gases
        cp = chamber_state.gas_properties.cp
        
        # Calculate local heat transfer coefficient
        h = 0.026 * (segment.mach_number**0.8) * (cp**0.8) * (chamber_state.pressure**0.8) * (D**-0.2) * (viscosity**-0.2)
        
        # Calculate heat flux
        heat_flux = h * (recovery_temp - material.max_temperature)
        
        # Calculate wall temperature using thermal resistance
        thermal_resistance = self.WALL_THICKNESS / material.thermal_conductivity
        wall_temp = recovery_temp - heat_flux * thermal_resistance
        
        # Calculate cooling requirement
        segment_area = np.pi * (segment.end_radius**2 - segment.start_radius**2)
        cooling_requirement = heat_flux * segment_area
        
        # Calculate safety factor
        safety_factor = min(
            material.yield_strength / (segment.pressure * segment.end_radius / self.WALL_THICKNESS),
            (material.max_temperature - wall_temp) / wall_temp
        )
        
        return HeatTransferResult(
            wall_temperature=wall_temp,
            heat_flux=heat_flux,
            cooling_requirement=cooling_requirement,
            safety_factor=safety_factor
        )

    def calculate_material_constraints(self,
                                    segment: NozzleSegment,
                                    material: MaterialProperties) -> Dict[str, float]:
        """Calculate material constraints for a nozzle segment"""
        # Calculate hoop stress
        hoop_stress = segment.pressure * segment.end_radius / self.WALL_THICKNESS
        
        # Calculate thermal stress
        thermal_expansion = 12e-6  # Typical thermal expansion coefficient
        thermal_stress = material.thermal_conductivity * thermal_expansion * (
            segment.temperature - 293)  # 293K is room temperature
        
        # Calculate combined stress
        combined_stress = hoop_stress + thermal_stress
        
        # Calculate safety factors
        stress_safety_factor = material.yield_strength / combined_stress
        temp_safety_factor = (material.max_temperature - segment.temperature) / segment.temperature
        
        return {
            'hoop_stress': hoop_stress,
            'thermal_stress': thermal_stress,
            'combined_stress': combined_stress,
            'stress_safety_factor': stress_safety_factor,
            'temp_safety_factor': temp_safety_factor
        }

    def calculate_segments(self,
                         throat_radius: float,
                         exit_radius: float,
                         length: float,
                         divergence_angle: float,
                         chamber_state: CombustionState,
                         material: MaterialProperties) -> List[NozzleSegment]:
        """Calculate nozzle segments with flow and heat transfer properties"""
        segments = []
        gamma = chamber_state.gas_properties.gamma
        
        # Calculate throat segment
        throat_length = length * self.THRROAT_SEGMENT_RATIO
        throat_segment = NozzleSegment(
            start_x=0,
            end_x=throat_length,
            start_radius=throat_radius * 0.8,
            end_radius=throat_radius,
            angle=0,
            length=throat_length,
            area_ratio=1.0,
            mach_number=1.0,
            pressure=chamber_state.pressure * (2/(gamma+1))**(gamma/(gamma-1)),
            temperature=chamber_state.temperature * (2/(gamma+1)),
            wall_temperature=0,  # Will be calculated
            heat_flux=0  # Will be calculated
        )
        
        # Calculate heat transfer for throat segment
        heat_transfer = self.calculate_heat_transfer(throat_segment, chamber_state, material)
        throat_segment.wall_temperature = heat_transfer.wall_temperature
        throat_segment.heat_flux = heat_transfer.heat_flux
        segments.append(throat_segment)
        
        # Calculate diverging section segments
        div_length = length - throat_length
        segment_length = div_length / (self.N_SEGMENTS - 1)
        
        for i in range(1, self.N_SEGMENTS):
            # Calculate segment positions
            start_x = throat_length + (i-1) * segment_length
            end_x = throat_length + i * segment_length
            
            # Calculate segment radii using Rao's method
            contour_points = self.calculate_rao_contour(
                throat_radius, exit_radius, length, divergence_angle)
            start_radius = np.interp(start_x, [p[0] for p in contour_points], [p[1] for p in contour_points])
            end_radius = np.interp(end_x, [p[0] for p in contour_points], [p[1] for p in contour_points])
            
            # Calculate segment angle
            angle = np.degrees(np.arctan2(end_radius - start_radius, segment_length))
            
            # Calculate area ratio
            area_ratio = (end_radius/throat_radius)**2
            
            # Calculate Mach number
            mach = self.calculate_mach_from_area(area_ratio, gamma)
            
            # Calculate pressure and temperature
            flow_props = self.calculate_flow_properties(mach, chamber_state)
            
            segment = NozzleSegment(
                start_x=start_x,
                end_x=end_x,
                start_radius=start_radius,
                end_radius=end_radius,
                angle=angle,
                length=segment_length,
                area_ratio=area_ratio,
                mach_number=mach,
                pressure=flow_props['pressure'],
                temperature=flow_props['temperature'],
                wall_temperature=0,  # Will be calculated
                heat_flux=0  # Will be calculated
            )
            
            # Calculate heat transfer for segment
            heat_transfer = self.calculate_heat_transfer(segment, chamber_state, material)
            segment.wall_temperature = heat_transfer.wall_temperature
            segment.heat_flux = heat_transfer.heat_flux
            
            segments.append(segment)
        
        return segments

    def calculate_thrust_coefficient(self,
                                   mach: float,
                                   gamma: float,
                                   pressure_ratio: float) -> float:
        """Calculate thrust coefficient"""
        term1 = np.sqrt(2*gamma**2/(gamma-1) * (2/(gamma+1))**((gamma+1)/(gamma-1)) * 
                       (1 - pressure_ratio**((gamma-1)/gamma)))
        
        # Calculate area ratio
        area_ratio = self.calculate_area_ratio(mach, gamma)
        
        term2 = (pressure_ratio - 1) * area_ratio
        
        return term1 + term2

    def calculate_performance_metrics(self,
                                   chamber_state: CombustionState,
                                   back_pressure: float,
                                   area_ratio: float,
                                   divergence_angle: float) -> Dict[str, float]:
        """Calculate performance metrics for the nozzle"""
        gamma = chamber_state.gas_properties.gamma
        
        # Calculate exit Mach number
        exit_mach = self.calculate_mach_from_area(area_ratio, gamma)
        
        # Calculate thrust coefficient
        thrust_coef = self.calculate_thrust_coefficient(
            exit_mach, gamma, back_pressure/chamber_state.pressure)
        
        # Calculate specific impulse
        isp = thrust_coef * chamber_state.characteristic_velocity / 9.81
        
        # Calculate efficiency
        efficiency = thrust_coef / self.calculate_thrust_coefficient(
            exit_mach, gamma, back_pressure/chamber_state.pressure)
        
        return {
            'thrust_coefficient': thrust_coef,
            'specific_impulse': isp,
            'efficiency': efficiency,
            'exit_mach': exit_mach
        } 