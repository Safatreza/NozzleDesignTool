from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QLabel, QFileDialog, QMessageBox, QGroupBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QSlider, QProgressBar, QMenu,
    QAction, QToolBar, QStatusBar, QDialog, QListWidget,
    QDialogButtonBox, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import sys
import os
from typing import Dict, Optional, List
import json
import pandas as pd
from datetime import datetime

from .engineering_calculations import NozzleGeometryCalculator, MaterialProperties
from .combustion import CombustionChamber
from .visualization import NozzleVisualizer
from .session_manager import SessionManager, DesignSession, UnitConverter
from .visualization_3d import Nozzle3DViewer

class SessionDialog(QDialog):
    """Dialog for managing design sessions"""
    
    def __init__(self, session_manager: SessionManager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.selected_session_id = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Design Sessions")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Session list
        self.session_list = QListWidget()
        self.update_session_list()
        layout.addWidget(self.session_list)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Open | QDialogButtonBox.Delete | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Connect delete button
        delete_button = button_box.button(QDialogButtonBox.Delete)
        delete_button.clicked.connect(self.delete_session)
        
        layout.addWidget(button_box)
    
    def update_session_list(self):
        """Update the list of sessions"""
        self.session_list.clear()
        sessions = self.session_manager.list_sessions()
        for session in sessions:
            item = f"{session['name']} ({session['modified_at'].strftime('%Y-%m-%d %H:%M')})"
            self.session_list.addItem(item)
    
    def delete_session(self):
        """Delete the selected session"""
        current = self.session_list.currentRow()
        if current >= 0:
            sessions = self.session_manager.list_sessions()
            session_id = sessions[current]['id']
            
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this session?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.session_manager.delete_session(session_id)
                self.update_session_list()
    
    def get_selected_session(self) -> Optional[DesignSession]:
        """Get the selected session"""
        current = self.session_list.currentRow()
        if current >= 0:
            sessions = self.session_manager.list_sessions()
            session_id = sessions[current]['id']
            return self.session_manager.load_session(session_id)
        return None

class NozzleDesignGUI(QMainWindow):
    """Main GUI window for nozzle design tool"""
    
    def __init__(self):
        super().__init__()
        self.calculator = NozzleGeometryCalculator()
        self.combustion = CombustionChamber()
        self.visualizer = NozzleVisualizer()
        self.session_manager = SessionManager()
        self.unit_converter = UnitConverter()
        self.current_session = None
        
        self.init_ui()
        self.create_menu()
        self.create_toolbar()
        self.create_status_bar()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('Nozzle Design Tool')
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create input panel
        input_panel = self.create_input_panel()
        main_layout.addWidget(input_panel, stretch=1)
        
        # Create output panel
        output_panel = self.create_output_panel()
        main_layout.addWidget(output_panel, stretch=2)
        
        # Initialize plots
        self.update_plots()
    
    def create_menu(self):
        """Create the main menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Design', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_design)
        file_menu.addAction(new_action)
        
        save_action = QAction('Save Design', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_design)
        file_menu.addAction(save_action)
        
        load_action = QAction('Load Design', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_design)
        file_menu.addAction(load_action)
        
        export_menu = file_menu.addMenu('Export')
        
        export_report = QAction('Export Full Report', self)
        export_report.triggered.connect(self.export_full_report)
        export_menu.addAction(export_report)
        
        export_csv = QAction('Export to CSV', self)
        export_csv.triggered.connect(lambda: self.export_results('csv'))
        export_menu.addAction(export_csv)
        
        export_excel = QAction('Export to Excel', self)
        export_excel.triggered.connect(lambda: self.export_results('excel'))
        export_menu.addAction(export_excel)
        
        export_png = QAction('Export to PNG', self)
        export_png.triggered.connect(lambda: self.export_results('png'))
        export_menu.addAction(export_png)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        show_3d_action = QAction('Show 3D View', self)
        show_3d_action.triggered.connect(self.show_3d_view)
        view_menu.addAction(show_3d_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        optimize_action = QAction('Optimize Design', self)
        optimize_action.triggered.connect(self.optimize_design)
        tools_menu.addAction(optimize_action)
        
        sensitivity_action = QAction('Sensitivity Analysis', self)
        sensitivity_action.triggered.connect(self.run_sensitivity_analysis)
        tools_menu.addAction(sensitivity_action)
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        calculate_action = QAction('Calculate', self)
        calculate_action.triggered.connect(self.calculate)
        toolbar.addAction(calculate_action)
        
        optimize_action = QAction('Optimize', self)
        optimize_action.triggered.connect(self.optimize_design)
        toolbar.addAction(optimize_action)
        
        export_action = QAction('Export', self)
        export_action.triggered.connect(self.export_results)
        toolbar.addAction(export_action)
    
    def create_status_bar(self):
        """Create the status bar"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Ready')
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.statusBar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()
    
    def create_input_panel(self) -> QWidget:
        """Create the input panel with all parameter inputs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Propellant selection
        propellant_group = QGroupBox("Propellant")
        propellant_layout = QFormLayout()
        self.propellant_combo = QComboBox()
        self.propellant_combo.addItems(self.combustion.get_available_propellants().keys())
        propellant_layout.addRow("Type:", self.propellant_combo)
        
        # Add custom propellant button
        custom_prop_button = QPushButton("Add Custom Propellant")
        custom_prop_button.clicked.connect(self.add_custom_propellant)
        propellant_layout.addRow(custom_prop_button)
        
        propellant_group.setLayout(propellant_layout)
        layout.addWidget(propellant_group)
        
        # Chamber conditions
        chamber_group = QGroupBox("Chamber Conditions")
        chamber_layout = QFormLayout()
        
        self.chamber_pressure = QDoubleSpinBox()
        self.chamber_pressure.setRange(0.1, 50.0)
        self.chamber_pressure.setValue(5.0)
        self.chamber_pressure.setSuffix(" MPa")
        self.chamber_pressure.setSingleStep(0.1)
        chamber_layout.addRow("Pressure:", self.chamber_pressure)
        
        self.chamber_temp = QDoubleSpinBox()
        self.chamber_temp.setRange(1000, 4000)
        self.chamber_temp.setValue(3000)
        self.chamber_temp.setSuffix(" K")
        self.chamber_temp.setSingleStep(100)
        chamber_layout.addRow("Temperature:", self.chamber_temp)
        
        self.fuel_ratio = QDoubleSpinBox()
        self.fuel_ratio.setRange(0.1, 10.0)
        self.fuel_ratio.setValue(2.5)
        self.fuel_ratio.setSingleStep(0.1)
        chamber_layout.addRow("Fuel-Oxidizer Ratio:", self.fuel_ratio)
        
        self.thrust = QDoubleSpinBox()
        self.thrust.setRange(100, 1000000)
        self.thrust.setValue(10000)
        self.thrust.setSuffix(" N")
        self.thrust.setSingleStep(1000)
        chamber_layout.addRow("Thrust:", self.thrust)
        
        # Add cooling parameters
        self.cooling_check = QCheckBox("Enable Cooling Analysis")
        self.cooling_check.setChecked(True)
        chamber_layout.addRow(self.cooling_check)
        
        self.coolant_temp = QDoubleSpinBox()
        self.coolant_temp.setRange(273, 373)
        self.coolant_temp.setValue(293)
        self.coolant_temp.setSuffix(" K")
        chamber_layout.addRow("Coolant Temperature:", self.coolant_temp)
        
        chamber_group.setLayout(chamber_layout)
        layout.addWidget(chamber_group)
        
        # Nozzle parameters
        nozzle_group = QGroupBox("Nozzle Parameters")
        nozzle_layout = QFormLayout()
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(self.calculator.DEFAULT_MATERIALS.keys())
        nozzle_layout.addRow("Material:", self.material_combo)
        
        self.optimization_combo = QComboBox()
        self.optimization_combo.addItems(["Thrust", "Mach Number", "Efficiency"])
        nozzle_layout.addRow("Optimization:", self.optimization_combo)
        
        self.target_value = QDoubleSpinBox()
        self.target_value.setRange(1.0, 10.0)
        self.target_value.setValue(3.0)
        self.target_value.setSuffix(" Mach")
        nozzle_layout.addRow("Target Value:", self.target_value)
        
        # Add advanced parameters
        self.advanced_check = QCheckBox("Show Advanced Parameters")
        self.advanced_check.toggled.connect(self.toggle_advanced_params)
        nozzle_layout.addRow(self.advanced_check)
        
        # Advanced parameters (initially hidden)
        self.advanced_group = QGroupBox("Advanced Parameters")
        advanced_layout = QFormLayout()
        
        self.wall_thickness = QDoubleSpinBox()
        self.wall_thickness.setRange(0.1, 10.0)
        self.wall_thickness.setValue(1.0)
        self.wall_thickness.setSuffix(" mm")
        advanced_layout.addRow("Wall Thickness:", self.wall_thickness)
        
        self.roughness = QDoubleSpinBox()
        self.roughness.setRange(0.1, 10.0)
        self.roughness.setValue(1.0)
        self.roughness.setSuffix(" µm")
        advanced_layout.addRow("Surface Roughness:", self.roughness)
        
        self.advanced_group.setLayout(advanced_layout)
        self.advanced_group.setVisible(False)
        nozzle_layout.addRow(self.advanced_group)
        
        nozzle_group.setLayout(nozzle_layout)
        layout.addWidget(nozzle_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.calculate)
        button_layout.addWidget(self.calculate_button)
        
        self.optimize_button = QPushButton("Optimize")
        self.optimize_button.clicked.connect(self.optimize_design)
        button_layout.addWidget(self.optimize_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_results)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return panel
    
    def create_output_panel(self) -> QWidget:
        """Create the output panel with plots and results"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget for different plots
        self.tab_widget = QTabWidget()
        
        # Contour plot tab
        contour_widget = QWidget()
        contour_layout = QVBoxLayout(contour_widget)
        self.contour_canvas = FigureCanvasQTAgg(Figure(figsize=(8, 6)))
        contour_layout.addWidget(self.contour_canvas)
        contour_layout.addWidget(NavigationToolbar2QT(self.contour_canvas, contour_widget))
        self.tab_widget.addTab(contour_widget, "Contour")
        
        # Performance plot tab
        perf_widget = QWidget()
        perf_layout = QVBoxLayout(perf_widget)
        self.performance_canvas = FigureCanvasQTAgg(Figure(figsize=(8, 6)))
        perf_layout.addWidget(self.performance_canvas)
        perf_layout.addWidget(NavigationToolbar2QT(self.performance_canvas, perf_widget))
        self.tab_widget.addTab(perf_widget, "Performance")
        
        # Heat transfer plot tab
        heat_widget = QWidget()
        heat_layout = QVBoxLayout(heat_widget)
        self.heat_canvas = FigureCanvasQTAgg(Figure(figsize=(8, 6)))
        heat_layout.addWidget(self.heat_canvas)
        heat_layout.addWidget(NavigationToolbar2QT(self.heat_canvas, heat_widget))
        self.tab_widget.addTab(heat_widget, "Heat Transfer")
        
        # Altitude optimization plot tab
        alt_widget = QWidget()
        alt_layout = QVBoxLayout(alt_widget)
        self.altitude_canvas = FigureCanvasQTAgg(Figure(figsize=(8, 6)))
        alt_layout.addWidget(self.altitude_canvas)
        alt_layout.addWidget(NavigationToolbar2QT(self.altitude_canvas, alt_widget))
        self.tab_widget.addTab(alt_widget, "Altitude Optimization")
        
        # 3D view tab
        self.viewer_3d = Nozzle3DViewer()
        self.tab_widget.addTab(self.viewer_3d, "3D View")
        
        # Add 3D view controls
        view_controls = QHBoxLayout()
        
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.clicked.connect(self.viewer_3d.reset_view)
        view_controls.addWidget(reset_view_btn)
        
        top_view_btn = QPushButton("Top View")
        top_view_btn.clicked.connect(self.viewer_3d.set_view_top)
        view_controls.addWidget(top_view_btn)
        
        side_view_btn = QPushButton("Side View")
        side_view_btn.clicked.connect(self.viewer_3d.set_view_side)
        view_controls.addWidget(side_view_btn)
        
        iso_view_btn = QPushButton("Isometric View")
        iso_view_btn.clicked.connect(self.viewer_3d.set_view_iso)
        view_controls.addWidget(iso_view_btn)
        
        # Add view controls to 3D tab
        self.viewer_3d.layout().addLayout(view_controls)
        
        layout.addWidget(self.tab_widget)
        
        # Results summary
        results_group = QGroupBox("Results Summary")
        results_layout = QFormLayout()
        
        self.thrust_label = QLabel("--")
        results_layout.addRow("Thrust:", self.thrust_label)
        
        self.isp_label = QLabel("--")
        results_layout.addRow("Specific Impulse:", self.isp_label)
        
        self.efficiency_label = QLabel("--")
        results_layout.addRow("Efficiency:", self.efficiency_label)
        
        self.exit_mach_label = QLabel("--")
        results_layout.addRow("Exit Mach:", self.exit_mach_label)
        
        # Add more results
        self.max_temp_label = QLabel("--")
        results_layout.addRow("Max Wall Temperature:", self.max_temp_label)
        
        self.max_heat_flux_label = QLabel("--")
        results_layout.addRow("Max Heat Flux:", self.max_heat_flux_label)
        
        self.safety_factor_label = QLabel("--")
        results_layout.addRow("Safety Factor:", self.safety_factor_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        return panel
    
    def toggle_advanced_params(self, checked: bool):
        """Toggle visibility of advanced parameters"""
        self.advanced_group.setVisible(checked)
    
    def add_custom_propellant(self):
        """Add a custom propellant to the list"""
        # TODO: Implement custom propellant dialog
        pass
    
    def show_3d_view(self):
        """Show 3D view of the nozzle"""
        if hasattr(self, 'current_results') and self.current_results:
            self.tab_widget.setCurrentWidget(self.viewer_3d)
            self.viewer_3d.update_nozzle(self.current_results['geometry'].segments)
            if self.cooling_check.isChecked():
                self.viewer_3d.add_heat_flux_visualization(self.current_results['geometry'].segments)
        else:
            QMessageBox.warning(self, "Warning", "No design data available for 3D visualization")
    
    def optimize_design(self):
        """Run optimization routine"""
        # TODO: Implement optimization
        pass
    
    def run_sensitivity_analysis(self):
        """Run sensitivity analysis"""
        # TODO: Implement sensitivity analysis
        pass
    
    def new_design(self):
        """Create a new design session"""
        if self.current_session is not None:
            reply = QMessageBox.question(
                self, "New Design",
                "Do you want to save the current design before creating a new one?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.save_design()
            elif reply == QMessageBox.Cancel:
                return
        
        self.current_session = DesignSession()
        self.clear_inputs()
        self.update_plots()
        self.statusBar.showMessage('New design created')
    
    def save_design(self):
        """Save the current design session"""
        if self.current_session is None:
            self.current_session = DesignSession()
        
        # Update session data from current inputs
        self.update_session_from_inputs()
        
        # Get session name if not set
        if not self.current_session.name:
            name, ok = QInputDialog.getText(
                self, "Save Design",
                "Enter a name for this design:"
            )
            if ok and name:
                self.current_session.name = name
            else:
                return
        
        try:
            session_id = self.session_manager.save_session(self.current_session)
            self.current_session.id = session_id
            self.statusBar.showMessage(f'Design saved as "{self.current_session.name}"')
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save design: {str(e)}")
    
    def load_design(self):
        """Load a saved design session"""
        dialog = SessionDialog(self.session_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            session = dialog.get_selected_session()
            if session:
                self.current_session = session
                self.update_inputs_from_session()
                self.update_plots()
                self.statusBar.showMessage(f'Loaded design "{session.name}"')
    
    def export_full_report(self):
        """Export a complete design report"""
        if not self.current_session:
            QMessageBox.warning(self, "Warning", "No design to export")
            return
        
        try:
            output_dir = QFileDialog.getExistingDirectory(
                self, "Select Export Directory"
            )
            
            if output_dir:
                self.session_manager.export_report(
                    self.current_session,
                    output_dir
                )
                self.statusBar.showMessage('Report exported successfully')
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
    
    def update_session_from_inputs(self):
        """Update current session with input values"""
        if not self.current_session:
            self.current_session = DesignSession()
        
        self.current_session.propellant_type = self.propellant_combo.currentText()
        self.current_session.chamber_pressure = self.chamber_pressure.value() * 1e6
        self.current_session.chamber_temperature = self.chamber_temp.value()
        self.current_session.fuel_ratio = self.fuel_ratio.value()
        self.current_session.thrust = self.thrust.value()
        self.current_session.material = self.material_combo.currentText()
        self.current_session.optimization_type = self.optimization_combo.currentText()
        self.current_session.target_value = self.target_value.value()
        
        # Update results if available
        if hasattr(self, 'current_results'):
            self.current_session.segments = self.current_results['geometry'].segments
            self.current_session.performance_metrics = self.current_results['metrics']
            self.current_session.chamber_state = self.current_results['chamber_state']
    
    def update_inputs_from_session(self):
        """Update input fields from current session"""
        if not self.current_session:
            return
        
        self.propellant_combo.setCurrentText(self.current_session.propellant_type)
        self.chamber_pressure.setValue(self.current_session.chamber_pressure / 1e6)
        self.chamber_temp.setValue(self.current_session.chamber_temperature)
        self.fuel_ratio.setValue(self.current_session.fuel_ratio)
        self.thrust.setValue(self.current_session.thrust)
        self.material_combo.setCurrentText(self.current_session.material)
        self.optimization_combo.setCurrentText(self.current_session.optimization_type)
        self.target_value.setValue(self.current_session.target_value)
        
        # Update results if available
        if self.current_session.segments:
            self.current_results = {
                'geometry': type('obj', (object,), {
                    'segments': self.current_session.segments
                }),
                'metrics': self.current_session.performance_metrics,
                'chamber_state': self.current_session.chamber_state
            }
    
    def clear_inputs(self):
        """Clear all input fields"""
        self.propellant_combo.setCurrentIndex(0)
        self.chamber_pressure.setValue(5.0)
        self.chamber_temp.setValue(3000)
        self.fuel_ratio.setValue(2.5)
        self.thrust.setValue(10000)
        self.material_combo.setCurrentIndex(0)
        self.optimization_combo.setCurrentIndex(0)
        self.target_value.setValue(3.0)
        self.current_results = None
    
    def calculate(self):
        """Calculate nozzle design based on input parameters"""
        try:
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self.statusBar.showMessage('Calculating...')
            
            # Get input parameters
            chamber_pressure = self.chamber_pressure.value() * 1e6  # Convert to Pa
            chamber_temp = self.chamber_temp.value()
            fuel_ratio = self.fuel_ratio.value()
            thrust = self.thrust.value()
            material = self.calculator.DEFAULT_MATERIALS[self.material_combo.currentText()]
            
            # Update progress
            self.progress_bar.setValue(20)
            QApplication.processEvents()
            
            # Calculate chamber state
            chamber_state = self.combustion.calculate_chamber_state(
                pressure=chamber_pressure,
                temperature=chamber_temp,
                fuel_oxidizer_ratio=fuel_ratio,
                thrust=thrust,
                propellant_type=self.propellant_combo.currentText()
            )
            
            # Update progress
            self.progress_bar.setValue(40)
            QApplication.processEvents()
            
            # Calculate nozzle geometry
            if self.optimization_combo.currentText() == "Thrust":
                geometry = self.calculator.optimize_for_thrust(
                    thrust, chamber_state, 101325)  # Sea level pressure
            else:
                geometry = self.calculator.optimize_for_mach(
                    self.target_value.value(), chamber_state, 101325)
            
            # Update progress
            self.progress_bar.setValue(60)
            QApplication.processEvents()
            
            # Store results
            self.current_results = {
                'geometry': geometry,
                'chamber_state': chamber_state,
                'metrics': geometry.performance_metrics
            }
            
            # Update plots
            self.update_plots(geometry.segments, chamber_state)
            
            # Update results summary
            self.update_results_summary(geometry.performance_metrics)
            
            # Update progress
            self.progress_bar.setValue(100)
            self.statusBar.showMessage('Calculation completed')
            
            # Hide progress bar after delay
            QTimer.singleShot(2000, self.progress_bar.hide)
            
        except Exception as e:
            self.progress_bar.hide()
            QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")
    
    def update_plots(self,
                    segments: Optional[List] = None,
                    chamber_state: Optional[object] = None):
        """Update all plots with current data"""
        if segments is None:
            # Create empty plots
            self.contour_canvas.figure.clear()
            self.performance_canvas.figure.clear()
            self.heat_canvas.figure.clear()
            self.altitude_canvas.figure.clear()
        else:
            # Update contour plot
            contour_fig = self.visualizer.create_contour_plot(
                segments, 'mach_number', 'Mach Number Distribution', 'Mach Number')
            self.contour_canvas.figure.clear()
            self.contour_canvas.figure = contour_fig
            
            # Update performance plot
            perf_fig = self.visualizer.create_performance_plot(segments, chamber_state)
            self.performance_canvas.figure.clear()
            self.performance_canvas.figure = perf_fig
            
            # Update heat transfer plot
            heat_fig = self.visualizer.create_heat_transfer_plot(segments)
            self.heat_canvas.figure.clear()
            self.heat_canvas.figure = heat_fig
            
            # Update altitude optimization plot
            if chamber_state is not None:
                alt_fig = self.visualizer.create_altitude_optimization_plot(
                    chamber_state, self.material_combo.currentText())
                self.altitude_canvas.figure.clear()
                self.altitude_canvas.figure = alt_fig
            
            # Update 3D view
            self.viewer_3d.update_nozzle(segments)
            if self.cooling_check.isChecked():
                self.viewer_3d.add_heat_flux_visualization(segments)
        
        # Refresh all canvases
        self.contour_canvas.draw()
        self.performance_canvas.draw()
        self.heat_canvas.draw()
        self.altitude_canvas.draw()
    
    def update_results_summary(self, metrics: Dict[str, float]):
        """Update the results summary with calculated metrics"""
        self.thrust_label.setText(f"{metrics['thrust_coefficient']:.3f}")
        self.isp_label.setText(f"{metrics['specific_impulse']:.0f} s")
        self.efficiency_label.setText(f"{metrics['efficiency']*100:.1f}%")
        self.exit_mach_label.setText(f"{metrics['exit_mach']:.2f}")
        
        # Update additional metrics if available
        if 'max_wall_temperature' in metrics:
            self.max_temp_label.setText(f"{metrics['max_wall_temperature']:.0f} K")
        if 'max_heat_flux' in metrics:
            self.max_heat_flux_label.setText(f"{metrics['max_heat_flux']/1e6:.1f} MW/m²")
        if 'safety_factor' in metrics:
            self.safety_factor_label.setText(f"{metrics['safety_factor']:.2f}")
    
    def export_results(self, format: str = None):
        """Export results to file"""
        try:
            if format is None:
                filename, format = QFileDialog.getSaveFileName(
                    self, "Export Results", "",
                    "CSV Files (*.csv);;PNG Files (*.png);;Excel Files (*.xlsx)")
                
                if not filename:
                    return
                
                format = filename.split('.')[-1]
            
            if format == 'csv':
                self.visualizer.export_results(self.current_results['geometry'].segments, filename, 'csv')
            elif format == 'png':
                self.visualizer.export_results(self.current_results['geometry'].segments, filename, 'png')
            elif format == 'xlsx':
                # Export to Excel with multiple sheets
                with pd.ExcelWriter(filename) as writer:
                    # Export segment data
                    segment_data = pd.DataFrame([
                        {
                            'Position (m)': s.start_x,
                            'Radius (m)': s.start_radius,
                            'Mach Number': s.mach_number,
                            'Pressure (Pa)': s.pressure,
                            'Temperature (K)': s.temperature,
                            'Wall Temperature (K)': s.wall_temperature,
                            'Heat Flux (W/m²)': s.heat_flux
                        }
                        for s in self.current_results['geometry'].segments
                    ])
                    segment_data.to_excel(writer, sheet_name='Segments', index=False)
                    
                    # Export performance metrics
                    metrics_data = pd.DataFrame([self.current_results['metrics']])
                    metrics_data.to_excel(writer, sheet_name='Performance', index=False)
            
            self.statusBar.showMessage('Results exported successfully')
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

def run_gui():
    """Run the GUI application"""
    app = QApplication(sys.argv)
    window = NozzleDesignGUI()
    window.show()
    sys.exit(app.exec_()) 