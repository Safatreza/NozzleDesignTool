"""Module for compressible flow calculations."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.optimize import fsolve

class FlowSolver:
    """Class for compressible flow calculations."""
    
    def __init__(self, gamma: float = 1.4, R: float = 287.0):
        """Initialize flow solver.
        
        Args:
            gamma: Specific heat ratio
            R: Gas constant (J/kg/K)
        """
        self.gamma = gamma
        self.R = R
    
    def calculate_flow_properties(self,
                                mach: float,
                                total_pressure: float,
                                total_temperature: float) -> Dict[str, float]:
        """Calculate flow properties at given Mach number.
        
        Args:
            mach: Mach number
            total_pressure: Total pressure in Pa
            total_temperature: Total temperature in K
            
        Returns:
            Dictionary of flow properties
        """
        # Calculate static pressure
        pressure = total_pressure / (1 + 0.5 * (self.gamma - 1) * mach**2)**(self.gamma / (self.gamma - 1))
        
        # Calculate static temperature
        temperature = total_temperature / (1 + 0.5 * (self.gamma - 1) * mach**2)
        
        # Calculate density
        density = pressure / (self.R * temperature)
        
        # Calculate velocity
        velocity = mach * np.sqrt(self.gamma * self.R * temperature)
        
        return {
            'pressure': pressure,
            'temperature': temperature,
            'density': density,
            'velocity': velocity
        }
    
    def calculate_mach_from_area_ratio(self,
                                     area_ratio: float,
                                     mach_guess: float = 2.0) -> float:
        """Calculate Mach number from area ratio.
        
        Args:
            area_ratio: Area ratio (A/A*)
            mach_guess: Initial guess for Mach number
            
        Returns:
            Mach number
        """
        def area_ratio_eq(m):
            return (1/m) * ((2/(self.gamma + 1)) * (1 + 0.5 * (self.gamma - 1) * m**2))**((self.gamma + 1)/(2 * (self.gamma - 1))) - area_ratio
        
        # Solve for Mach number
        mach = fsolve(area_ratio_eq, mach_guess)[0]
        
        return mach
    
    def calculate_throat_area(self,
                            mass_flow: float,
                            total_pressure: float,
                            total_temperature: float) -> float:
        """Calculate throat area from mass flow.
        
        Args:
            mass_flow: Mass flow rate in kg/s
            total_pressure: Total pressure in Pa
            total_temperature: Total temperature in K
            
        Returns:
            Throat area in m^2
        """
        # Calculate critical pressure ratio
        critical_pressure_ratio = (2/(self.gamma + 1))**(self.gamma/(self.gamma - 1))
        
        # Calculate critical temperature ratio
        critical_temperature_ratio = 2/(self.gamma + 1)
        
        # Calculate throat pressure and temperature
        throat_pressure = total_pressure * critical_pressure_ratio
        throat_temperature = total_temperature * critical_temperature_ratio
        
        # Calculate throat density
        throat_density = throat_pressure / (self.R * throat_temperature)
        
        # Calculate throat velocity
        throat_velocity = np.sqrt(self.gamma * self.R * throat_temperature)
        
        # Calculate throat area
        throat_area = mass_flow / (throat_density * throat_velocity)
        
        return throat_area
    
    def calculate_thrust_coefficient(self,
                                   expansion_ratio: float,
                                   chamber_pressure: float,
                                   exit_pressure: float = 101325.0) -> float:
        """Calculate thrust coefficient.
        
        Args:
            expansion_ratio: Nozzle expansion ratio
            chamber_pressure: Chamber pressure in Pa
            exit_pressure: Exit pressure in Pa
            
        Returns:
            Thrust coefficient
        """
        # Calculate exit Mach number
        exit_mach = self.calculate_mach_from_area_ratio(expansion_ratio)
        
        # Calculate exit pressure ratio
        exit_pressure_ratio = (1 + 0.5 * (self.gamma - 1) * exit_mach**2)**(self.gamma / (self.gamma - 1))
        
        # Calculate ideal thrust coefficient
        cf_ideal = np.sqrt(2 * self.gamma**2 / (self.gamma - 1) * 
                          (2/(self.gamma + 1))**((self.gamma + 1)/(self.gamma - 1)) *
                          (1 - (exit_pressure/chamber_pressure)**((self.gamma - 1)/self.gamma)))
        
        # Add pressure thrust term
        cf = cf_ideal + expansion_ratio * (exit_pressure - exit_pressure_ratio * chamber_pressure) / chamber_pressure
        
        return cf
    
    def calculate_specific_impulse(self,
                                 thrust_coefficient: float,
                                 chamber_temperature: float) -> float:
        """Calculate specific impulse.
        
        Args:
            thrust_coefficient: Thrust coefficient
            chamber_temperature: Chamber temperature in K
            
        Returns:
            Specific impulse in seconds
        """
        # Calculate characteristic velocity
        c_star = np.sqrt(self.gamma * self.R * chamber_temperature) / self.gamma
        
        # Calculate specific impulse
        isp = thrust_coefficient * c_star / 9.81
        
        return isp
    
    def calculate_efficiency(self,
                           actual_thrust: float,
                           ideal_thrust: float) -> float:
        """Calculate nozzle efficiency.
        
        Args:
            actual_thrust: Actual thrust in N
            ideal_thrust: Ideal thrust in N
            
        Returns:
            Nozzle efficiency (0-1)
        """
        return actual_thrust / ideal_thrust

    def calculate_flow_properties_from_area_ratio(self, area_ratio: float, chamber_state: Dict[str, float]) -> Dict[str, float]:
        """Calculate flow properties from area ratio and chamber state."""
        mach = self.calculate_mach_from_area_ratio(area_ratio)
        return self.calculate_flow_properties(
            mach,
            chamber_state['pressure'],
            chamber_state['temperature']
        )

    def _calculate_mach_from_area_ratio(self, area_ratio: float, mach_guess: float = 2.0) -> float:
        """Alias for calculate_mach_from_area_ratio for test compatibility."""
        return self.calculate_mach_from_area_ratio(area_ratio, mach_guess)

    def _calculate_pressure(self, mach: float, p0: float) -> float:
        """Calculate static pressure from Mach number and total pressure."""
        return p0 / (1 + (self.gamma - 1)/2 * mach**2)**(self.gamma/(self.gamma - 1))

    def _calculate_temperature(self, mach: float, T0: float) -> float:
        """Calculate static temperature from Mach number and total temperature."""
        return T0 / (1 + (self.gamma - 1)/2 * mach**2)

    def calculate_mass_flow(self, throat_area: float, chamber_state: Dict[str, float]) -> float:
        """Calculate mass flow rate through the nozzle."""
        gamma = chamber_state['gamma']
        R = chamber_state['gas_constant']
        p0 = chamber_state['pressure']
        T0 = chamber_state['temperature']
        pr_crit = (2/(gamma + 1))**(gamma/(gamma - 1))
        Tr_crit = 2/(gamma + 1)
        rho_crit = p0 * pr_crit / (R * T0 * Tr_crit)
        v_crit = np.sqrt(gamma * R * T0 * Tr_crit)
        return rho_crit * v_crit * throat_area

    def calculate_thrust(self, exit_area: float, chamber_state: Dict[str, float], ambient_pressure: float) -> float:
        """Calculate thrust from nozzle exit conditions."""
        exit_props = self.calculate_flow_properties_from_area_ratio(
            exit_area/chamber_state['throat_area'], chamber_state)
        m_dot = self.calculate_mass_flow(chamber_state['throat_area'], chamber_state)
        v_exit = exit_props['velocity']
        momentum_thrust = m_dot * v_exit
        pressure_thrust = (exit_props['pressure'] - ambient_pressure) * exit_area
        return momentum_thrust + pressure_thrust 