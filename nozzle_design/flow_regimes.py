from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
from .thermodynamics import GasMixture, GasProperties

@dataclass
class FlowState:
    """Represents the state of flow at a point in the nozzle"""
    mach: float
    pressure: float  # Pa
    temperature: float  # K
    density: float  # kg/m³
    area_ratio: float  # A/A*
    is_shock: bool = False
    flow_regime: str = "subsonic"  # subsonic, choked, supersonic, over-expanded, under-expanded

class FlowRegime:
    """Base class for different flow regimes"""
    def __init__(self, gas_mixture: GasMixture):
        self.gas_mixture = gas_mixture
        self.gas_props = gas_mixture.get_mixture_properties(3000)  # Initial temperature

    def calculate_area_ratio(self, mach: float) -> float:
        """Calculate area ratio for given Mach number"""
        gamma = self.gas_props.gamma
        return (1/mach) * ((2/(gamma+1)) * (1 + (gamma-1)/2 * mach**2))**((gamma+1)/(2*(gamma-1)))

    def calculate_mach_from_area(self, area_ratio: float, is_subsonic: bool = True) -> float:
        """Calculate Mach number from area ratio using numerical solution"""
        def mach_equation(m):
            return self.calculate_area_ratio(m) - area_ratio

        # Initial guess based on whether we want subsonic or supersonic solution
        m0 = 0.5 if is_subsonic else 2.0
        return self._solve_newton(mach_equation, m0)

    def _solve_newton(self, func, x0: float, tol: float = 1e-6, max_iter: int = 100) -> float:
        """Newton-Raphson method for solving nonlinear equations"""
        x = x0
        for _ in range(max_iter):
            fx = func(x)
            if abs(fx) < tol:
                return x
            # Numerical derivative
            h = 1e-6
            dfx = (func(x + h) - fx) / h
            x = x - fx/dfx
        raise ValueError("Newton-Raphson method did not converge")

    def determine_flow_regime(self, 
                            inlet_pressure: float,
                            back_pressure: float,
                            area_ratio: float) -> str:
        """Determine the flow regime based on pressure ratios"""
        gamma = self.gas_props.gamma
        
        # Calculate critical pressure ratio
        critical_pressure_ratio = (2/(gamma+1))**(gamma/(gamma-1))
        
        # Calculate design pressure ratio for supersonic flow
        design_mach = self.calculate_mach_from_area(area_ratio, is_subsonic=False)
        design_pressure_ratio = (1 + (gamma-1)/2 * design_mach**2)**(-gamma/(gamma-1))
        
        # Determine flow regime
        if back_pressure > inlet_pressure:
            return "subsonic"  # Flow cannot start
        elif back_pressure > inlet_pressure * critical_pressure_ratio:
            return "choked"  # Flow is choked at throat
        elif back_pressure > inlet_pressure * design_pressure_ratio:
            return "over-expanded"  # Shock in nozzle
        else:
            return "under-expanded"  # Supersonic flow with expansion waves

class ConvergingNozzle(FlowRegime):
    """Handles flow in converging nozzles"""
    def calculate_flow(self, 
                      inlet_pressure: float,
                      back_pressure: float,
                      inlet_temp: float) -> List[FlowState]:
        """Calculate flow states through converging nozzle"""
        states = []
        gamma = self.gas_props.gamma
        
        # Calculate critical pressure ratio
        critical_pressure_ratio = (2/(gamma+1))**(gamma/(gamma-1))
        
        # Determine flow regime
        flow_regime = self.determine_flow_regime(inlet_pressure, back_pressure, 1.0)
        
        # Calculate exit state
        if flow_regime == "subsonic":
            # Subsonic flow
            exit_mach = self.calculate_mach_from_area(1.0, is_subsonic=True)
            exit_pressure = back_pressure
        else:  # choked
            # Choked flow
            exit_mach = 1.0
            exit_pressure = inlet_pressure * critical_pressure_ratio
        
        # Calculate exit state
        exit_temp = inlet_temp * (1 + (gamma-1)/2 * exit_mach**2)**(-1)
        exit_density = exit_pressure / (self.gas_props.molecular_weight * 8.314 * exit_temp)
        
        states.append(FlowState(
            mach=exit_mach,
            pressure=exit_pressure,
            temperature=exit_temp,
            density=exit_density,
            area_ratio=1.0,
            flow_regime=flow_regime
        ))
        
        return states

