# Nozzle Design Tool

A comprehensive tool for designing and analyzing rocket engine nozzles, featuring:
- 2D and 3D visualization of nozzle geometry
- Performance analysis and optimization
- Heat transfer analysis
- Machine learning-based optimization
- Export to various CAD formats
- Web interface for easy access

## Features

- **Nozzle Design**
  - Contour optimization for maximum thrust
  - Target Mach number optimization
  - Multiple propellant combinations
  - Material selection and thermal analysis

- **Visualization**
  - 2D contour plots
  - Performance parameter plots
  - Heat transfer visualization
  - Interactive 3D view
  - Altitude optimization plots

- **Analysis**
  - Thrust coefficient calculation
  - Specific impulse analysis
  - Heat transfer analysis
  - Wall temperature prediction
  - Efficiency calculations

- **Optimization**
  - Machine learning-based optimization
  - Multi-objective optimization
  - Constraint handling
  - Sensitivity analysis

- **Export**
  - STL format for 3D printing
  - OBJ format for visualization
  - STEP format for CAD
  - IGES format for CAD
  - Full design report generation

## Installation

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nozzle-design-tool.git
   cd nozzle-design-tool
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   # For desktop GUI
   python -m nozzle_design.gui

   # For web interface
   python -m nozzle_design.web_app
   ```

### Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t nozzle-design-tool .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 nozzle-design-tool
   ```

3. Access the web interface at `http://localhost:5000`

## Usage

### Desktop GUI

1. Launch the application
2. Enter input parameters:
   - Propellant type
   - Chamber conditions
   - Thrust requirements
   - Optimization type
3. Click "Calculate" to generate the design
4. Use the "Optimize" button for advanced optimization
5. View results in various plots and 3D view
6. Export the design in your preferred format

### Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. Use the web interface to:
   - Create new designs
   - Load saved designs
   - View interactive plots
   - Export results
   - Generate reports

## Development

### Project Structure

```
nozzle_design/
├── __init__.py
├── engineering_calculations.py
├── combustion.py
├── visualization.py
├── visualization_3d.py
├── gui.py
├── web_app.py
├── ml_optimization.py
├── model_export.py
└── session_manager.py
```

### Running Tests

```bash
pytest tests/
```

### Code Style

The project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

Run the checks:
```bash
black .
flake8
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NASA CEA for thermodynamic calculations
- OpenMDAO for optimization framework
- VTK for 3D visualization
- Plotly for interactive plots
