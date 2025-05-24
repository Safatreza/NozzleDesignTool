from typing import Dict, Tuple
from .models import NozzleProfile
from .combustion import CombustionChamber
from .optimization import NozzleOptimizer, NozzleGeometry

class UserInterface:
    """Handles all user input and output operations"""
    
    def __init__(self):
        self.combustion = CombustionChamber()
        self.optimizer = NozzleOptimizer()
    
    def get_user_input(self) -> Tuple[str, float, float, float, Dict[str, float], str, Dict]:
        """Get user input for nozzle design parameters"""
        try:
            name = input("Enter your name: ").strip()
            
            # Get propellant type
            print("\nAvailable propellant combinations:")
            propellants = self.combustion.get_available_propellants()
            for i, (prop_type, _) in enumerate(propellants.items(), 1):
                print(f"{i}. {prop_type}")
            prop_choice = input("Select propellant type (1-3): ").strip()
            propellant_type = list(propellants.keys())[int(prop_choice) - 1]
            
            # Get combustion chamber conditions
            print("\nEnter combustion chamber conditions:")
            chamber_pressure = float(input("Chamber pressure (Pa): "))
            chamber_temp = float(input("Chamber temperature (K): "))
            fuel_oxidizer_ratio = float(input("Fuel-oxidizer ratio (mass): "))
            thrust = float(input("Required thrust (N): "))
            
            # Get optimization mode
            print("\nSelect optimization mode:")
            print("1. Optimize for thrust")
            print("2. Optimize for exit Mach number")
            opt_choice = input("Select mode (1-2): ").strip()
            
            if opt_choice == "1":
                target_thrust = float(input("Target thrust (N): "))
                target_mach = None
            else:
                target_mach = float(input("Target exit Mach number: "))
                target_thrust = None
            
            # Get back pressure
            print("\nEnter back pressure conditions:")
            use_atmospheric = input("Use atmospheric pressure at altitude? (y/n): ").lower() == 'y'
            if use_atmospheric:
                altitude = float(input("Altitude (m): "))
                back_pressure = None  # Will be calculated from altitude
            else:
                back_pressure = float(input("Back pressure (Pa): "))
                altitude = 0.0
            
            # Calculate combustion state
            chamber_state = self.combustion.calculate_chamber_state(
                pressure=chamber_pressure,
                temperature=chamber_temp,
                fuel_oxidizer_ratio=fuel_oxidizer_ratio,
                thrust=thrust,
                propellant_type=propellant_type
            )
            
            # Optimize nozzle geometry
            if target_thrust is not None:
                geometry = self.optimizer.optimize_for_thrust(
                    target_thrust, chamber_state, back_pressure)
            else:
                geometry = self.optimizer.optimize_for_mach(
                    target_mach, chamber_state, back_pressure)
            
            return name, geometry.performance_metrics['exit_mach'], altitude, geometry.area_ratio, chamber_state.gas_properties, 'bell', {
                'chamber_state': chamber_state,
                'propellant_type': propellant_type,
                'back_pressure': back_pressure,
                'optimized_geometry': geometry
            }
        except ValueError as e:
            print(f"⚠️ Invalid input: {str(e)}")
            return self.get_user_input()

    def display_output(self, profile: NozzleProfile, name: str, chamber_state=None, optimized_geometry=None) -> None:
        """Display the nozzle design results"""
        print(f"\n🚀 Welcome, {name}! Here's your nozzle design result:")
        
        # Display combustion chamber information
        if chamber_state:
            print("\nCombustion Chamber:")
            print(f"Chamber Pressure: {chamber_state.pressure/1e6:.2f} MPa")
            print(f"Chamber Temperature: {chamber_state.temperature:.1f} K")
            print(f"Fuel-Oxidizer Ratio: {chamber_state.fuel_oxidizer_ratio:.2f}")
            print(f"Mass Flow Rate: {chamber_state.mass_flow:.2f} kg/s")
            print(f"Characteristic Velocity: {chamber_state.characteristic_velocity:.0f} m/s")
        
        # Display optimized geometry information
        if optimized_geometry:
            print("\nOptimized Nozzle Geometry:")
            print(f"Area Ratio: {optimized_geometry.area_ratio:.2f}")
            print(f"Length: {optimized_geometry.length:.3f} m")
            print(f"Divergence Angle: {optimized_geometry.divergence_angle:.1f}°")
            print(f"Throat Radius: {optimized_geometry.throat_radius*1000:.1f} mm")
            print(f"Exit Radius: {optimized_geometry.exit_radius*1000:.1f} mm")
            
            print("\nPerformance Metrics:")
            print(f"Thrust Coefficient: {optimized_geometry.performance_metrics['thrust_coefficient']:.3f}")
            print(f"Specific Impulse: {optimized_geometry.performance_metrics['specific_impulse']:.0f} s")
            print(f"Efficiency: {optimized_geometry.performance_metrics['efficiency']*100:.1f}%")
            
            # Display segment information
            print("\nNozzle Segments:")
            print("Segment  Start (mm)  End (mm)  Length (mm)  Angle (°)  Mach  Pressure (kPa)  Temp (K)")
            print("-" * 80)
            for i, segment in enumerate(optimized_geometry.segments):
                print(f"{i+1:3d}     {segment.start_x*1000:8.1f}  {segment.end_x*1000:8.1f}  "
                      f"{segment.length*1000:10.1f}  {segment.angle:8.1f}  {segment.mach_number:4.2f}  "
                      f"{segment.pressure/1000:12.1f}  {segment.temperature:7.1f}")
        
        print(f"\nNozzle Type: {profile.shape}")
        print(f"Nozzle Length: {profile.length:.2f} m")
        
        # Display flow properties
        print("\nFlow Properties:")
        print(f"Exit Pressure: {profile.pressure_gradient[-1]/1e3:.1f} kPa")
        print(f"Exit Temperature: {profile.temperature_gradient[-1]:.1f} K")
        
        # Display flow regime information
        if hasattr(profile, 'flow_regime'):
            print(f"\nFlow Regime: {profile.flow_regime}")
            if profile.flow_regime == "over-expanded":
                print("⚠️ Warning: Nozzle is over-expanded. Shock waves may be present.")
            elif profile.flow_regime == "under-expanded":
                print("ℹ️ Note: Nozzle is under-expanded. Expansion waves will form at exit.")
            elif profile.flow_regime == "choked":
                print("ℹ️ Note: Flow is choked at throat.")
        
        # Display gas properties
        print("\nGas Properties:")
        print(f"Molecular Weight: {profile.gas_properties.molecular_weight:.2f} kg/mol")
        print(f"Specific Heat Ratio (γ): {profile.gas_properties.gamma:.3f}")
        print(f"Specific Heat (Cp): {profile.gas_properties.cp:.1f} J/kg·K")
        
        # Display shock information if present
        if any(abs(p2/p1 - 1) > 0.1 for p1, p2 in zip(profile.pressure_gradient[:-1], profile.pressure_gradient[1:])):
            print("\n⚠️ Shock wave detected in the nozzle!") 