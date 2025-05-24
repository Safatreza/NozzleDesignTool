from vtk import (
    vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor,
    vtkPolyData, vtkPoints, vtkCellArray, vtkPolyDataMapper,
    vtkActor, vtkProperty, vtkAxesActor, vtkOrientationMarkerWidget,
    vtkConeSource, vtkTubeFilter, vtkPolyLine, vtkSphereSource
)
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
import numpy as np
from typing import List, Optional, Tuple

from .engineering_calculations import NozzleSegment

class Nozzle3DViewer(QWidget):
    """3D visualization of the nozzle using VTK"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the 3D viewer UI"""
        layout = QVBoxLayout(self)
        
        # Create VTK renderer
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(0.2, 0.3, 0.4)
        
        # Create render window
        self.render_window = vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        # Create render window interactor
        self.interactor = vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.render_window)
        
        # Add coordinate axes
        self.add_coordinate_axes()
        
        # Set up the interactor style
        self.interactor.Initialize()
        self.interactor.Start()
    
    def add_coordinate_axes(self):
        """Add coordinate axes to the scene"""
        axes = vtkAxesActor()
        axes.SetTotalLength(1.0, 1.0, 1.0)
        axes.SetShaftType(0)
        axes.SetAxisLabels(1)
        axes.SetCylinderRadius(0.02)
        
        # Add orientation marker
        marker = vtkOrientationMarkerWidget()
        marker.SetOrientationMarker(axes)
        marker.SetInteractor(self.interactor)
        marker.SetViewport(0.0, 0.0, 0.2, 0.2)
        marker.SetEnabled(1)
        marker.InteractiveOn()
    
    def update_nozzle(self, segments: List[NozzleSegment]):
        """Update the nozzle visualization with new segments"""
        # Clear existing actors
        self.renderer.RemoveAllViewProps()
        self.add_coordinate_axes()
        
        # Create points for the nozzle contour
        points = vtkPoints()
        for segment in segments:
            points.InsertNextPoint(segment.start_x, segment.start_radius, 0)
        points.InsertNextPoint(segments[-1].end_x, segments[-1].end_radius, 0)
        
        # Create lines for the nozzle contour
        lines = vtkCellArray()
        for i in range(points.GetNumberOfPoints() - 1):
            line = vtkPolyLine()
            line.GetPointIds().SetNumberOfIds(2)
            line.GetPointIds().SetId(0, i)
            line.GetPointIds().SetId(1, i + 1)
            lines.InsertNextCell(line)
        
        # Create polydata
        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)
        
        # Create tube filter for better visualization
        tube = vtkTubeFilter()
        tube.SetInputData(polydata)
        tube.SetRadius(0.01)
        tube.SetNumberOfSides(32)
        
        # Create mapper and actor
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(tube.GetOutputPort())
        
        actor = vtkActor()
        actor.SetMapper(mapper)
        
        # Set properties
        prop = actor.GetProperty()
        prop.SetColor(0.8, 0.8, 0.8)  # Light gray
        prop.SetOpacity(0.8)
        prop.SetAmbient(0.2)
        prop.SetDiffuse(0.8)
        prop.SetSpecular(0.2)
        
        # Add actor to renderer
        self.renderer.AddActor(actor)
        
        # Add points for Mach number visualization
        self.add_mach_points(segments)
        
        # Reset camera and render
        self.renderer.ResetCamera()
        self.render_window.Render()
    
    def add_mach_points(self, segments: List[NozzleSegment]):
        """Add points colored by Mach number"""
        for segment in segments:
            # Create sphere for each point
            sphere = vtkSphereSource()
            sphere.SetCenter(segment.start_x, segment.start_radius, 0)
            sphere.SetRadius(0.005)
            sphere.SetPhiResolution(16)
            sphere.SetThetaResolution(16)
            
            # Create mapper
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            
            # Create actor
            actor = vtkActor()
            actor.SetMapper(mapper)
            
            # Set color based on Mach number
            prop = actor.GetProperty()
            mach = segment.mach_number
            if mach < 1.0:
                # Subsonic: blue to green
                r = 0.0
                g = mach
                b = 1.0 - mach
            else:
                # Supersonic: green to red
                r = min((mach - 1.0) / 2.0, 1.0)
                g = max(1.0 - (mach - 1.0) / 2.0, 0.0)
                b = 0.0
            
            prop.SetColor(r, g, b)
            prop.SetOpacity(0.8)
            
            # Add actor to renderer
            self.renderer.AddActor(actor)
    
    def add_heat_flux_visualization(self, segments: List[NozzleSegment]):
        """Add heat flux visualization"""
        for segment in segments:
            if segment.heat_flux > 0:
                # Create cone to represent heat flux
                cone = vtkConeSource()
                cone.SetCenter(segment.start_x, segment.start_radius, 0)
                cone.SetDirection(0, 1, 0)  # Point outward
                cone.SetHeight(0.02)
                cone.SetRadius(0.005)
                
                # Create mapper
                mapper = vtkPolyDataMapper()
                mapper.SetInputConnection(cone.GetOutputPort())
                
                # Create actor
                actor = vtkActor()
                actor.SetMapper(mapper)
                
                # Set color based on heat flux
                prop = actor.GetProperty()
                heat_ratio = min(segment.heat_flux / 1e6, 1.0)  # Normalize to MW/m²
                prop.SetColor(1.0, 1.0 - heat_ratio, 0.0)  # Yellow to red
                prop.SetOpacity(0.6)
                
                # Add actor to renderer
                self.renderer.AddActor(actor)
    
    def reset_view(self):
        """Reset the camera view"""
        self.renderer.ResetCamera()
        self.render_window.Render()
    
    def set_view_top(self):
        """Set view to top"""
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0, 0, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 1, 0)
        self.render_window.Render()
    
    def set_view_side(self):
        """Set view to side"""
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(1, 0, 0)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.render_window.Render()
    
    def set_view_iso(self):
        """Set view to isometric"""
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(1, 1, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.render_window.Render() 