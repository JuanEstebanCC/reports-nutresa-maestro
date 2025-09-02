from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReportRow(BaseModel):
    codigo_agente: str  # Agent code (subdomain)
    nombre_agente: str  # Agent commercial name
    periodo_tiempo: str  # Time period (e.g., "Agosto 2025")
    variable: str  # Variable name
    meta_asignada: Optional[float] = None  # Assigned goal
    meta_distribuida: Optional[float] = None  # Distributed goal
    porcentaje_meta: Optional[float] = None  # Goal percentage
    incentivo_asignado: Optional[float] = None  # Assigned incentive
    incentivo_distribuido: Optional[float] = None  # Distributed incentive
    porcentaje_variables_completadas: Optional[float] = None  # Variables completion percentage
    porcentaje_ejecucion_incentivo: Optional[float] = None  # Incentive execution percentage (PHP logic)
    user_id: Optional[int] = None  # User ID (for frontend compatibility)
    program_id: Optional[int] = None  # Program ID (for frontend compatibility)

class ReportResponse(BaseModel):
    data: List[Dict[str, Any]]
    total_records: int
    subdomains_processed: List[str]
    generated_at: str

class SubdomainConfig(BaseModel):
    subdomain: str
    database_name: str
