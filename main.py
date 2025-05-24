from nozzle_design import UserInterface, NozzleDesigner, NozzleVisualizer
from nozzle_design.gui import run_gui

def main():
    # Create UI instance
    ui = UserInterface()
    
    # Get user input
    name, mach, altitude, expansion_ratio, gas_properties, nozzle_type, chamber_data = ui.get_user_input()

    # Calculate nozzle profile
    nozzle_designer = NozzleDesigner()
    profile = nozzle_designer.calculate_profile(
        mach=mach,
        altitude=altitude,
        expansion_ratio=expansion_ratio,
        gas_properties=gas_properties,
        nozzle_type=nozzle_type,
        chamber_state=chamber_data['chamber_state']
    )

    # Display results
    ui.display_output(profile, name, chamber_data['chamber_state'])

    # Plot nozzle profile
    NozzleVisualizer.plot_profile(profile)

if __name__ == "__main__":
    run_gui()

