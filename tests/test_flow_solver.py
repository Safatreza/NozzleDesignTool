"""Unit tests for compressible flow calculations."""

import pytest
import numpy as np
from nozzle_design.flow_solver import FlowSolver

@pytest.fixture
def flow_solver():
    """Create a flow solver instance for testing."""
    return FlowSolver(gamma=1.4, R=287.0)

@pytest.fixture
def chamber_state():
    """Create a chamber state dictionary for testing."""
    return {
        'pressure': 10e6,  # 10 MPa
        'temperature': 3000.0,  # 3000 K
        'throat_area': 0.01,  # 0.01 m²
        'gamma': 1.4,
        'gas_constant': 287.0
    }

def test_calculate_flow_properties(flow_solver, chamber_state):
    """Test flow properties calculation."""
    # Test subsonic flow
    subsonic_props = flow_solver.calculate_flow_properties(
        area_ratio=0.5,
        chamber_state=chamber_state
    )
    assert subsonic_props['mach'] < 1.0
    assert subsonic_props['pressure'] > 0
    assert subsonic_props['temperature'] > 0
    
    # Test supersonic flow
    supersonic_props = flow_solver.calculate_flow_properties(
        area_ratio=2.0,
        chamber_state=chamber_state
    )
    assert supersonic_props['mach'] > 1.0
    assert supersonic_props['pressure'] > 0
    assert supersonic_props['temperature'] > 0
    
    # Test throat conditions
    throat_props = flow_solver.calculate_flow_properties(
        area_ratio=1.0,
        chamber_state=chamber_state
    )
    assert abs(throat_props['mach'] - 1.0) < 0.01
    assert throat_props['pressure'] > 0
    assert throat_props['temperature'] > 0

def test_calculate_mach_from_area_ratio(flow_solver):
    """Test Mach number calculation from area ratio."""
    # Test subsonic solution
    mach_sub = flow_solver._calculate_mach_from_area_ratio(0.5)
    assert mach_sub < 1.0
    
    # Test supersonic solution
    mach_sup = flow_solver._calculate_mach_from_area_ratio(2.0)
    assert mach_sup > 1.0
    
    # Test throat conditions
    mach_throat = flow_solver._calculate_mach_from_area_ratio(1.0)
    assert abs(mach_throat - 1.0) < 0.01

def test_calculate_pressure(flow_solver):
    """Test pressure calculation."""
    p0 = 10e6  # 10 MPa
    mach = 2.0
    
    pressure = flow_solver._calculate_pressure(mach, p0)
    assert pressure > 0
    assert pressure < p0  # Static pressure should be less than total pressure

def test_calculate_temperature(flow_solver):
    """Test temperature calculation."""
    T0 = 3000.0  # 3000 K
    mach = 2.0
    
    temperature = flow_solver._calculate_temperature(mach, T0)
    assert temperature > 0
    assert temperature < T0  # Static temperature should be less than total temperature

def test_calculate_mass_flow(flow_solver, chamber_state):
    """Test mass flow calculation."""
    throat_area = 0.01  # 0.01 m²
    
    mass_flow = flow_solver.calculate_mass_flow(throat_area, chamber_state)
    assert mass_flow > 0
    
    # For given conditions, mass flow should be roughly 10 kg/s
    assert 5.0 < mass_flow < 15.0

def test_calculate_thrust(flow_solver, chamber_state):
    """Test thrust calculation."""
    exit_area = 0.02  # 0.02 m²
    ambient_pressure = 101325.0  # 1 atm
    
    thrust = flow_solver.calculate_thrust(
        exit_area=exit_area,
        chamber_state=chamber_state,
        ambient_pressure=ambient_pressure
    )
    assert thrust > 0
    
    # For given conditions, thrust should be roughly 100 kN
    assert 50e3 < thrust < 150e3

def test_isentropic_relations(flow_solver):
    """Test isentropic flow relations."""
    # Test that area ratio equation is satisfied
    def check_area_ratio(M: float, A_ratio: float) -> bool:
        """Check if area ratio equation is satisfied."""
        gamma = flow_solver.gamma
        term1 = 1/M
        term2 = ((2/(gamma + 1)) * (1 + (gamma - 1)/2 * M**2))**((gamma + 1)/(2*(gamma - 1)))
        return abs(term1 * term2 - A_ratio) < 1e-6
    
    # Test subsonic solution
    mach_sub = flow_solver._calculate_mach_from_area_ratio(0.5)
    assert check_area_ratio(mach_sub, 0.5)
    
    # Test supersonic solution
    mach_sup = flow_solver._calculate_mach_from_area_ratio(2.0)
    assert check_area_ratio(mach_sup, 2.0)
    
    # Test throat conditions
    mach_throat = flow_solver._calculate_mach_from_area_ratio(1.0)
    assert check_area_ratio(mach_throat, 1.0) 