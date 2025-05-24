import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import pint
from dataclasses import asdict, dataclass
import pandas as pd
from pathlib import Path

from .engineering_calculations import NozzleGeometryCalculator, NozzleSegment
from .combustion import CombustionState

# Initialize unit registry
ureg = pint.UnitRegistry()

@dataclass
class DesignSession:
    """Represents a complete nozzle design session"""
    id: Optional[int] = None
    name: str = ""
    created_at: datetime = None
    modified_at: datetime = None
    propellant_type: str = ""
    chamber_pressure: float = 0.0  # Pa
    chamber_temperature: float = 0.0  # K
    fuel_ratio: float = 0.0
    thrust: float = 0.0  # N
    material: str = ""
    optimization_type: str = ""
    target_value: float = 0.0
    segments: List[NozzleSegment] = None
    performance_metrics: Dict[str, float] = None
    chamber_state: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()
        if self.segments is None:
            self.segments = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.chamber_state is None:
            self.chamber_state = {}
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for storage"""
        data = asdict(self)
        # Convert datetime objects to strings
        data['created_at'] = data['created_at'].isoformat()
        data['modified_at'] = data['modified_at'].isoformat()
        # Convert segments to dictionaries
        data['segments'] = [asdict(s) for s in self.segments]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DesignSession':
        """Create session from dictionary"""
        # Convert datetime strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        # Convert segment dictionaries back to NozzleSegment objects
        data['segments'] = [NozzleSegment(**s) for s in data['segments']]
        return cls(**data)

class SessionManager:
    """Manages design sessions and data persistence"""
    
    def __init__(self, db_path: str = "nozzle_designs.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS design_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
    
    def save_session(self, session: DesignSession) -> int:
        """Save a design session to the database"""
        session.modified_at = datetime.now()
        data = session.to_dict()
        
        with sqlite3.connect(self.db_path) as conn:
            if session.id is None:
                # New session
                cursor = conn.execute(
                    "INSERT INTO design_sessions (name, created_at, modified_at, data) VALUES (?, ?, ?, ?)",
                    (session.name, session.created_at.isoformat(), session.modified_at.isoformat(), json.dumps(data))
                )
                session.id = cursor.lastrowid
            else:
                # Update existing session
                conn.execute(
                    "UPDATE design_sessions SET name = ?, modified_at = ?, data = ? WHERE id = ?",
                    (session.name, session.modified_at.isoformat(), json.dumps(data), session.id)
                )
        
        return session.id
    
    def load_session(self, session_id: int) -> DesignSession:
        """Load a design session from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM design_sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Session {session_id} not found")
            
            data = json.loads(row[0])
            return DesignSession.from_dict(data)
    
    def list_sessions(self) -> List[Dict]:
        """List all saved sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, name, created_at, modified_at FROM design_sessions ORDER BY modified_at DESC"
            )
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'created_at': datetime.fromisoformat(row[2]),
                    'modified_at': datetime.fromisoformat(row[3])
                }
                for row in cursor.fetchall()
            ]
    
    def delete_session(self, session_id: int):
        """Delete a design session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM design_sessions WHERE id = ?", (session_id,))
    
    def export_report(self, session: DesignSession, output_path: str):
        """Export a complete design report"""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export session data
        with open(output_path / "session_data.json", 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        
        # Export segments to Excel
        segment_data = pd.DataFrame([
            {
                'Position (m)': s.start_x,
                'Radius (m)': s.start_radius,
                'Mach Number': s.mach_number,
                'Pressure (Pa)': s.pressure,
                'Temperature (K)': s.temperature,
                'Wall Temperature (K)': s.wall_temperature,
                'Heat Flux (W/m²)': s.heat_flux
            }
            for s in session.segments
        ])
        
        # Export performance metrics
        metrics_data = pd.DataFrame([session.performance_metrics])
        
        # Save to Excel with multiple sheets
        with pd.ExcelWriter(output_path / "design_report.xlsx") as writer:
            segment_data.to_excel(writer, sheet_name='Segments', index=False)
            metrics_data.to_excel(writer, sheet_name='Performance', index=False)
            
            # Add chamber state
            chamber_data = pd.DataFrame([session.chamber_state])
            chamber_data.to_excel(writer, sheet_name='Chamber State', index=False)
        
        # Generate HTML report
        self._generate_html_report(session, output_path / "design_report.html")
    
    def _generate_html_report(self, session: DesignSession, output_path: Path):
        """Generate an HTML report with all design information"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Nozzle Design Report - {session.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .section {{ margin: 20px 0; }}
                h1, h2 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>Nozzle Design Report</h1>
            <div class="section">
                <h2>Design Information</h2>
                <table>
                    <tr><th>Property</th><th>Value</th></tr>
                    <tr><td>Name</td><td>{session.name}</td></tr>
                    <tr><td>Created</td><td>{session.created_at}</td></tr>
                    <tr><td>Modified</td><td>{session.modified_at}</td></tr>
                    <tr><td>Propellant</td><td>{session.propellant_type}</td></tr>
                    <tr><td>Material</td><td>{session.material}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Chamber Conditions</h2>
                <table>
                    <tr><th>Property</th><th>Value</th></tr>
                    <tr><td>Pressure</td><td>{session.chamber_pressure/1e6:.2f} MPa</td></tr>
                    <tr><td>Temperature</td><td>{session.chamber_temperature:.0f} K</td></tr>
                    <tr><td>Fuel Ratio</td><td>{session.fuel_ratio:.2f}</td></tr>
                    <tr><td>Thrust</td><td>{session.thrust/1000:.1f} kN</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Performance Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    {self._format_metrics_table(session.performance_metrics)}
                </table>
            </div>
            
            <div class="section">
                <h2>Nozzle Segments</h2>
                <table>
                    <tr>
                        <th>Position (m)</th>
                        <th>Radius (m)</th>
                        <th>Mach</th>
                        <th>Pressure (Pa)</th>
                        <th>Temperature (K)</th>
                        <th>Wall Temp (K)</th>
                        <th>Heat Flux (W/m²)</th>
                    </tr>
                    {self._format_segments_table(session.segments)}
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _format_metrics_table(self, metrics: Dict[str, float]) -> str:
        """Format performance metrics for HTML table"""
        rows = []
        for key, value in metrics.items():
            if 'temperature' in key.lower():
                formatted = f"{value:.0f} K"
            elif 'pressure' in key.lower():
                formatted = f"{value/1e6:.2f} MPa"
            elif 'heat_flux' in key.lower():
                formatted = f"{value/1e6:.1f} MW/m²"
            elif 'efficiency' in key.lower():
                formatted = f"{value*100:.1f}%"
            else:
                formatted = f"{value:.3f}"
            rows.append(f"<tr><td>{key}</td><td>{formatted}</td></tr>")
        return "\n".join(rows)
    
    def _format_segments_table(self, segments: List[NozzleSegment]) -> str:
        """Format segments for HTML table"""
        rows = []
        for s in segments:
            rows.append(f"""
                <tr>
                    <td>{s.start_x:.3f}</td>
                    <td>{s.start_radius:.3f}</td>
                    <td>{s.mach_number:.2f}</td>
                    <td>{s.pressure:.0f}</td>
                    <td>{s.temperature:.0f}</td>
                    <td>{s.wall_temperature:.0f}</td>
                    <td>{s.heat_flux:.0f}</td>
                </tr>
            """)
        return "\n".join(rows)

class UnitConverter:
    """Handles unit conversions using pint"""
    
    @staticmethod
    def convert(value: float, from_unit: str, to_unit: str) -> float:
        """Convert a value from one unit to another"""
        quantity = value * ureg(from_unit)
        return quantity.to(to_unit).magnitude
    
    @staticmethod
    def format_value(value: float, unit: str, precision: int = 3) -> str:
        """Format a value with its unit"""
        return f"{value:.{precision}f} {unit}"
    
    @staticmethod
    def parse_value(value_str: str) -> tuple:
        """Parse a string containing a value and unit"""
        quantity = ureg(value_str)
        return quantity.magnitude, str(quantity.units) 