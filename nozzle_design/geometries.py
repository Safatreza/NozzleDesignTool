"""Module for nozzle geometry classes."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from .nozzle_geometry import NozzleSegment

@dataclass
class NozzleGeometry:
    """Base class for nozzle geometries."""
    throat_radius: float
    exit_radius: float
    length: float
    expansion_ratio: float
    wall_angle: float

    def get_segments(self, n: int = 50):
        """Return a list of NozzleSegment objects for this geometry."""
        x = np.linspace(0, self.length, n)
        segments = []
        for i in range(len(x) - 1):
            segments.append(NozzleSegment(
                start_x=x[i],
                start_radius=self.get_radius(x[i]),
                end_x=x[i+1],
                end_radius=self.get_radius(x[i+1]),
                type='generic'))
        return segments

class ConicalNozzle(NozzleGeometry):
    """Conical nozzle geometry."""
    
    def __init__(self,
                 throat_radius: float,
                 exit_radius: float,
                 length: float,
                 wall_angle: float = 15.0):
        """Initialize conical nozzle.
        
        Args:
            throat_radius: Throat radius in meters
            exit_radius: Exit radius in meters
            length: Nozzle length in meters
            wall_angle: Wall angle in degrees
        """
        expansion_ratio = (exit_radius / throat_radius) ** 2
        super().__init__(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            expansion_ratio=expansion_ratio,
            wall_angle=wall_angle
        )
    
    def get_radius(self, x: float) -> float:
        """Get radius at axial position.
        
        Args:
            x: Axial position in meters
            
        Returns:
            Radius in meters
        """
        return self.throat_radius + x * np.tan(np.radians(self.wall_angle))

class BellNozzle(NozzleGeometry):
    """Bell nozzle geometry using Rao's method."""
    
    def __init__(self,
                 throat_radius: float,
                 exit_radius: float,
                 length: float,
                 wall_angle: float = 15.0,
                 n_points: int = 100):
        """Initialize bell nozzle.
        
        Args:
            throat_radius: Throat radius in meters
            exit_radius: Exit radius in meters
            length: Nozzle length in meters
            wall_angle: Initial wall angle in degrees
            n_points: Number of points for contour
        """
        expansion_ratio = (exit_radius / throat_radius) ** 2
        super().__init__(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            expansion_ratio=expansion_ratio,
            wall_angle=wall_angle
        )
        self.n_points = n_points
        self._generate_contour()
    
    def _generate_contour(self) -> None:
        """Generate nozzle contour using Rao's method."""
        # Generate points along nozzle
        x = np.linspace(0, self.length, self.n_points)
        
        # Calculate radius using Rao's method
        theta_n = np.radians(self.wall_angle)
        theta_e = np.radians(15.0)  # Exit angle
        
        # Throat region
        throat_length = 0.382 * self.throat_radius
        throat_angle = np.radians(30.0)
        
        # Expansion region
        expansion_length = self.length - throat_length
        
        # Generate contour
        r = np.zeros_like(x)
        for i, xi in enumerate(x):
            if xi < throat_length:
                # Throat region (circular arc)
                r[i] = self.throat_radius * (1 + np.cos(throat_angle * xi / throat_length))
            else:
                # Expansion region (Rao's method)
                t = (xi - throat_length) / expansion_length
                theta = theta_n + (theta_e - theta_n) * t
                r[i] = self.throat_radius + (self.exit_radius - self.throat_radius) * t
        
        self.contour = np.column_stack((x, r))
    
    def get_radius(self, x: float) -> float:
        """Get radius at axial position.
        
        Args:
            x: Axial position in meters
            
        Returns:
            Radius in meters
        """
        return np.interp(x, self.contour[:, 0], self.contour[:, 1])

class DualBellNozzle(NozzleGeometry):
    """Dual-bell nozzle geometry."""
    
    def __init__(self,
                 throat_radius: float,
                 exit_radius: float,
                 length: float,
                 wall_angle: float = 15.0,
                 inflection_point: float = 0.5):
        """Initialize dual-bell nozzle.
        
        Args:
            throat_radius: Throat radius in meters
            exit_radius: Exit radius in meters
            length: Nozzle length in meters
            wall_angle: Initial wall angle in degrees
            inflection_point: Location of inflection point (0-1)
        """
        expansion_ratio = (exit_radius / throat_radius) ** 2
        super().__init__(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            expansion_ratio=expansion_ratio,
            wall_angle=wall_angle
        )
        self.inflection_point = inflection_point
    
    def get_radius(self, x: float) -> float:
        """Get radius at axial position.
        
        Args:
            x: Axial position in meters
            
        Returns:
            Radius in meters
        """
        if x < self.length * self.inflection_point:
            # First bell
            return self.throat_radius + x * np.tan(np.radians(self.wall_angle))
        else:
            # Second bell
            x1 = self.length * self.inflection_point
            r1 = self.get_radius(x1)
            return r1 + (x - x1) * np.tan(np.radians(self.wall_angle * 1.5))

class AerospikeNozzle(NozzleGeometry):
    """Aerospike nozzle geometry."""
    
    def __init__(self,
                 throat_radius: float,
                 exit_radius: float,
                 length: float,
                 wall_angle: float = 15.0,
                 spike_angle: float = 20.0):
        """Initialize aerospike nozzle.
        
        Args:
            throat_radius: Throat radius in meters
            exit_radius: Exit radius in meters
            length: Nozzle length in meters
            wall_angle: Initial wall angle in degrees
            spike_angle: Spike angle in degrees
        """
        expansion_ratio = (exit_radius / throat_radius) ** 2
        super().__init__(
            throat_radius=throat_radius,
            exit_radius=exit_radius,
            length=length,
            expansion_ratio=expansion_ratio,
            wall_angle=wall_angle
        )
        self.spike_angle = spike_angle
    
    def get_radius(self, x: float) -> float:
        """Get radius at axial position.
        
        Args:
            x: Axial position in meters
            
        Returns:
            Radius in meters
        """
        # Calculate spike profile
        spike_radius = self.throat_radius + x * np.tan(np.radians(self.spike_angle))
        
        # Calculate outer contour
        outer_radius = self.throat_radius + x * np.tan(np.radians(self.wall_angle))
        
        # Return the difference for the annular flow area
        return outer_radius - spike_radius 