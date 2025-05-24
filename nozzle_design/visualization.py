import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from typing import List, Tuple, Dict, Optional
from .engineering_calculations import NozzleSegment, NozzleGeometryCalculator
from .combustion import CombustionState

class NozzleVisualizer:
    """Handles visualization of nozzle analysis results"""
    
    def __init__(self):
        self.calculator = NozzleGeometryCalculator()
        
    def create_contour_plot(self,
                          segments: List[NozzleSegment],
                          property_name: str,
                          title: str,
                          colorbar_label: str) -> Figure:
        """Create a contour plot of a property along the nozzle"""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Extract data
        x = [s.start_x for s in segments]
        y = [s.start_radius for s in segments]
        values = [getattr(s, property_name) for s in segments]
        
        # Create contour plot
        contour = ax.tricontourf(x, y, values, levels=20, cmap='jet')
        
        # Add colorbar
        cbar = fig.colorbar(contour, ax=ax)
        cbar.set_label(colorbar_label)
        
        # Add nozzle wall
        wall_x = x + [segments[-1].end_x]
        wall_y = y + [segments[-1].end_radius]
        ax.plot(wall_x, wall_y, 'k-', linewidth=2, label='Nozzle Wall')
        
        # Add centerline
        ax.plot(wall_x, [0]*len(wall_x), 'k--', alpha=0.5)
        
        # Customize plot
        ax.set_xlabel('Axial Position (m)')
        ax.set_ylabel('Radius (m)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.axis('equal')
        
        return fig
    
    def create_performance_plot(self,
                              segments: List[NozzleSegment],
                              chamber_state: CombustionState) -> Figure:
        """Create a plot of performance parameters along the nozzle"""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Extract data
        x = [s.start_x for s in segments]
        mach = [s.mach_number for s in segments]
        pressure = [s.pressure/1e6 for s in segments]  # Convert to MPa
        temperature = [s.temperature for s in segments]
        
        # Create plot
        ax.plot(x, mach, 'b-', label='Mach Number')
        ax.plot(x, pressure, 'r-', label='Pressure (MPa)')
        ax.plot(x, temperature, 'g-', label='Temperature (K)')
        
        # Add throat location
        throat_x = segments[0].end_x
        ax.axvline(x=throat_x, color='k', linestyle='--', alpha=0.5, label='Throat')
        
        # Customize plot
        ax.set_xlabel('Axial Position (m)')
        ax.set_ylabel('Value')
        ax.set_title('Nozzle Performance Parameters')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        return fig
    
    def create_heat_transfer_plot(self,
                                segments: List[NozzleSegment]) -> Figure:
        """Create a plot of heat transfer parameters"""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Extract data
        x = [s.start_x for s in segments]
        wall_temp = [s.wall_temperature for s in segments]
        heat_flux = [s.heat_flux/1e6 for s in segments]  # Convert to MW/m²
        
        # Create plot
        ax.plot(x, wall_temp, 'r-', label='Wall Temperature (K)')
        ax2 = ax.twinx()
        ax2.plot(x, heat_flux, 'b-', label='Heat Flux (MW/m²)')
        
        # Add throat location
        throat_x = segments[0].end_x
        ax.axvline(x=throat_x, color='k', linestyle='--', alpha=0.5, label='Throat')
        
        # Customize plot
        ax.set_xlabel('Axial Position (m)')
        ax.set_ylabel('Temperature (K)')
        ax2.set_ylabel('Heat Flux (MW/m²)')
        ax.set_title('Heat Transfer Analysis')
        ax.grid(True, alpha=0.3)
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        return fig
    
    def create_altitude_optimization_plot(self,
                                        chamber_state: CombustionState,
                                        material: str) -> Figure:
        """Create a plot of expansion ratio vs. altitude for vacuum optimization"""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Generate altitude range
        altitudes = np.linspace(0, 100000, 100)  # 0 to 100 km
        
        # Calculate atmospheric pressure at each altitude
        pressures = [self._calculate_atmospheric_pressure(h) for h in altitudes]
        
        # Calculate optimal expansion ratio for each pressure
        expansion_ratios = []
        for p in pressures:
            # Find expansion ratio that gives exit pressure = ambient pressure
            def pressure_error(area_ratio):
                mach = self.calculator.calculate_mach_from_area(
                    area_ratio, chamber_state.gas_properties.gamma)
                exit_pressure = chamber_state.pressure * (
                    1 + (chamber_state.gas_properties.gamma-1)/2 * mach**2)**(
                    -chamber_state.gas_properties.gamma/(chamber_state.gas_properties.gamma-1))
                return abs(exit_pressure - p)
            
            # Optimize expansion ratio
            result = minimize(pressure_error, x0=10.0, bounds=[(1.0, 100.0)])
            expansion_ratios.append(result.x[0])
        
        # Create plot
        ax.plot(altitudes/1000, expansion_ratios, 'b-')
        
        # Customize plot
        ax.set_xlabel('Altitude (km)')
        ax.set_ylabel('Optimal Expansion Ratio')
        ax.set_title('Vacuum Optimization')
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def _calculate_atmospheric_pressure(self, altitude: float) -> float:
        """Calculate atmospheric pressure at given altitude"""
        # Simple exponential model
        p0 = 101325  # Sea level pressure (Pa)
        h0 = 7400    # Scale height (m)
        return p0 * np.exp(-altitude/h0)
    
    def export_results(self,
                      segments: List[NozzleSegment],
                      filename: str,
                      format: str = 'csv') -> None:
        """Export nozzle analysis results to file"""
        if format == 'csv':
            self._export_csv(segments, filename)
        elif format == 'png':
            self._export_plots(segments, filename)
    
    def _export_csv(self, segments: List[NozzleSegment], filename: str) -> None:
        """Export results to CSV file"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Position (m)', 'Radius (m)', 'Mach Number',
                'Pressure (Pa)', 'Temperature (K)',
                'Wall Temperature (K)', 'Heat Flux (W/m²)'
            ])
            
            # Write data
            for segment in segments:
                writer.writerow([
                    segment.start_x,
                    segment.start_radius,
                    segment.mach_number,
                    segment.pressure,
                    segment.temperature,
                    segment.wall_temperature,
                    segment.heat_flux
                ])
    
    def _export_plots(self, segments: List[NozzleSegment], filename: str) -> None:
        """Export plots to PNG file"""
        # Create all plots
        contour_fig = self.create_contour_plot(
            segments, 'mach_number', 'Mach Number Distribution', 'Mach Number')
        perf_fig = self.create_performance_plot(segments, None)
        heat_fig = self.create_heat_transfer_plot(segments)
        
        # Save plots
        contour_fig.savefig(f'{filename}_contour.png')
        perf_fig.savefig(f'{filename}_performance.png')
        heat_fig.savefig(f'{filename}_heat.png') 