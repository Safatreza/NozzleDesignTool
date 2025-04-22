# Nozzle Design Tool

This is a Python-based tool designed to help aerospace engineers or students design nozzles for rockets. The program allows the user to input specific parameters like Mach number, altitude, and expansion ratio, then calculates and displays the nozzle profile, including shape, length, pressure gradients, and temperature gradients. It also provides a visual representation of the nozzle shape using `Matplotlib`.

## Features

- **User Input**: Prompts the user to input Mach number, altitude, and expansion ratio.
- **Nozzle Profile Calculation**: Calculates nozzle length, shape (conical or bell), and dummy pressure/temperature gradients based on the input parameters.
- **Visualization**: Uses `Matplotlib` to plot the nozzle shape and the pressure/temperature profiles.
- **Simple Interface**: User-friendly command-line interface for easy interaction.

## Requirements

Before running the project, make sure you have the required dependencies installed:

- Python 3.x
- `Matplotlib` for plotting the nozzle shape and gradients.

To install `Matplotlib`, run:

```bash
pip install matplotlib
