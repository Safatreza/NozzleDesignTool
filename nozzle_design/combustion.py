from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np
from .thermodynamics import GasMixture, GasProperties

@dataclass
class CombustionState:
    """Represents the state of combustion chamber"""
    pressure: float  # Pa
    temperature: float  # K
    fuel_oxidizer_ratio: float  # mass ratio
    thrust: float  # N
    mass_flow: float  # kg/s
    characteristic_velocity: float  # m/s
    gas_properties: GasProperties

class CombustionChamber:
    """Handles combustion chamber calculations"""
    
    def __init__(self):
        # Common propellant combinations
        self.propellant_data = {
            'LOX/LH2': {
                'fuel': 'H2',
                'oxidizer': 'O2',
                'optimal_ratio': 0.25,  # mass ratio
                'c_star': 2300,  # m/s
                'gamma': 1.2
            },
            'LOX/RP1': {
                'fuel': 'C12H23',
                'oxidizer': 'O2',
                'optimal_ratio': 2.56,
                'c_star': 1800,
                'gamma': 1.2
            },
            'N2O4/MMH': {
                'fuel': 'CH3NHNH2',
                'oxidizer': 'N2O4',
                'optimal_ratio': 0.85,
                'c_star': 1700,
                'gamma': 1.2
            }
        }

    def calculate_chamber_state(self,
                              pressure: float,
                              temperature: float,
                              fuel_oxidizer_ratio: float,
                              thrust: float,
                              propellant_type: str = 'LOX/LH2') -> CombustionState:
        """Calculate combustion chamber state"""
        # Get propellant data
        prop_data = self.propellant_data.get(propellant_type)
        if not prop_data:
            raise ValueError(f"Unknown propellant type: {propellant_type}")

        # Calculate mass flow rate
        # Using simplified rocket equation: F = m_dot * c_star * Cf
        # Cf (thrust coefficient) is approximated as 1.5 for initial calculation
        Cf = 1.5
        mass_flow = thrust / (prop_data['c_star'] * Cf)

        # Calculate mixture composition
        components = self._calculate_mixture_composition(
            fuel_oxidizer_ratio,
            prop_data['fuel'],
            prop_data['oxidizer']
        )

        # Create gas mixture
        gas_mixture = GasMixture(components)
        gas_properties = gas_mixture.get_mixture_properties(temperature)

        return CombustionState(
            pressure=pressure,
            temperature=temperature,
            fuel_oxidizer_ratio=fuel_oxidizer_ratio,
            thrust=thrust,
            mass_flow=mass_flow,
            characteristic_velocity=prop_data['c_star'],
            gas_properties=gas_properties
        )

    def _calculate_mixture_composition(self,
                                     ratio: float,
                                     fuel: str,
                                     oxidizer: str) -> Dict[str, float]:
        """Calculate mole fractions from mass ratio"""
        # Simplified calculation assuming ideal gas behavior
        # In reality, this should use actual combustion chemistry
        total_mass = 1.0 + ratio
        fuel_mass = ratio / total_mass
        oxidizer_mass = 1.0 / total_mass

        # Convert mass fractions to mole fractions
        # Using approximate molecular weights
        mw_fuel = 2.0 if fuel == 'H2' else 170.0  # kg/kmol
        mw_oxidizer = 32.0 if oxidizer == 'O2' else 92.0  # kg/kmol

        fuel_moles = fuel_mass / mw_fuel
        oxidizer_moles = oxidizer_mass / mw_oxidizer
        total_moles = fuel_moles + oxidizer_moles

        return {
            fuel: fuel_moles / total_moles,
            oxidizer: oxidizer_moles / total_moles
        }

    def calculate_optimal_ratio(self, propellant_type: str) -> float:
        """Get optimal fuel-oxidizer ratio for given propellant combination"""
        prop_data = self.propellant_data.get(propellant_type)
        if not prop_data:
            raise ValueError(f"Unknown propellant type: {propellant_type}")
        return prop_data['optimal_ratio']

    def get_available_propellants(self) -> Dict[str, Dict]:
        """Get available propellant combinations"""
        return self.propellant_data 