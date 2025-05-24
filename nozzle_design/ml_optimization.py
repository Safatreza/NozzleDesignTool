import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from scipy.optimize import minimize, differential_evolution
import pandas as pd
from typing import Dict, List, Tuple, Optional
import joblib
import os
from dataclasses import dataclass

from .engineering_calculations import NozzleGeometryCalculator, NozzleSegment
from .combustion import CombustionState

@dataclass
class OptimizationConstraints:
    """Constraints for nozzle optimization"""
    max_divergence_angle: float = 15.0  # degrees
    min_divergence_angle: float = 5.0   # degrees
    max_length_ratio: float = 3.0       # L/D ratio
    min_length_ratio: float = 1.5       # L/D ratio
    max_wall_temp: float = 1500.0       # K
    max_heat_flux: float = 2.0e6        # W/m²
    min_safety_factor: float = 1.5      # dimensionless
    max_weight: float = 100.0           # kg

class MLNozzleOptimizer:
    """Machine learning-based nozzle optimization"""
    
    def __init__(self, model_path: str = "models/nozzle_ml_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.load_or_create_model()
    
    def load_or_create_model(self):
        """Load existing model or create new one"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
    
    def prepare_features(self, design_params: Dict) -> np.ndarray:
        """Prepare features for ML model"""
        features = np.array([
            design_params['chamber_pressure'],
            design_params['chamber_temperature'],
            design_params['fuel_ratio'],
            design_params['thrust'],
            design_params['divergence_angle'],
            design_params['length_ratio']
        ]).reshape(1, -1)
        return self.scaler.fit_transform(features)
    
    def predict_performance(self, design_params: Dict) -> Dict[str, float]:
        """Predict nozzle performance using ML model"""
        features = self.prepare_features(design_params)
        predictions = self.model.predict(features)[0]
        
        return {
            'thrust_coefficient': predictions[0],
            'specific_impulse': predictions[1],
            'efficiency': predictions[2],
            'exit_mach': predictions[3]
        }
    
    def train_model(self, training_data: pd.DataFrame):
        """Train the ML model with historical data"""
        X = training_data[['chamber_pressure', 'chamber_temperature', 'fuel_ratio',
                          'thrust', 'divergence_angle', 'length_ratio']]
        y = training_data[['thrust_coefficient', 'specific_impulse', 'efficiency', 'exit_mach']]
        
        X_scaled = self.scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
        
        self.model.fit(X_train, y_train)
        score = self.model.score(X_test, y_test)
        
        # Save the trained model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        
        return score

class MultivariableOptimizer:
    """Multivariable optimization engine for nozzle design"""
    
    def __init__(self, calculator: NozzleGeometryCalculator):
        self.calculator = calculator
        self.ml_optimizer = MLNozzleOptimizer()
    
    def optimize(self,
                chamber_state: CombustionState,
                constraints: OptimizationConstraints,
                objective: str = 'thrust',
                method: str = 'differential_evolution') -> Dict:
        """Optimize nozzle design for multiple objectives"""
        
        def objective_function(x):
            """Objective function for optimization"""
            divergence_angle, length_ratio = x
            
            # Calculate nozzle geometry
            geometry = self.calculator.calculate_geometry(
                divergence_angle=divergence_angle,
                length_ratio=length_ratio,
                chamber_state=chamber_state
            )
            
            # Calculate performance metrics
            metrics = geometry.performance_metrics
            
            if objective == 'thrust':
                return -metrics['thrust_coefficient']  # Negative for maximization
            elif objective == 'efficiency':
                return -metrics['efficiency']
            elif objective == 'weight':
                return self.calculate_weight(geometry)
            else:
                return -metrics['specific_impulse']
        
        def constraint_function(x):
            """Constraint function for optimization"""
            divergence_angle, length_ratio = x
            
            # Calculate nozzle geometry
            geometry = self.calculator.calculate_geometry(
                divergence_angle=divergence_angle,
                length_ratio=length_ratio,
                chamber_state=chamber_state
            )
            
            # Get constraints
            max_temp = max(s.wall_temperature for s in geometry.segments)
            max_heat = max(s.heat_flux for s in geometry.segments)
            weight = self.calculate_weight(geometry)
            
            return [
                constraints.max_divergence_angle - divergence_angle,  # g(x) >= 0
                divergence_angle - constraints.min_divergence_angle,
                constraints.max_length_ratio - length_ratio,
                length_ratio - constraints.min_length_ratio,
                constraints.max_wall_temp - max_temp,
                constraints.max_heat_flux - max_heat,
                weight - constraints.max_weight
            ]
        
        # Initial guess
        x0 = [
            (constraints.min_divergence_angle + constraints.max_divergence_angle) / 2,
            (constraints.min_length_ratio + constraints.max_length_ratio) / 2
        ]
        
        # Bounds
        bounds = [
            (constraints.min_divergence_angle, constraints.max_divergence_angle),
            (constraints.min_length_ratio, constraints.max_length_ratio)
        ]
        
        # Constraints
        cons = {'type': 'ineq', 'fun': constraint_function}
        
        # Optimize
        if method == 'differential_evolution':
            result = differential_evolution(
                objective_function,
                bounds=bounds,
                constraints=cons,
                maxiter=100,
                popsize=20,
                mutation=(0.5, 1.0),
                recombination=0.7
            )
        else:
            result = minimize(
                objective_function,
                x0=x0,
                bounds=bounds,
                constraints=cons,
                method='SLSQP',
                options={'maxiter': 100}
            )
        
        # Get optimized geometry
        optimized_geometry = self.calculator.calculate_geometry(
            divergence_angle=result.x[0],
            length_ratio=result.x[1],
            chamber_state=chamber_state
        )
        
        return {
            'geometry': optimized_geometry,
            'divergence_angle': result.x[0],
            'length_ratio': result.x[1],
            'objective_value': -result.fun,  # Convert back from negative
            'success': result.success,
            'message': result.message
        }
    
    def calculate_weight(self, geometry) -> float:
        """Calculate nozzle weight based on geometry and material"""
        # Simple weight calculation (can be enhanced with more detailed model)
        volume = 0
        for i in range(len(geometry.segments) - 1):
            s1, s2 = geometry.segments[i], geometry.segments[i + 1]
            dx = s2.start_x - s1.start_x
            r1, r2 = s1.start_radius, s2.start_radius
            volume += np.pi * dx * (r1**2 + r1*r2 + r2**2) / 3
        
        # Assume steel density (kg/m³)
        density = 7850
        return volume * density
    
    def sensitivity_analysis(self,
                           chamber_state: CombustionState,
                           constraints: OptimizationConstraints,
                           n_samples: int = 100) -> pd.DataFrame:
        """Perform sensitivity analysis of design parameters"""
        results = []
        
        for _ in range(n_samples):
            # Random sampling within constraints
            divergence_angle = np.random.uniform(
                constraints.min_divergence_angle,
                constraints.max_divergence_angle
            )
            length_ratio = np.random.uniform(
                constraints.min_length_ratio,
                constraints.max_length_ratio
            )
            
            # Calculate geometry and performance
            geometry = self.calculator.calculate_geometry(
                divergence_angle=divergence_angle,
                length_ratio=length_ratio,
                chamber_state=chamber_state
            )
            
            results.append({
                'divergence_angle': divergence_angle,
                'length_ratio': length_ratio,
                'thrust_coefficient': geometry.performance_metrics['thrust_coefficient'],
                'specific_impulse': geometry.performance_metrics['specific_impulse'],
                'efficiency': geometry.performance_metrics['efficiency'],
                'exit_mach': geometry.performance_metrics['exit_mach'],
                'weight': self.calculate_weight(geometry)
            })
        
        return pd.DataFrame(results) 