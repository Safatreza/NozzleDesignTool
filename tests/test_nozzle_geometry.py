"""Unit tests for nozzle geometry calculations."""

import pytest
import numpy as np
from nozzle_design.nozzle_geometry import NozzleGeometryCalculator, NozzleSegment, NozzleGeometry
from nozzle_design.flow_solver import FlowSolver
from nozzle_design.materials import get_material

@pytest.fixture
def flow_solver():
    """Create a flow solver instance for testing."""
    return FlowSolver(gamma=1.4, R=287.0)

@pytest.fixture
def calculator(flow_solver):
    """Create a nozzle geometry calculator instance for testing."""
    return NozzleGeometryCalculator(flow_solver)

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
def material():
    """Create a material instance for testing."""
    return get_material('copper')

def test_calculate_geometry(calculator, chamber_state, material):
    """Test nozzle geometry calculation."""
    geometry = calculator.calculate_geometry(
        divergence_angle=15.0,
        length_ratio=2.0,
        chamber_state=chamber_state,
        material=material
    )
    
    # Check that we got a NozzleGeometry object
    assert isinstance(geometry, NozzleGeometry)
    
    # Check that we have segments
    assert len(geometry.segments) > 0
    
    # Check segment properties
    segment = geometry.segments[0]
    assert isinstance(segment, NozzleSegment)
    assert segment.start_x >= 0
    assert segment.end_x > segment.start_x
    assert segment.start_radius > 0
    assert segment.end_radius > segment.start_radius
    assert segment.angle > 0
    assert segment.length > 0
    assert segment.area_ratio > 0
    assert segment.mach_number > 0
    assert segment.pressure > 0
    assert segment.temperature > 0
    assert segment.wall_temperature > 0
    assert segment.heat_flux > 0
    
    # Check performance metrics
    metrics = geometry.performance_metrics
    assert 'thrust_coefficient' in metrics
    assert 'specific_impulse' in metrics
    assert 'efficiency' in metrics
    assert 'exit_mach' in metrics
    assert metrics['thrust_coefficient'] > 0
    assert metrics['specific_impulse'] > 0
    assert 0 < metrics['efficiency'] <= 1
    assert metrics['exit_mach'] > 1

def test_optimize_for_thrust(calculator, chamber_state, material):
    """Test thrust optimization."""
    geometry = calculator.optimize_for_thrust(
        thrust=100e3,  # 100 kN
        chamber_state=chamber_state,
        ambient_pressure=101325.0,
        material=material
    )
    
    # Check that we got a NozzleGeometry object
    assert isinstance(geometry, NozzleGeometry)
    
    # Check that we have segments
    assert len(geometry.segments) > 0
    
    # Check performance metrics
    metrics = geometry.performance_metrics
    assert metrics['thrust_coefficient'] > 0
    assert metrics['specific_impulse'] > 0
    assert 0 < metrics['efficiency'] <= 1
    assert metrics['exit_mach'] > 1

def test_optimize_for_mach(calculator, chamber_state, material):
    """Test Mach number optimization."""
    target_mach = 3.0
    geometry = calculator.optimize_for_mach(
        target_mach=target_mach,
        chamber_state=chamber_state,
        ambient_pressure=101325.0,
        material=material
    )
    
    # Check that we got a NozzleGeometry object
    assert isinstance(geometry, NozzleGeometry)
    
    # Check that we have segments
    assert len(geometry.segments) > 0
    
    # Check exit Mach number
    exit_mach = geometry.segments[-1].mach_number
    assert abs(exit_mach - target_mach) < 0.1  # Within 10% of target
    
    # Check performance metrics
    metrics = geometry.performance_metrics
    assert metrics['thrust_coefficient'] > 0
    assert metrics['specific_impulse'] > 0
    assert 0 < metrics['efficiency'] <= 1

def test_calculate_throat_area(calculator, chamber_state):
    """Test throat area calculation."""
    throat_area = calculator._calculate_throat_area(chamber_state)
    assert throat_area > 0
    
    # Check that throat area is reasonable
    # For given conditions, throat area should be roughly 0.01 m²
    assert 0.001 < throat_area < 0.1

def test_calculate_thrust_coefficient(calculator):
    """Test thrust coefficient calculation."""
    thrust_coeff = calculator._calculate_thrust_coefficient(
        exit_pressure=101325.0,
        exit_mach=3.0,
        chamber_pressure=10e6,
        ambient_pressure=101325.0,
        gamma=1.4
    )
    assert thrust_coeff > 0
    assert thrust_coeff < 2.0  # Thrust coefficient should be less than 2

def test_calculate_specific_impulse(calculator):
    """Test specific impulse calculation."""
    isp = calculator._calculate_specific_impulse(
        thrust_coeff=1.5,
        chamber_pressure=10e6,
        throat_area=0.01,
        mass_flow=10.0
    )
    assert isp > 0
    assert isp < 1000  # Isp should be less than 1000 seconds

def test_calculate_efficiency(calculator):
    """Test efficiency calculation."""
    efficiency = calculator._calculate_efficiency(
        thrust_coeff=1.5,
        ideal_thrust_coeff=1.6
    )
    assert 0 < efficiency <= 1
    assert abs(efficiency - 0.9375) < 1e-6  # 1.5/1.6 = 0.9375 