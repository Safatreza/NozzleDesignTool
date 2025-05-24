from typing import Dict, List, Tuple
import numpy as np
from .models import NozzleProfile
from .thermodynamics import GasMixture, IsentropicFlow, RealGasEffects
from .flow_regimes import ConvergingNozzle, ConvergingDivergingNozzle, FlowState
from .geometries import ConicalNozzle, BellNozzle, DualBellNozzle, AerospikeNozzle
from .combustion import CombustionState

class NozzleDesigner:
    """Handles the nozzle design calculations"""
    
    def __init__(self):
        self.real_gas = RealGasEffects()
        self.geometries = {
            'conical': ConicalNozzle(),
            'bell': BellNozzle(),
            'dual-bell': DualBellNozzle(),
            'aerospike': AerospikeNozzle()
        }

    def calculate_profile(self, 
                         mach: float, 
                         altitude: float, 
                         expansion_ratio: float,
                         gas_properties: Dict[str, float],
                         nozzle_type: str = 'bell',
                         chamber_state: CombustionState = None,
                         back_pressure: float = None) -> NozzleProfile:
        """Calculate the complete nozzle profile"""
        # Use chamber state if provided, otherwise use default values
        if chamber_state:
            initial_temp = chamber_state.temperature
            initial_pressure = chamber_state.pressure
        else:
            initial_temp = 3000  # K
            initial_pressure = 1e6  # Pa
        
        # Calculate back pressure
        if back_pressure is None:
            back_pressure = self._calculate_atmospheric_pressure(altitude)
        
        # Select nozzle geometry
        geometry = self.geometries.get(nozzle_type.lower(), BellNozzle())
        
        # Calculate nozzle length based on expansion ratio and chamber state
        if chamber_state:
            # Use mass flow rate to estimate throat area
            throat_area = chamber_state.mass_flow / (
                initial_pressure * np.sqrt(chamber_state.gas_properties.gamma / 
                (chamber_state.gas_properties.molecular_weight * 8.314 * initial_temp)))
            throat_radius = np.sqrt(throat_area / np.pi)
        else:
            throat_radius = 0.1  # m
        
        # Calculate nozzle length (simplified)
        length = expansion_ratio * throat_radius * 2
        
        # Calculate nozzle contour
        contour = geometry.calculate_contour(throat_radius, expansion_ratio, length)
        
        # Create gas mixture from properties
        gas_mixture = GasMixture(gas_properties)
        
        # Calculate flow properties
        if nozzle_type.lower() == 'conical':
            flow = ConvergingNozzle(gas_mixture)
            states = flow.calculate_flow(initial_pressure, back_pressure, initial_temp)
        else:
            flow = ConvergingDivergingNozzle(gas_mixture)
            states = flow.calculate_flow(
                initial_pressure, back_pressure, initial_temp, expansion_ratio)
        
        # Extract flow properties
        pressure_gradient = [state.pressure for state in states]
        temperature_gradient = [state.temperature for state in states]
        
        # Get gas properties at exit conditions
        exit_state = states[-1]
        gas_properties = gas_mixture.get_mixture_properties(exit_state.temperature)
        
        # Create profile with flow regime information
        profile = NozzleProfile(
            shape=nozzle_type,
            length=length,
            pressure_gradient=pressure_gradient,
            temperature_gradient=temperature_gradient,
            gas_properties=gas_properties,
            geometry=contour
        )
        
        # Add flow regime information
        profile.flow_regime = exit_state.flow_regime
        
        return profile

    def _calculate_atmospheric_pressure(self, altitude: float) -> float:
        """Calculate atmospheric pressure at given altitude"""
        # Simple exponential atmosphere model
        p0 = 101325  # Pa (sea level pressure)
        h0 = 7400    # m (scale height)
        return p0 * np.exp(-altitude/h0) 