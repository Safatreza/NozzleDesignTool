"""Module for Cantera visualization of nozzle flow."""

from typing import List, Dict, Optional, Tuple
import numpy as np
import cantera as ct
import matplotlib.pyplot as plt
from pathlib import Path

from .nozzle_geometry import NozzleSegment

class CanteraVisualizer:
    """Visualizer for nozzle flow using Cantera."""
    
    def __init__(self, segments: List[NozzleSegment], gas: Optional[ct.Solution] = None):
        """Initialize the visualizer with nozzle segments.
        
        Args:
            segments: List of nozzle segments
            gas: Cantera gas object (optional)
        """
        self.segments = segments
        self.gas = gas or ct.Solution('gri30.yaml')
        self.flow_data = None
    
    def setup_flow(self,
                  chamber_state: Dict[str, float],
                  propellant: str = 'H2:1, O2:0.5') -> None:
        """Set up flow conditions.
        
        Args:
            chamber_state: Dictionary containing chamber conditions
            propellant: Propellant composition in Cantera format
        """
        # Set gas composition
        self.gas.TPX = (
            chamber_state['temperature'],
            chamber_state['pressure'],
            propellant
        )
        
        # Calculate flow properties
        self.flow_data = self._calculate_flow_properties(chamber_state)
    
    def _calculate_flow_properties(self,
                                 chamber_state: Dict[str, float]) -> Dict[str, np.ndarray]:
        """Calculate flow properties along nozzle.
        
        Args:
            chamber_state: Dictionary containing chamber conditions
            
        Returns:
            Dictionary of flow properties
        """
        # Initialize arrays
        n_points = len(self.segments)
        x = np.zeros(n_points)
        area = np.zeros(n_points)
        mach = np.zeros(n_points)
        pressure = np.zeros(n_points)
        temperature = np.zeros(n_points)
        density = np.zeros(n_points)
        velocity = np.zeros(n_points)
        
        # Calculate properties at each point
        for i, segment in enumerate(self.segments):
            x[i] = segment.start_x
            area[i] = np.pi * segment.start_radius**2
            
            # Calculate flow properties using Cantera
            self.gas.equilibrate('HP')
            mach[i] = segment.mach_number
            pressure[i] = segment.pressure
            temperature[i] = segment.temperature
            density[i] = self.gas.density
            velocity[i] = mach[i] * np.sqrt(self.gas.cp / self.gas.cv * ct.gas_constant * temperature[i])
        
        return {
            'x': x,
            'area': area,
            'mach': mach,
            'pressure': pressure,
            'temperature': temperature,
            'density': density,
            'velocity': velocity
        }
    
    def plot_flow_properties(self,
                           properties: List[str] = None,
                           save_path: Optional[str] = None) -> None:
        """Plot flow properties along nozzle.
        
        Args:
            properties: List of properties to plot
            save_path: Path to save plot (optional)
        """
        if self.flow_data is None:
            raise ValueError("Flow not set up. Call setup_flow first.")
        
        if properties is None:
            properties = ['mach', 'pressure', 'temperature', 'density']
        
        # Create subplots
        n_plots = len(properties)
        fig, axes = plt.subplots(n_plots, 1, figsize=(10, 4*n_plots))
        if n_plots == 1:
            axes = [axes]
        
        # Plot each property
        for ax, prop in zip(axes, properties):
            ax.plot(self.flow_data['x'], self.flow_data[prop])
            ax.set_xlabel('Axial Position (m)')
            ax.set_ylabel(prop.capitalize())
            ax.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    
    def plot_contour(self,
                    property_name: str,
                    n_levels: int = 20,
                    save_path: Optional[str] = None) -> None:
        """Plot property contour in nozzle.
        
        Args:
            property_name: Name of property to plot
            n_levels: Number of contour levels
            save_path: Path to save plot (optional)
        """
        if self.flow_data is None:
            raise ValueError("Flow not set up. Call setup_flow first.")
        
        # Create mesh for contour plot
        x = self.flow_data['x']
        r = np.array([segment.start_radius for segment in self.segments])
        X, R = np.meshgrid(x, r)
        
        # Interpolate property values
        Z = np.interp(X.flatten(), x, self.flow_data[property_name]).reshape(X.shape)
        
        # Create contour plot
        plt.figure(figsize=(10, 6))
        contour = plt.contourf(X, R, Z, n_levels, cmap='jet')
        plt.colorbar(contour, label=property_name.capitalize())
        plt.xlabel('Axial Position (m)')
        plt.ylabel('Radius (m)')
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    
    def export_flow_data(self, filename: str) -> None:
        """Export flow data to file.
        
        Args:
            filename: Output filename
        """
        if self.flow_data is None:
            raise ValueError("Flow not set up. Call setup_flow first.")
        
        # Save data to numpy file
        np.savez(filename, **self.flow_data)
    
    def calculate_performance_metrics(self) -> Dict[str, float]:
        """Calculate nozzle performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        if self.flow_data is None:
            raise ValueError("Flow not set up. Call setup_flow first.")
        
        # Get exit conditions
        exit_idx = -1
        exit_mach = self.flow_data['mach'][exit_idx]
        exit_pressure = self.flow_data['pressure'][exit_idx]
        exit_temperature = self.flow_data['temperature'][exit_idx]
        exit_velocity = self.flow_data['velocity'][exit_idx]
        
        # Calculate thrust coefficient
        thrust_coeff = self._calculate_thrust_coefficient(
            exit_mach=exit_mach,
            exit_pressure=exit_pressure,
            chamber_pressure=self.gas.P,
            ambient_pressure=101325.0  # 1 atm
        )
        
        # Calculate specific impulse
        isp = exit_velocity / 9.81
        
        return {
            'thrust_coefficient': thrust_coeff,
            'specific_impulse': isp,
            'exit_mach': exit_mach,
            'exit_pressure': exit_pressure,
            'exit_temperature': exit_temperature,
            'exit_velocity': exit_velocity
        }
    
    def _calculate_thrust_coefficient(self,
                                    exit_mach: float,
                                    exit_pressure: float,
                                    chamber_pressure: float,
                                    ambient_pressure: float) -> float:
        """Calculate thrust coefficient.
        
        Args:
            exit_mach: Exit Mach number
            exit_pressure: Exit pressure
            chamber_pressure: Chamber pressure
            ambient_pressure: Ambient pressure
            
        Returns:
            Thrust coefficient
        """
        gamma = self.gas.cp / self.gas.cv
        
        # Momentum term
        momentum_term = exit_mach * np.sqrt(
            (2 / (gamma - 1)) * (1 + (gamma - 1) / 2 * exit_mach**2)
        )
        
        # Pressure term
        pressure_term = (exit_pressure - ambient_pressure) / chamber_pressure
        
        return momentum_term + pressure_term 