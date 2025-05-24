# Nozzle Design Tool

A comprehensive Python-based tool for designing and analyzing rocket nozzles. This tool provides advanced features for nozzle design, flow analysis, and visualization using Gmsh and Cantera.

## Features

- **Nozzle Design**
  - Conical and bell nozzle geometries
  - Customizable expansion ratios
  - Material selection and thermal analysis
  - Performance optimization

- **Flow Analysis**
  - Compressible flow calculations
  - Real gas effects using Cantera
  - Multiple flow regimes support
  - Performance metrics calculation

- **Visualization**
  - 3D mesh generation with Gmsh
  - Flow property visualization
  - Contour plots
  - Interactive 3D views

- **Export Capabilities**
  - STL, OBJ, STEP, and IGES formats
  - Flow data export
  - Performance reports
  - Manufacturing drawings

## Installation

### Prerequisites
- Python 3.9 or higher
- Docker (optional, for containerized deployment)

### Local Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Safatreza/NozzleDesignTool.git
   cd NozzleDesignTool
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

### Docker Installation
1. Build the Docker image:
   ```bash
   docker build -t nozzle-design-tool .
   ```

2. Run the container:
   ```bash
   docker run -it --rm nozzle-design-tool
   ```

## Usage

### Basic Usage
```python
from nozzle_design import NozzleDesigner

# Create a nozzle designer instance
designer = NozzleDesigner(
    chamber_pressure=10e6,  # 10 MPa
    chamber_temperature=3000,  # 3000 K
    exit_pressure=101325,  # 1 atm
    expansion_ratio=10.0,
    material='copper'
)

# Generate nozzle geometry
nozzle = designer.design_nozzle()

# Analyze flow
flow_data = designer.analyze_flow()

# Visualize results
designer.visualize()
```

### Advanced Usage
```python
from nozzle_design import NozzleDesigner
from nozzle_design.materials import get_material

# Create custom nozzle design
designer = NozzleDesigner(
    chamber_pressure=10e6,
    chamber_temperature=3000,
    exit_pressure=101325,
    expansion_ratio=10.0,
    material=get_material('inconel'),
    optimization_target='thrust'
)

# Optimize nozzle design
optimized_nozzle = designer.optimize()

# Export results
designer.export_results('nozzle_design.zip')
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8

# Type checking
mypy nozzle_design/
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

- Gmsh for mesh generation
- Cantera for flow analysis
- NASA CEA for thermodynamic properties

## Contact

For questions and support, please open an issue in the GitHub repository.
