"""Unit tests for Cantera visualization."""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import cantera as ct
from nozzle_design.cantera_visualization import CanteraVisualizer
from nozzle_design.nozzle_geometry import NozzleSegment

@pytest.fixture
def nozzle_segments():
    """Create sample nozzle segments for testing."""
    return [
        NozzleSegment(
            start_x=0.0,
            start_radius=0.05,
            end_x=0.1,
            end_radius=0.03,
            angle=15.0,
            length=0.1,
            area_ratio=1.0,
            mach_number=0.5,
            pressure=10e6,
            temperature=3000.0,
            wall_temperature=1000.0,
            heat_flux=1e6
        ),
        NozzleSegment(
            start_x=0.1,
            start_radius=0.03,
            end_x=0.2,
            end_radius=0.03,
            angle=0.0,
            length=0.1,
            area_ratio=1.0,
            mach_number=1.0,
            pressure=5e6,
            temperature=2500.0,
            wall_temperature=800.0,
            heat_flux=2e6
        ),
        NozzleSegment(
            start_x=0.2,
            start_radius=0.03,
            end_x=0.4,
            end_radius=0.06,
            angle=15.0,
            length=0.2,
            area_ratio=4.0,
            mach_number=2.0,
            pressure=1e6,
            temperature=2000.0,
            wall_temperature=600.0,
            heat_flux=3e6
        )
    ]

@pytest.fixture
def chamber_state():
    """Create a chamber state dictionary for testing."""
    return {
        'pressure': 10e6,  # 10 MPa
        'temperature': 3000.0,  # 3000 K
        'mass_flow': 10.0,  # 10 kg/s
        'gamma': 1.4,
        'gas_constant': 287.0,
        'area_ratio': 10.0,
        'ambient_pressure': 101325.0  # 1 atm
    }

@pytest.fixture
def visualizer(nozzle_segments):
    """Create a Cantera visualizer instance for testing."""
    return CanteraVisualizer(nozzle_segments)

def test_setup_flow(visualizer, chamber_state):
    """Test flow setup."""
    visualizer.setup_flow(chamber_state, propellant='H2:1, O2:0.5')
    assert visualizer.flow_data is not None
    assert 'x' in visualizer.flow_data
    assert 'mach' in visualizer.flow_data
    assert 'pressure' in visualizer.flow_data
    assert 'temperature' in visualizer.flow_data

def test_flow_properties(visualizer, chamber_state):
    """Test flow property calculations."""
    visualizer.setup_flow(chamber_state)
    flow_data = visualizer.flow_data
    
    # Check property ranges
    assert np.all(flow_data['mach'] >= 0)
    assert np.all(flow_data['pressure'] > 0)
    assert np.all(flow_data['temperature'] > 0)
    assert np.all(flow_data['density'] > 0)
    assert np.all(flow_data['velocity'] >= 0)
    
    # Check Mach number progression
    assert flow_data['mach'][0] < 1.0  # Subsonic at inlet
    assert abs(flow_data['mach'][1] - 1.0) < 0.1  # Sonic at throat
    assert flow_data['mach'][-1] > 1.0  # Supersonic at exit

def test_plot_flow_properties(visualizer, chamber_state):
    """Test flow property plotting."""
    visualizer.setup_flow(chamber_state)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "flow_properties.png"
        visualizer.plot_flow_properties(
            properties=['mach', 'pressure', 'temperature'],
            save_path=str(filename)
        )
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_plot_contour(visualizer, chamber_state):
    """Test contour plotting."""
    visualizer.setup_flow(chamber_state)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "contour.png"
        visualizer.plot_contour(
            property_name='mach',
            n_levels=20,
            save_path=str(filename)
        )
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_export_flow_data(visualizer, chamber_state):
    """Test flow data export."""
    visualizer.setup_flow(chamber_state)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = Path(tmpdir) / "flow_data.npz"
        visualizer.export_flow_data(str(filename))
        assert filename.exists()
        assert filename.stat().st_size > 0

def test_calculate_performance_metrics(visualizer, chamber_state):
    """Test performance metric calculations."""
    visualizer.setup_flow(chamber_state)
    metrics = visualizer.calculate_performance_metrics()
    
    assert 'thrust_coefficient' in metrics
    assert 'specific_impulse' in metrics
    assert 'exit_mach' in metrics
    assert 'exit_pressure' in metrics
    assert 'exit_temperature' in metrics
    assert 'exit_velocity' in metrics
    
    # Check metric ranges
    assert metrics['thrust_coefficient'] > 0
    assert metrics['specific_impulse'] > 0
    assert metrics['exit_mach'] > 1.0
    assert metrics['exit_pressure'] > 0
    assert metrics['exit_temperature'] > 0
    assert metrics['exit_velocity'] > 0

def test_thrust_coefficient_calculation(visualizer):
    """Test thrust coefficient calculation."""
    thrust_coeff = visualizer._calculate_thrust_coefficient(
        exit_mach=2.0,
        exit_pressure=1e6,
        chamber_pressure=10e6,
        ambient_pressure=101325.0
    )
    
    assert thrust_coeff > 0
    assert thrust_coeff < 2.0  # Thrust coefficient should be less than 2

def test_gas_properties(visualizer, chamber_state):
    """Test gas property calculations."""
    visualizer.setup_flow(chamber_state)
    
    # Check gas properties
    assert visualizer.gas is not None
    assert visualizer.gas.T == chamber_state['temperature']
    assert visualizer.gas.P == chamber_state['pressure']
    
    # Check gas composition
    assert visualizer.gas['H2'].X[0] > 0
    assert visualizer.gas['O2'].X[0] > 0

def test_flow_consistency(visualizer, chamber_state):
    """Test flow property consistency."""
    visualizer.setup_flow(chamber_state)
    flow_data = visualizer.flow_data
    
    # Check that properties are consistent with isentropic flow
    for i in range(len(flow_data['x'])):
        mach = flow_data['mach'][i]
        pressure = flow_data['pressure'][i]
        temperature = flow_data['temperature'][i]
        
        # Check isentropic relations
        gamma = visualizer.gas.cp / visualizer.gas.cv
        pressure_ratio = pressure / chamber_state['pressure']
        temperature_ratio = temperature / chamber_state['temperature']
        
        expected_pressure_ratio = (1 + (gamma - 1)/2 * mach**2)**(-gamma/(gamma - 1))
        expected_temperature_ratio = (1 + (gamma - 1)/2 * mach**2)**(-1)
        
        assert abs(pressure_ratio - expected_pressure_ratio) < 0.1
        assert abs(temperature_ratio - expected_temperature_ratio) < 0.1 