class ConvergingDivergingNozzle(FlowRegime):
    """Handles flow in converging-diverging nozzles"""
    def calculate_flow(self,
                      inlet_pressure: float,
                      back_pressure: float,
                      inlet_temp: float,
                      area_ratio: float) -> List[FlowState]:
        """Calculate flow states through CD nozzle including shock analysis"""
        states = []
        gamma = self.gas_props.gamma
        
        # Determine flow regime
        flow_regime = self.determine_flow_regime(inlet_pressure, back_pressure, area_ratio)
        
        if flow_regime == "subsonic":
            # Subsonic flow throughout
            exit_mach = self.calculate_mach_from_area(area_ratio, is_subsonic=True)
            states.append(self._calculate_flow_state(
                exit_mach, inlet_pressure, inlet_temp, area_ratio, flow_regime))
            
        elif flow_regime == "choked":
            # Flow is choked but not supersonic
            throat_mach = 1.0
            throat_state = self._calculate_flow_state(
                throat_mach, inlet_pressure, inlet_temp, 1.0, flow_regime)
            states.append(throat_state)
            
            # Calculate subsonic exit state
            exit_mach = self.calculate_mach_from_area(area_ratio, is_subsonic=True)
            states.append(self._calculate_flow_state(
                exit_mach, throat_state.pressure, throat_state.temperature, 
                area_ratio, flow_regime))
            
        elif flow_regime == "over-expanded":
            # Calculate shock location
            shock_location = self._find_shock_location(area_ratio, back_pressure/inlet_pressure)
            if shock_location is not None:
                states.extend(self._calculate_shock_flow(
                    inlet_pressure, inlet_temp, area_ratio, shock_location, flow_regime))
            else:
                # Subsonic flow throughout
                exit_mach = self.calculate_mach_from_area(area_ratio, is_subsonic=True)
                states.append(self._calculate_flow_state(
                    exit_mach, inlet_pressure, inlet_temp, area_ratio, flow_regime))
        else:  # under-expanded
            # Supersonic flow throughout
            exit_mach = self.calculate_mach_from_area(area_ratio, is_subsonic=False)
            states.append(self._calculate_flow_state(
                exit_mach, inlet_pressure, inlet_temp, area_ratio, flow_regime))
        
        return states

    def _find_shock_location(self, 
                           area_ratio: float, 
                           pressure_ratio: float) -> Optional[float]:
        """Find the location of normal shock in the nozzle"""
        # Calculate design pressure ratio
        gamma = self.gas_props.gamma
        design_mach = self.calculate_mach_from_area(area_ratio, is_subsonic=False)
        design_pressure_ratio = (1 + (gamma-1)/2 * design_mach**2)**(-gamma/(gamma-1))
        
        # If back pressure is higher than design, shock must exist
        if pressure_ratio > design_pressure_ratio:
            # Simplified shock location calculation
            # In reality, this should use more sophisticated methods
            return 1.5  # Place shock at 1.5 times throat area
        return None

    def _calculate_shock_flow(self,
                            inlet_pressure: float,
                            inlet_temp: float,
                            area_ratio: float,
                            shock_location: float,
                            flow_regime: str) -> List[FlowState]:
        """Calculate flow states including shock"""
        states = []
        gamma = self.gas_props.gamma
        
        # Pre-shock state
        pre_shock_mach = self.calculate_mach_from_area(shock_location, is_subsonic=False)
        pre_shock_state = self._calculate_flow_state(
            pre_shock_mach, inlet_pressure, inlet_temp, shock_location, flow_regime)
        states.append(pre_shock_state)
        
        # Post-shock state
        post_shock_mach = np.sqrt((1 + (gamma-1)/2 * pre_shock_mach**2) / 
                                (gamma * pre_shock_mach**2 - (gamma-1)/2))
        post_shock_pressure = pre_shock_state.pressure * (
            (2*gamma*pre_shock_mach**2 - (gamma-1)) / (gamma+1))
        post_shock_temp = pre_shock_state.temperature * (
            (2*gamma*pre_shock_mach**2 - (gamma-1)) * 
            ((gamma-1)*pre_shock_mach**2 + 2) / 
            ((gamma+1)**2 * pre_shock_mach**2))
        
        post_shock_state = FlowState(
            mach=post_shock_mach,
            pressure=post_shock_pressure,
            temperature=post_shock_temp,
            density=post_shock_pressure / (self.gas_props.molecular_weight * 8.314 * post_shock_temp),
            area_ratio=shock_location,
            is_shock=True,
            flow_regime=flow_regime
        )
        states.append(post_shock_state)
        
        # Exit state
        exit_mach = self.calculate_mach_from_area(area_ratio/shock_location, is_subsonic=True)
        exit_state = self._calculate_flow_state(
            exit_mach, post_shock_pressure, post_shock_temp, 
            area_ratio/shock_location, flow_regime)
        states.append(exit_state)
        
        return states

    def _calculate_flow_state(self,
                            mach: float,
                            reference_pressure: float,
                            reference_temp: float,
                            area_ratio: float,
                            flow_regime: str) -> FlowState:
        """Calculate flow state for given Mach number and reference conditions"""
        gamma = self.gas_props.gamma
        
        pressure = reference_pressure * (1 + (gamma-1)/2 * mach**2)**(-gamma/(gamma-1))
        temperature = reference_temp * (1 + (gamma-1)/2 * mach**2)**(-1)
        density = pressure / (self.gas_props.molecular_weight * 8.314 * temperature)
        
        return FlowState(
            mach=mach,
            pressure=pressure,
            temperature=temperature,
            density=density,
            area_ratio=area_ratio,
            flow_regime=flow_regime
        ) 