import matplotlib.pyplot as plt
import numpy as np
from .models import NozzleProfile

class NozzleVisualizer:
    """Handles visualization of nozzle profiles and flow properties"""
    
    @staticmethod
    def plot_profile(profile: NozzleProfile) -> None:
        """Plot the nozzle profile and flow properties"""
        # Extract geometry
        x_coords, y_coords = zip(*profile.geometry)
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
        
        # Plot nozzle geometry
        ax1.plot(x_coords, y_coords, label='Nozzle Wall', color='blue')
        ax1.plot(x_coords, [-y for y in y_coords], color='blue')
        ax1.fill_between(x_coords, y_coords, [-y for y in y_coords], color='skyblue', alpha=0.3)
        ax1.set_title(f"{profile.shape} Nozzle Profile")
        ax1.set_xlabel("Nozzle Length (m)")
        ax1.set_ylabel("Width (m)")
        ax1.grid(True)
        ax1.legend()
        
        # Plot pressure and temperature gradients
        x = np.linspace(0, profile.length, len(profile.pressure_gradient))
        ax2.plot(x, profile.pressure_gradient, '--', color='red', label='Pressure')
        ax2_twin = ax2.twinx()
        ax2_twin.plot(x, profile.temperature_gradient, '--', color='orange', label='Temperature')
        
        ax2.set_xlabel("Nozzle Length (m)")
        ax2.set_ylabel("Pressure (Pa)", color='red')
        ax2_twin.set_ylabel("Temperature (K)", color='orange')
        
        # Add legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        plt.tight_layout()
        plt.show() 