from flask import Flask, render_template, request, jsonify, send_file
import os
from pathlib import Path
import json
import tempfile
from datetime import datetime

from .engineering_calculations import NozzleGeometryCalculator, OptimizationConstraints
from .combustion import CombustionChamber
from .ml_optimization import MultivariableOptimizer
from .model_export import NozzleModelExporter
from .session_manager import SessionManager

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize components
calculator = NozzleGeometryCalculator()
combustion = CombustionChamber()
optimizer = MultivariableOptimizer(calculator)
session_manager = SessionManager()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate nozzle design"""
    try:
        data = request.json
        
        # Get input parameters
        chamber_pressure = float(data['chamber_pressure']) * 1e6  # Convert to Pa
        chamber_temp = float(data['chamber_temperature'])
        fuel_ratio = float(data['fuel_ratio'])
        thrust = float(data['thrust'])
        
        # Calculate chamber state
        chamber_state = combustion.calculate_chamber_state(
            pressure=chamber_pressure,
            temperature=chamber_temp,
            fuel_oxidizer_ratio=fuel_ratio,
            thrust=thrust,
            propellant_type=data['propellant_type']
        )
        
        # Calculate nozzle geometry
        if data['optimization_type'] == 'thrust':
            geometry = calculator.optimize_for_thrust(
                thrust, chamber_state, 101325)  # Sea level pressure
        else:
            geometry = calculator.optimize_for_mach(
                float(data['target_value']), chamber_state, 101325)
        
        # Prepare response
        response = {
            'geometry': {
                'segments': [
                    {
                        'start_x': s.start_x,
                        'end_x': s.end_x,
                        'start_radius': s.start_radius,
                        'end_radius': s.end_radius,
                        'angle': s.angle,
                        'length': s.length,
                        'area_ratio': s.area_ratio,
                        'mach_number': s.mach_number,
                        'pressure': s.pressure,
                        'temperature': s.temperature,
                        'wall_temperature': s.wall_temperature,
                        'heat_flux': s.heat_flux
                    }
                    for s in geometry.segments
                ],
                'performance_metrics': geometry.performance_metrics
            },
            'chamber_state': chamber_state.__dict__
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/optimize', methods=['POST'])
def optimize():
    """Optimize nozzle design"""
    try:
        data = request.json
        
        # Get input parameters
        chamber_pressure = float(data['chamber_pressure']) * 1e6
        chamber_temp = float(data['chamber_temperature'])
        fuel_ratio = float(data['fuel_ratio'])
        thrust = float(data['thrust'])
        
        # Calculate chamber state
        chamber_state = combustion.calculate_chamber_state(
            pressure=chamber_pressure,
            temperature=chamber_temp,
            fuel_oxidizer_ratio=fuel_ratio,
            thrust=thrust,
            propellant_type=data['propellant_type']
        )
        
        # Set up constraints
        constraints = OptimizationConstraints(
            max_divergence_angle=float(data.get('max_divergence_angle', 15.0)),
            min_divergence_angle=float(data.get('min_divergence_angle', 5.0)),
            max_length_ratio=float(data.get('max_length_ratio', 3.0)),
            min_length_ratio=float(data.get('min_length_ratio', 1.5)),
            max_wall_temp=float(data.get('max_wall_temp', 1500.0)),
            max_heat_flux=float(data.get('max_heat_flux', 2.0e6)),
            min_safety_factor=float(data.get('min_safety_factor', 1.5)),
            max_weight=float(data.get('max_weight', 100.0))
        )
        
        # Run optimization
        result = optimizer.optimize(
            chamber_state=chamber_state,
            constraints=constraints,
            objective=data.get('objective', 'thrust'),
            method=data.get('method', 'differential_evolution')
        )
        
        # Prepare response
        response = {
            'geometry': {
                'segments': [
                    {
                        'start_x': s.start_x,
                        'end_x': s.end_x,
                        'start_radius': s.start_radius,
                        'end_radius': s.end_radius,
                        'angle': s.angle,
                        'length': s.length,
                        'area_ratio': s.area_ratio,
                        'mach_number': s.mach_number,
                        'pressure': s.pressure,
                        'temperature': s.temperature,
                        'wall_temperature': s.wall_temperature,
                        'heat_flux': s.heat_flux
                    }
                    for s in result['geometry'].segments
                ],
                'performance_metrics': result['geometry'].performance_metrics
            },
            'optimization_result': {
                'divergence_angle': result['divergence_angle'],
                'length_ratio': result['length_ratio'],
                'objective_value': result['objective_value'],
                'success': result['success'],
                'message': result['message']
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/export', methods=['POST'])
def export_model():
    """Export nozzle model to various formats"""
    try:
        data = request.json
        format = data.get('format', 'stl')
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create exporter
            exporter = NozzleModelExporter([
                NozzleSegment(**s) for s in data['segments']
            ])
            
            # Export file
            filename = f"nozzle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if format == 'all':
                exporter.export_all_formats(temp_dir, filename)
                # Create zip file
                import zipfile
                zip_path = os.path.join(temp_dir, f"{filename}.zip")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for ext in ['stl', 'obj', 'step', 'iges']:
                        zipf.write(
                            os.path.join(temp_dir, f"{filename}.{ext}"),
                            f"{filename}.{ext}"
                        )
                return send_file(zip_path, as_attachment=True)
            else:
                file_path = os.path.join(temp_dir, f"{filename}.{format}")
                if format == 'stl':
                    exporter.export_stl(file_path)
                elif format == 'obj':
                    exporter.export_obj(file_path)
                elif format == 'step':
                    exporter.export_step(file_path)
                elif format == 'iges':
                    exporter.export_iges(file_path)
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all saved design sessions"""
    try:
        sessions = session_manager.list_sessions()
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Get a specific design session"""
    try:
        session = session_manager.load_session(session_id)
        return jsonify(session.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sessions', methods=['POST'])
def save_session():
    """Save a new design session"""
    try:
        data = request.json
        session = DesignSession(**data)
        session_id = session_manager.save_session(session)
        return jsonify({'id': session_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a design session"""
    try:
        session_manager.delete_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def run_web_app(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """Run the Flask web application"""
    app.run(host=host, port=port, debug=debug) 