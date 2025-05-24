"""Module for compressible flow calculations in rocket nozzles."""

from typing import Dict, Optional
import numpy as np
from scipy.optimize import fsolve

class FlowSolver:
    """Solver for compressible flow calculations in rocket nozzles."""
    
    def __init__(self, gamma: float = 1.4, R: float = 287.0):
        """Initialize the flow solver.
        
        Args:
            gamma: Specific heat ratio (default: 1.4 for air)
            R: Gas constant in J/(kg·K) (default: 287.0 for air)
        """
        self.gamma = gamma
        self.R = R
    
    def calculate_flow_properties(self,
                                area_ratio: float,
                                chamber_state: Dict[str, float]) -> Dict[str, float]:
        """Calculate flow properties for a given area ratio.
        
        Args:
            area_ratio: Area ratio (A/A*)
            chamber_state: Dictionary containing chamber conditions
            
        Returns:
            Dictionary of flow properties (Mach, pressure, temperature)
        """
        # Get chamber conditions
        p0 = chamber_state['pressure']
        T0 = chamber_state['temperature']
        
        # Calculate Mach number
        mach = self._calculate_mach_from_area_ratio(area_ratio)
        
        # Calculate pressure
        pressure = self._calculate_pressure(mach, p0)
        
        # Calculate temperature
        temperature = self._calculate_temperature(mach, T0)
        
        return {
            'mach': mach,
            'pressure': pressure,
            'temperature': temperature
        }
    
    def _calculate_mach_from_area_ratio(self, area_ratio: float) -> float:
        """Calculate Mach number from area ratio using isentropic relations.
        
        Args:
            area_ratio: Area ratio (A/A*)
            
        Returns:
            Mach number
        """
        def area_ratio_equation(M: float) -> float:
            """Equation for area ratio as a function of Mach number."""
            return (1/M) * ((2/(self.gamma + 1)) * (1 + (self.gamma - 1)/2 * M**2))**((self.gamma + 1)/(2*(self.gamma - 1))) - area_ratio
        
        # Initial guess for subsonic solution
        M_subsonic = fsolve(area_ratio_equation, 0.5)[0]
        
        # Initial guess for supersonic solution
        M_supersonic = fsolve(area_ratio_equation, 2.0)[0]
        
        # Return the appropriate solution based on area ratio
        if area_ratio < 1.0:
            return M_subsonic
        else:
            return M_supersonic
    
    def _calculate_pressure(self, mach: float, p0: float) -> float:
        """Calculate static pressure from Mach number and total pressure.
        
        Args:
            mach: Mach number
            p0: Total pressure in Pascals
            
        Returns:
            Static pressure in Pascals
        """
        return p0 / (1 + (self.gamma - 1)/2 * mach**2)**(self.gamma/(self.gamma - 1))
    
    def _calculate_temperature(self, mach: float, T0: float) -> float:
        """Calculate static temperature from Mach number and total temperature.
        
        Args:
            mach: Mach number
            T0: Total temperature in Kelvin
            
        Returns:
            Static temperature in Kelvin
        """
        return T0 / (1 + (self.gamma - 1)/2 * mach**2)
    
    def calculate_mass_flow(self,
                          throat_area: float,
                          chamber_state: Dict[str, float]) -> float:
        """Calculate mass flow rate through the nozzle.
        
        Args:
            throat_area: Throat area in square meters
            chamber_state: Dictionary containing chamber conditions
            
        Returns:
            Mass flow rate in kg/s
        """
        p0 = chamber_state['pressure']
        T0 = chamber_state['temperature']
        
        # Critical pressure ratio
        pr_crit = (2/(self.gamma + 1))**(self.gamma/(self.gamma - 1))
        
        # Critical temperature ratio
        Tr_crit = 2/(self.gamma + 1)
        
        # Critical density
        rho_crit = p0 * pr_crit / (self.R * T0 * Tr_crit)
        
        # Critical velocity
        v_crit = np.sqrt(self.gamma * self.R * T0 * Tr_crit)
        
        return rho_crit * v_crit * throat_area
    
    def calculate_thrust(self,
                        exit_area: float,
                        chamber_state: Dict[str, float],
                        ambient_pressure: float) -> float:
        """Calculate thrust from nozzle exit conditions.
        
        Args:
            exit_area: Exit area in square meters
            chamber_state: Dictionary containing chamber conditions
            ambient_pressure: Ambient pressure in Pascals
            
        Returns:
            Thrust in Newtons
        """
        # Calculate exit conditions
        exit_props = self.calculate_flow_properties(
            area_ratio=exit_area/chamber_state['throat_area'],
            chamber_state=chamber_state
        )
        
        # Calculate mass flow
        m_dot = self.calculate_mass_flow(
            throat_area=chamber_state['throat_area'],
            chamber_state=chamber_state
        )
        
        # Calculate exit velocity
        v_exit = exit_props['mach'] * np.sqrt(self.gamma * self.R * exit_props['temperature'])
        
        # Calculate thrust
        momentum_thrust = m_dot * v_exit
        pressure_thrust = (exit_props['pressure'] - ambient_pressure) * exit_area
        
        return momentum_thrust + pressure_thrust 