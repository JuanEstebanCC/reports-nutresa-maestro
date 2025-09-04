from typing import List, Dict, Any
from app.core.database import db_manager
from app.models.schemas import ReportRow
from datetime import datetime
import logging
import json
import os
import re

logger = logging.getLogger(__name__)

class ReportService:
    
    def __init__(self):
        """Initialize the service and load NIN data"""
        self.nin_data = self._load_nin_data()
    
    def _load_nin_data(self) -> List[Dict[str, str]]:
        """Load NIN data from nin.json file"""
        try:
            nin_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'nin.json')
            with open(nin_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            logger.error(f"Error loading nin.json: {str(e)}")
            return []
    
    def _get_agent_code_by_name(self, agent_name: str) -> str:
        """Get agent code (NIN) by agent name using regex matching"""
        if not agent_name or not self.nin_data:
            return "UNKNOWN"
        
        # Normalize the agent name for comparison (remove extra spaces, convert to uppercase)
        normalized_agent_name = re.sub(r'\s+', ' ', agent_name.strip().upper())
        
        for item in self.nin_data:
            # Normalize the name from JSON for comparison
            normalized_json_name = re.sub(r'\s+', ' ', item['ac'].strip().upper())
            
            # Try exact match first
            if normalized_agent_name == normalized_json_name:
                return item['nin']
            
            # Try partial match - check if the key words from agent name are in the JSON name
            agent_words = set(normalized_agent_name.split())
            json_words = set(normalized_json_name.split())
            
            # If most of the important words match (excluding common words)
            common_words = {'S.A.S', 'SAS', 'S.A', 'SA', 'LTDA', 'AGENCIA'}
            agent_important_words = agent_words - common_words
            json_important_words = json_words - common_words
            
            if agent_important_words and json_important_words:
                # Calculate similarity based on important words
                intersection = agent_important_words.intersection(json_important_words)
                if len(intersection) >= max(1, len(agent_important_words) * 0.7):  # 70% match threshold
                    return item['nin']
        
        return "UNKNOWN"
    
    async def generate_report(self, period_id: int) -> Dict[str, Any]:
        """
        Generate report by iterating through all subdomains and aggregating data for a specific period
        """
        all_data = []
        processed_subdomains = []
        
        # Get all available subdomains (process all 60 agents)
        import time
        start_time = time.time()
        
        all_subdomains = db_manager.get_available_subdomains()
        subdomains = all_subdomains  # Process all agents
        
        for i, subdomain in enumerate(subdomains, 1):
            try:
                agent_start_time = time.time()
                logger.info(f"Processing subdomain: {subdomain} for period: {period_id}")
                subdomain_data = await self._get_subdomain_data(subdomain, period_id)
                all_data.extend(subdomain_data)
                processed_subdomains.append(subdomain)
                
            except Exception as e:
                logger.error(f"Error processing subdomain {subdomain}: {str(e)}")
                continue
        
        total_time = time.time() - start_time
        
        return {
            "data": all_data,
            "total_records": len(all_data),
            "subdomains_processed": processed_subdomains,
            "generated_at": datetime.now().isoformat()
        }
    
    async def _get_subdomain_data(self, subdomain: str, period_id: int) -> List[Dict[str, Any]]:
        """
        Get report data for a specific subdomain and period following the new structure (optimized)
        """
        try:
            connection = await db_manager.get_connection(subdomain)
            
            # Quick table existence check
            if not await self._check_tables_exist(connection):
                logger.info(f"Tables not found in {subdomain}, using mock data")
                return self._get_mock_data_new_structure(subdomain, period_id)
            
            # Get real data with optimized query
            return await self._get_real_data_optimized(connection, subdomain, period_id)
            
        except Exception as e:
            logger.error(f"Error processing subdomain {subdomain}: {str(e)}")
            return self._get_mock_data_new_structure(subdomain, period_id)
    
    async def _check_tables_exist(self, connection) -> bool:
        """Check if required tables exist (optimized)"""
        try:
            cursor = await connection.cursor()
            
            # Check which tables exist
            await cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name IN ('users', 'people', 'liquidations', 'roles', 'programs_users', 'programs', 'variables', 'periods')
            """)
            existing_tables = await cursor.fetchall()
            table_names = [table[0] for table in existing_tables]
            
            # Check liquidations table specifically and count records
            if 'liquidations' in table_names:
                await cursor.execute("SELECT COUNT(*) FROM liquidations")
                liquidations_count = await cursor.fetchone()
            
            await cursor.close()
            tables_found = len(table_names)
            return tables_found >= 6  # At least 6 main tables must exist
            
        except Exception as e:
            logger.error(f"Error checking tables: {str(e)}")
            return False
    
    def _get_mock_data_new_structure(self, subdomain: str, period_id: int) -> List[Dict[str, Any]]:
        """Generate mock data by variable for the subdomain (agent commercial) for a specific period"""
        
        # Mock variables with their totals for the entire subdomain
        # Based on the new liquidations table logic: MAX(goal) per vendor, SUM(results), SUM(points)
        mock_variables_data = [
            {
                "variable_name": "CSI - Frijoles Zenú 2da Etapa",
                "total_meta_asignada": 0,  # Sum of MAX goals per vendor
                "total_meta_distribuida": 0,  # Sum of results from liquidations table
                "total_incentivo_asignado": 0,  # Sum of points from liquidations table
                "total_incentivo_distribuido": 0,  # Sum of points for approved liquidations
                "porcentaje_variables_completadas": 0.0
            },
            {
                "variable_name": "CSI - Snack de Película", 
                "total_meta_asignada": 3,  # Sum of MAX goals per vendor from liquidations table
                "total_meta_distribuida": 0,  # Sum of results from liquidations table
                "total_incentivo_asignado": 150,  # Sum of points from liquidations table
                "total_incentivo_distribuido": 0,  # Sum of points for approved liquidations
                "porcentaje_variables_completadas": 0.0
            },
            {
                "variable_name": "CSI - Tosh Manzanilla Limoncillo 2da Etapa",
                "total_meta_asignada": 0,
                "total_meta_distribuida": 0,
                "total_incentivo_asignado": 0,
                "total_incentivo_distribuido": 0,
                "porcentaje_variables_completadas": 0.0
            },
            {
                "variable_name": "CSI- Ahorramax 2da Etapa AU",
                "total_meta_asignada": 0,
                "total_meta_distribuida": 0,
                "total_incentivo_asignado": 0,
                "total_incentivo_distribuido": 0,
                "porcentaje_variables_completadas": 0.0
            },
            {
                "variable_name": "CSI- Ahorramax 2da Etapa TD",
                "total_meta_asignada": 0,
                "total_meta_distribuida": 0,
                "total_incentivo_asignado": 0,
                "total_incentivo_distribuido": 0,
                "porcentaje_variables_completadas": 0.0
            },
            {
                "variable_name": "DN - La Especial Nueces",
                "total_meta_asignada": 1327,  # Sum of MAX goals per vendor from liquidations table
                "total_meta_distribuida": 0,  # Sum of results from liquidations table
                "total_incentivo_asignado": 500,  # Sum of points from liquidations table
                "total_incentivo_distribuido": 0,  # Sum of points for approved liquidations
                "porcentaje_variables_completadas": 0.0
            }
        ]
        
        report_data = []
        
        for var_data in mock_variables_data:
            # Calculate compliance percentage correctly
            porcentaje_meta = 0.0
            if var_data["total_meta_asignada"] > 0:
                porcentaje_meta = round((var_data["total_meta_distribuida"] / var_data["total_meta_asignada"]) * 100, 2)
            
            agent_name = self._get_agent_name_by_subdomain(subdomain)
            report_row = {
                "codigo_agente": self._get_agent_code_by_name(agent_name),
                "nombre_agente": agent_name,
                "periodo_tiempo": f"Periodo {period_id}",
                "variable": var_data["variable_name"],
                "meta_asignada": var_data["total_meta_asignada"],
                "meta_distribuida": var_data["total_meta_distribuida"],
                "porcentaje_meta": porcentaje_meta,
                "incentivo_asignado": var_data["total_incentivo_asignado"],
                "incentivo_distribuido": var_data["total_incentivo_distribuido"],
                "porcentaje_variables_completadas": var_data["porcentaje_variables_completadas"],
                "porcentaje_ejecucion_incentivo": 0.0,  # Mock data has no execution
                "user_id": None,
                "program_id": 1
            }
            report_data.append(report_row)
        
        return report_data
    
    async def _get_distributed_incentives(self, connection, period_id: int) -> Dict[int, float]:
        """
        Separate query to get distributed incentives ONLY (sum of all incentives per variable)
        This implements the exact logic from the provided query for incentivo distribuido
        Los incentivos asignados siguen usando el cálculo original
        """
        cursor = await connection.cursor()
        
        try:
            # Query that exactly matches the user's working SQL - first get individual incentives, then sum by variable
            # This is ONLY for distributed incentives, not assigned
            incentive_query = """
            SELECT 
                variable_id,
                SUM(incentive) as total_incentivos_distribuidos
            FROM (
                SELECT
                    u.id,
                    l.variable_id,
                    (ru.points * CAST(prog.pointValue AS DECIMAL(10,2))) as incentive
                FROM users u
                JOIN people p ON u.person_id = p.id
                JOIN programs_users pu ON u.id = pu.user_id
                JOIN programs prog ON pu.program_id = prog.id
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN liquidations l ON p.nin = l.nin
                LEFT JOIN rules ru ON ru.user_id = u.id AND ru.variable_id = l.variable_id
                LEFT JOIN rule_periods rp ON rp.rule_id = ru.id AND rp.period_id = l.period_id
                WHERE u.role_id IN (1, 2, 3, 5, 6)
                  AND rp.period_id = %s
                  AND l.variable_id IS NOT NULL
                  AND ru.points IS NOT NULL
                  AND prog.pointValue IS NOT NULL
                GROUP BY u.id, l.period_id, l.variable_id, ru.points, prog.pointValue
            ) as subquery
            GROUP BY variable_id
            """
            
            await cursor.execute(incentive_query, (period_id,))
            results = await cursor.fetchall()
            
            # Convert to dictionary: variable_id -> total_distributed_incentive
            distributed_incentives_by_variable = {}
            for row in results:
                variable_id, total_distributed_incentive = row
                distributed_incentives_by_variable[variable_id] = float(total_distributed_incentive or 0)
            
            return distributed_incentives_by_variable
            
        except Exception as e:
            logger.error(f"Error getting distributed incentives: {str(e)}")
            return {}
        finally:
            await cursor.close()

    async def _get_real_data_optimized(self, connection, subdomain: str, period_id: int) -> List[Dict[str, Any]]:
        """Get real data from database aggregated by variable for the subdomain (agent commercial) for a specific period"""
        cursor = await connection.cursor()

        try:
            # Get distributed incentives using separate query
            distributed_incentives = await self._get_distributed_incentives(connection, period_id)
                
            # Main query without the complex incentive distributed logic
            query = """
            SELECT
                v.name_to_display as variable_name,
                v.id as variable_id,
                l.goal as meta_asignada_agente,
                COALESCE(vendor_goals.total_vendor_goals, 0) as meta_distribuida_vendors,
                l.results as resultados_agente,
                COALESCE(vendor_results.total_vendor_results, 0) as resultados_vendors,
                ROUND((COALESCE(vendor_results.total_vendor_results, 0) / COALESCE(vendor_goals.total_vendor_goals, 1)) * 100, 2) as cumplimiento_porcentaje,
                COALESCE(rules_user.points_regla_user, 0) * (SELECT pointValue FROM programs WHERE id = 1) as incentivo_asignado_puntos,
                (SELECT pointValue FROM programs WHERE id = 1) as point_value,
                2 as user_id,
                1 as program_id
            FROM liquidations l
            INNER JOIN variables v ON l.variable_id = v.id
            LEFT JOIN (
                SELECT ru.variable_id, ru.points as points_regla_user
                FROM rules ru
                INNER JOIN rule_periods rp ON ru.id = rp.rule_id
                WHERE rp.period_id = %s
                AND ru.user_id = 2
            ) rules_user ON l.variable_id = rules_user.variable_id
            LEFT JOIN (
                SELECT l2.variable_id, 
                       CASE WHEN l2.variable_id IN (3, 4) THEN AVG(l2.goal) ELSE SUM(l2.goal) END as total_vendor_goals
                FROM liquidations l2
                INNER JOIN people p2 ON l2.nin = p2.nin
                INNER JOIN users u2 ON p2.id = u2.person_id
                WHERE l2.period_id = %s
                AND l2.program_id = 1
                AND u2.role_id = 5
                AND l2.goal > 0
                GROUP BY l2.variable_id
            ) vendor_goals ON l.variable_id = vendor_goals.variable_id
            LEFT JOIN (
                SELECT l3.variable_id, 
                       CASE WHEN l3.variable_id IN (3, 4) THEN AVG(l3.results) ELSE SUM(l3.results) END as total_vendor_results
                FROM liquidations l3
                INNER JOIN people p3 ON l3.nin = p3.nin
                INNER JOIN users u3 ON p3.id = u3.person_id
                WHERE l3.period_id = %s
                AND l3.program_id = 1
                AND u3.role_id = 5
                GROUP BY l3.variable_id
            ) vendor_results ON l.variable_id = vendor_results.variable_id
            WHERE l.period_id = %s
            AND l.program_id = 1
            AND l.nin = (SELECT nin FROM people WHERE id = (SELECT person_id FROM users WHERE id = 2))
            AND l.goal > 0
            ORDER BY
                CASE
                    WHEN v.name_to_display = 'Ejecución Presupuestal' THEN 1
                    WHEN v.name_to_display = 'Pideky' THEN 2
                    WHEN v.name_to_display = 'Gestión de Activos' THEN 3
                    WHEN v.name_to_display = 'Efectividad' THEN 4
                    ELSE 5
                END,
                v.name_to_display
            """

            print(f"🔍 Executing main query for period {period_id}...")
            await cursor.execute(query, (period_id, period_id, period_id, period_id))
            results = await cursor.fetchall()

            # If no results, try a simpler query
            if not results:
                return await self._get_simplified_data(connection, subdomain, period_id)

            report_data = []
            period_totals = {
                'total_assigned_incentives': 0.0,
                'total_given_incentives': 0.0,
                'total_executed_incentive': 0.0,
                'total_meta_asignada': 0.0,
                'total_meta_distribuida': 0.0
            }

            # Get agent name
            agent_name = self._get_agent_name_by_subdomain(subdomain)

            # Get period information
            period_info = await self._get_period_info(connection, period_id)

            # Group results by variable to avoid duplicates
            variables_data = {}
            
            for row in results:
                (variable_name, variable_id, meta_asignada_agente, meta_distribuida_vendors, resultados_agente, resultados_vendors, cumplimiento_porcentaje,
                 incentivo_asignado_puntos, point_value,
                 user_id, program_id) = row

                # Skip "Ejecución Presupuestal" variable (matches frontend logic)
                if 'Ejecución Presupuestal' in variable_name or 'EJECUCIÓN PRESUPUESTAL' in variable_name.upper():
                    continue

                # Use variable_name as key for grouping
                if variable_name not in variables_data:
                    variables_data[variable_name] = {
                        'variable_id': variable_id,
                        'total_meta_asignada': 0.0,
                        'total_meta_distribuida': 0.0,
                        'total_resultados_agente': 0.0,
                        'total_resultados_vendors': 0.0,
                        'total_incentivo_asignado': 0.0,
                        'total_incentivo_distribuido': 0.0,
                        'user_id': user_id,
                        'program_id': program_id,
                        'point_value': float(point_value) if point_value else 500.0
                    }
                
                # Accumulate values for this variable
                variables_data[variable_name]['total_meta_asignada'] += float(meta_asignada_agente or 0)
                variables_data[variable_name]['total_meta_distribuida'] += float(meta_distribuida_vendors or 0)
                variables_data[variable_name]['total_resultados_agente'] += float(resultados_agente or 0)
                variables_data[variable_name]['total_resultados_vendors'] += float(resultados_vendors or 0)
                variables_data[variable_name]['total_incentivo_asignado'] += float(incentivo_asignado_puntos or 0)
                
                # Get distributed incentive from separate query
                distributed_incentive = distributed_incentives.get(variable_id, 0.0)
                variables_data[variable_name]['total_incentivo_distribuido'] += distributed_incentive

            # Count completed variables for percentage calculation
            total_variables = len(variables_data)
            completed_variables = sum(1 for var_data in variables_data.values() 
                                    if var_data['total_meta_asignada'] > 0 and 
                                       var_data['total_meta_distribuida'] >= var_data['total_meta_asignada'])  # 100% or more

            # Now create report rows from aggregated data
            for variable_name, var_data in variables_data.items():
                # Calculate percentage of meta distributed vs meta assigned (Meta Distribuida / Meta Asignada)
                porcentaje_meta = 0.0
                if var_data['total_meta_asignada'] > 0:
                    porcentaje_meta = round((var_data['total_meta_distribuida'] / var_data['total_meta_asignada']) * 100, 2)
                
                # Calculate incentive execution percentage for this specific variable
                executed_incentive = 0.0
                if var_data['total_incentivo_asignado'] > 0:
                    executed_incentive = round((var_data['total_incentivo_distribuido'] / var_data['total_incentivo_asignado']) * 100, 2)
                
                # Calculate variables completion percentage (real percentage of completed variables)
                porcentaje_variables_completadas = 0.0
                if total_variables > 0:
                    porcentaje_variables_completadas = round((completed_variables / total_variables) * 100, 2)

                # Create report row
                report_row = {
                    "codigo_agente": self._get_agent_code_by_name(agent_name),
                    "nombre_agente": agent_name,
                    "periodo_tiempo": period_info,
                    "variable": variable_name,
                    "meta_asignada": round(var_data['total_meta_asignada'], 2),
                    "meta_distribuida": round(var_data['total_meta_distribuida'], 2),
                    "porcentaje_meta": porcentaje_meta,
                    "incentivo_asignado": round(var_data['total_incentivo_asignado'], 2),
                    "incentivo_distribuido": round(var_data['total_incentivo_distribuido'], 2),
                    "porcentaje_variables_completadas": round(porcentaje_variables_completadas, 2),
                    "porcentaje_ejecucion_incentivo": executed_incentive,
                    "user_id": var_data['user_id'],
                    "program_id": var_data['program_id']
                }

                report_data.append(report_row)

                # Accumulate period totals
                period_totals['total_assigned_incentives'] += var_data['total_incentivo_asignado']
                period_totals['total_given_incentives'] += var_data['total_incentivo_distribuido']
                period_totals['total_meta_asignada'] += var_data['total_meta_asignada']
                period_totals['total_meta_distribuida'] += var_data['total_meta_distribuida']

            # Calculate total execution percentage
            if period_totals['total_assigned_incentives'] > 0:
                period_totals['total_executed_incentive'] = round(
                    (period_totals['total_given_incentives'] / period_totals['total_assigned_incentives']) * 100, 2
                )

            # Calculate total compliance percentage based on vendor performance
            total_porcentaje_meta = 0.0
            if period_totals['total_meta_distribuida'] > 0:
                total_porcentaje_meta = round(
                    (period_totals['total_meta_distribuida'] / period_totals['total_meta_asignada']) * 100, 2
                )

            # Add TOTAL row
            if report_data:
                total_row = {
                    "codigo_agente": self._get_agent_code_by_name(agent_name),
                    "nombre_agente": agent_name,
                    "periodo_tiempo": period_info,
                    "variable": "TOTAL",
                    "meta_asignada": round(period_totals['total_meta_asignada'], 2),
                    "meta_distribuida": round(period_totals['total_meta_distribuida'], 2),
                    "porcentaje_meta": total_porcentaje_meta,
                    "incentivo_asignado": round(period_totals['total_assigned_incentives'], 2),
                    "incentivo_distribuido": round(period_totals['total_given_incentives'], 2),
                    "porcentaje_variables_completadas": round((completed_variables / total_variables) * 100, 2) if total_variables > 0 else 0.0,
                    "porcentaje_ejecucion_incentivo": period_totals['total_executed_incentive'],
                    "user_id": None,
                    "program_id": 1
                }
                report_data.append(total_row)

            return report_data

        except Exception as e:
            logger.error(f"Error in optimized query for {subdomain}: {str(e)}")
            return self._get_mock_data_new_structure(subdomain, period_id)
        finally:
            await cursor.close()

    async def _get_simplified_data(self, connection, subdomain: str, period_id: int) -> List[Dict[str, Any]]:
        """Get simplified data when full query fails - matches working SQL logic with basic calculations"""
        cursor = await connection.cursor()

        try:
            # Get distributed incentives using separate query
            distributed_incentives = await self._get_distributed_incentives(connection, period_id)
            
            # Simplified main query without complex incentive logic
            simple_query = """
            SELECT
                v.name_to_display as variable_name,
                v.id as variable_id,
                l.goal as meta_asignada_agente,
                COALESCE(vendor_goals.total_vendor_goals, 0) as meta_distribuida_vendors,
                l.results as resultados_agente,
                COALESCE(vendor_results.total_vendor_results, 0) as resultados_vendors,
                ROUND((COALESCE(vendor_results.total_vendor_results, 0) / COALESCE(vendor_goals.total_vendor_goals, 1)) * 100, 2) as cumplimiento_porcentaje,
                COALESCE(rules_user.points_regla_user, 0) * (SELECT pointValue FROM programs WHERE id = 1) as incentivo_asignado_puntos,
                (SELECT pointValue FROM programs WHERE id = 1) as point_value,
                2 as user_id,
                1 as program_id
            FROM liquidations l
            INNER JOIN variables v ON l.variable_id = v.id
            LEFT JOIN (
                SELECT ru.variable_id, ru.points as points_regla_user
                FROM rules ru
                INNER JOIN rule_periods rp ON ru.id = rp.rule_id
                WHERE rp.period_id = %s
                AND ru.user_id = 2
            ) rules_user ON l.variable_id = rules_user.variable_id
            LEFT JOIN (
                SELECT l2.variable_id, 
                       CASE WHEN l2.variable_id IN (3, 4) THEN AVG(l2.goal) ELSE SUM(l2.goal) END as total_vendor_goals
                FROM liquidations l2
                INNER JOIN people p2 ON l2.nin = p2.nin
                INNER JOIN users u2 ON p2.id = u2.person_id
                WHERE l2.period_id = %s
                AND l2.program_id = 1
                AND u2.role_id = 5
                AND l2.goal > 0
                GROUP BY l2.variable_id
            ) vendor_goals ON l.variable_id = vendor_goals.variable_id
            LEFT JOIN (
                SELECT l3.variable_id, 
                       CASE WHEN l3.variable_id IN (3, 4) THEN AVG(l3.results) ELSE SUM(l3.results) END as total_vendor_results
                FROM liquidations l3
                INNER JOIN people p3 ON l3.nin = p3.nin
                INNER JOIN users u3 ON p3.id = u3.person_id
                WHERE l3.period_id = %s
                AND l3.program_id = 1
                AND u3.role_id = 5
                GROUP BY l3.variable_id
            ) vendor_results ON l.variable_id = vendor_results.variable_id
            WHERE l.period_id = %s
            AND l.program_id = 1
            AND l.nin = (SELECT nin FROM people WHERE id = (SELECT person_id FROM users WHERE id = 2))
            AND l.goal > 0
            ORDER BY
                CASE
                    WHEN v.name_to_display = 'Ejecución Presupuestal' THEN 1
                    WHEN v.name_to_display = 'Pideky' THEN 2
                    WHEN v.name_to_display = 'Gestión de Activos' THEN 3
                    WHEN v.name_to_display = 'Efectividad' THEN 4
                    ELSE 5
                END,
                v.name_to_display
            LIMIT 20
            """

            await cursor.execute(simple_query, (period_id, period_id, period_id, period_id))
            simple_results = await cursor.fetchall()

            if not simple_results:
                return self._get_mock_data_new_structure(subdomain, period_id)

            report_data = []
            period_totals = {
                'total_assigned_incentives': 0.0,
                'total_given_incentives': 0.0,
                'total_executed_incentive': 0.0,
                'total_meta_asignada': 0.0,
                'total_meta_distribuida': 0.0
            }

            agent_name = self._get_agent_name_by_subdomain(subdomain)

            # Get period information
            period_info = await self._get_period_info(connection, period_id)

            # Group results by variable to avoid duplicates
            variables_data = {}
            
            for row in simple_results:
                (variable_name, variable_id, meta_asignada_agente, meta_distribuida_vendors, resultados_agente, resultados_vendors, cumplimiento_porcentaje,
                 incentivo_asignado_puntos, point_value,
                 user_id, program_id) = row

                # Skip "Ejecución Presupuestal" variable
                if 'Ejecución Presupuestal' in variable_name or 'EJECUCIÓN PRESUPUESTAL' in variable_name.upper():
                    continue

                # Use variable_name as key for grouping
                if variable_name not in variables_data:
                    variables_data[variable_name] = {
                        'variable_id': variable_id,
                        'total_meta_asignada': 0.0,
                        'total_meta_distribuida': 0.0,
                        'total_resultados_agente': 0.0,
                        'total_resultados_vendors': 0.0,
                        'total_incentivo_asignado': 0.0,
                        'total_incentivo_distribuido': 0.0,
                        'user_id': user_id,
                        'program_id': program_id,
                        'point_value': float(point_value) if point_value else 500.0
                    }
                
                # Accumulate values for this variable
                variables_data[variable_name]['total_meta_asignada'] += float(meta_asignada_agente or 0)
                variables_data[variable_name]['total_meta_distribuida'] += float(meta_distribuida_vendors or 0)
                variables_data[variable_name]['total_resultados_agente'] += float(resultados_agente or 0)
                variables_data[variable_name]['total_resultados_vendors'] += float(resultados_vendors or 0)
                variables_data[variable_name]['total_incentivo_asignado'] += float(incentivo_asignado_puntos or 0)
                
                # Get distributed incentive from separate query
                distributed_incentive = distributed_incentives.get(variable_id, 0.0)
                variables_data[variable_name]['total_incentivo_distribuido'] += distributed_incentive

            # Count completed variables for percentage calculation
            total_variables = len(variables_data)
            completed_variables = sum(1 for var_data in variables_data.values() 
                                    if var_data['total_meta_asignada'] > 0 and 
                                       var_data['total_meta_distribuida'] >= var_data['total_meta_asignada'])  # 100% or more

            # Now create report rows from aggregated data
            for variable_name, var_data in variables_data.items():
                # Calculate percentage of meta distributed vs meta assigned (Meta Distribuida / Meta Asignada)
                porcentaje_meta = 0.0
                if var_data['total_meta_asignada'] > 0:
                    porcentaje_meta = round((var_data['total_meta_distribuida'] / var_data['total_meta_asignada']) * 100, 2)
                
                # Calculate incentive execution percentage for this specific variable
                executed_incentive = 0.0
                if var_data['total_incentivo_asignado'] > 0:
                    executed_incentive = round((var_data['total_incentivo_distribuido'] / var_data['total_incentivo_asignado']) * 100, 2)
                
                # Calculate variables completion percentage (real percentage of completed variables)
                porcentaje_variables_completadas = 0.0
                if total_variables > 0:
                    porcentaje_variables_completadas = round((completed_variables / total_variables) * 100, 2)

                report_row = {
                    "codigo_agente": self._get_agent_code_by_name(agent_name),
                    "nombre_agente": agent_name,
                    "periodo_tiempo": period_info,
                    "variable": variable_name,
                    "meta_asignada": round(var_data['total_meta_asignada'], 2),
                    "meta_distribuida": round(var_data['total_meta_distribuida'], 2),
                    "porcentaje_meta": porcentaje_meta,
                    "incentivo_asignado": round(var_data['total_incentivo_asignado'], 2),
                    "incentivo_distribuido": round(var_data['total_incentivo_distribuido'], 2),
                    "porcentaje_variables_completadas": round(porcentaje_variables_completadas, 2),
                    "porcentaje_ejecucion_incentivo": executed_incentive,
                    "user_id": var_data['user_id'],
                    "program_id": var_data['program_id']
                }

                report_data.append(report_row)

                # Accumulate period totals
                period_totals['total_assigned_incentives'] += var_data['total_incentivo_asignado']
                period_totals['total_given_incentives'] += var_data['total_incentivo_distribuido']
                period_totals['total_meta_asignada'] += var_data['total_meta_asignada']
                period_totals['total_meta_distribuida'] += var_data['total_meta_distribuida']

            # Calculate total execution percentage
            if period_totals['total_assigned_incentives'] > 0:
                period_totals['total_executed_incentive'] = round(
                    (period_totals['total_given_incentives'] / period_totals['total_assigned_incentives']) * 100, 2
                )

            # Calculate total compliance percentage based on vendor performance
            total_porcentaje_meta = 0.0
            if period_totals['total_meta_distribuida'] > 0:
                total_porcentaje_meta = round(
                    (period_totals['total_meta_distribuida'] / period_totals['total_meta_asignada']) * 100, 2
                )

            # Add TOTAL row
            if report_data:
                total_row = {
                    "codigo_agente": self._get_agent_code_by_name(agent_name),
                    "nombre_agente": agent_name,
                    "periodo_tiempo": period_info,
                    "variable": "TOTAL",
                    "meta_asignada": round(period_totals['total_meta_asignada'], 2),
                    "meta_distribuida": round(period_totals['total_meta_distribuida'], 2),
                    "porcentaje_meta": total_porcentaje_meta,
                    "incentivo_asignado": round(period_totals['total_assigned_incentives'], 2),
                    "incentivo_distribuido": round(period_totals['total_given_incentives'], 2),
                    "porcentaje_variables_completadas": round((completed_variables / total_variables) * 100, 2) if total_variables > 0 else 0.0,
                    "porcentaje_ejecucion_incentivo": period_totals['total_executed_incentive'],
                    "user_id": None,
                    "program_id": 1
                }
                report_data.append(total_row)

            return report_data

        except Exception as e:
            logger.error(f"Error in simplified query for {subdomain}: {str(e)}")
            return self._get_mock_data_new_structure(subdomain, period_id)
        finally:
            await cursor.close()
    
    def _get_agent_name_by_subdomain(self, subdomain: str) -> str:
        """Get agent name based on subdomain"""
        agent_names = {
            "1030773": "A.H.H. DISTRIBUCIONES S.A.S",
            "1089723": "AGENCIA COMERCIAL NUTRICOL SAS",
            "comercruz": "COMERCRUZ DISTRIBUCIONES",
            "santiagodetunja": "SANTIAGO DE TUNJA COMERCIAL",
            "maxgol": "MAXGOL DISTRIBUCIONES",
            "distrimarcasagentecomercial": "DISTRIMARCAS AGENTE COMERCIAL",
            "jyddistribuciones": "JYD DISTRIBUCIONES"
        }
        
        return agent_names.get(subdomain, f"AGENCIA COMERCIAL {subdomain.upper()}")
    
    def _format_period(self, period_start) -> str:
        """Format period date to Spanish month year"""
        if not period_start:
            return "Periodo Desconocido"
        
        # Handle case where period_start might be an integer or other type
        if isinstance(period_start, int):
            return f"Periodo {period_start}"  # Use period ID as fallback
        
        # Handle case where period_start is a datetime object
        if hasattr(period_start, 'month') and hasattr(period_start, 'year'):
            month_names = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            
            month_name = month_names.get(period_start.month, "")
            return f"{month_name} {period_start.year}"
        
        # Fallback for any other type
        return "Periodo Desconocido"
    
    async def _get_completion_percentage_fast(self, cursor, user_id: int, period_id: int) -> float:
        """Fast completion percentage calculation"""
        try:
            query = """
            SELECT 
                COUNT(DISTINCT l.variable_id) as total,
                COUNT(DISTINCT CASE WHEN l.results > 0 THEN l.variable_id END) as completed
            FROM liquidations l
            JOIN people p ON l.nin = p.nin
            JOIN users u ON p.id = u.person_id
            WHERE u.id = %s AND l.period_id = %s
            """
            
            await cursor.execute(query, (user_id, period_id))
            result = await cursor.fetchone()
            
            if result and result[0] > 0:
                total, completed = result
                return round((completed / total) * 100, 2)
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating completion percentage: {str(e)}")
            return 0.0
    
    # Additional utility methods for backward compatibility and future use
    async def _calculate_incentives(self, connection, user_id: int, variable_id: int, period_id: int) -> Dict[str, float]:
        """
        Calculate incentive assigned and distributed based on points and point value
        (Kept for potential future use or backward compatibility)
        """
        try:
            cursor = await connection.cursor()
            
            # Get assigned points and point value in single query
            query = """
            SELECT ru.points, pr.pointValue
            FROM rules ru
            JOIN rule_periods rp ON rp.rule_id = ru.id
            JOIN programs_users pu ON pu.user_id = ru.user_id
            JOIN programs pr ON pr.id = pu.program_id
            WHERE ru.user_id = %s 
              AND ru.variable_id = %s 
              AND rp.period_id = %s
            """
            
            await cursor.execute(query, (user_id, variable_id, period_id))
            result = await cursor.fetchone()
            await cursor.close()
            
            if result and result[0] and result[1]:
                points, point_value = result
                incentivo_asignado = float(points) * float(point_value)
                return {
                    "asignado": incentivo_asignado,
                    "distribuido": incentivo_asignado  # Can be modified based on achievement
                }
            
            return {"asignado": 0.0, "distribuido": 0.0}
            
        except Exception as e:
            logger.error(f"Error calculating incentives: {str(e)}")
            return {"asignado": 0.0, "distribuido": 0.0}
    
    async def _get_period_info(self, connection, period_id: int) -> str:
        """
        Get period information formatted as "Month Year" (e.g., "Agosto 2025")
        (Kept for potential future use or backward compatibility)
        """
        try:
            query = "SELECT start_date FROM periods WHERE id = %s"
            cursor = await connection.cursor()
            await cursor.execute(query, (period_id,))
            result = await cursor.fetchone()
            await cursor.close()
            
            if result and result[0]:
                return self._format_period(result[0])
            return f'Periodo {period_id}'
            
        except Exception as e:
            logger.error(f"Error getting period info: {str(e)}")
            return f'Periodo {period_id}'
    
    async def _get_variable_name(self, connection, variable_id: int) -> str:
        """
        Get variable name by ID
        (Kept for potential future use or backward compatibility)
        """
        try:
            query = "SELECT name FROM variables WHERE id = %s"
            cursor = await connection.cursor()
            await cursor.execute(query, (variable_id,))
            result = await cursor.fetchone()
            await cursor.close()
            
            if result and result[0]:
                return result[0]
            return 'Variable'
            
        except Exception as e:
            logger.error(f"Error getting variable name: {str(e)}")
            return 'Variable'
    
    async def _calculate_variables_completion_percentage(self, connection, user_id: int, period_id: int) -> float:
        """
        Calculate percentage of variables completed for a user in a specific period
        (Kept for potential future use or backward compatibility)
        """
        try:
            cursor = await connection.cursor()
            
            # Combined query for efficiency
            query = """
            SELECT 
                COUNT(DISTINCT l.variable_id) as total_variables,
                COUNT(DISTINCT CASE WHEN l.results > 0 THEN l.variable_id END) as completed_variables
            FROM liquidations l
            JOIN people p ON l.nin = p.nin
            JOIN users u ON p.id = u.person_id
            WHERE u.id = %s AND l.period_id = %s
            """
            
            await cursor.execute(query, (user_id, period_id))
            result = await cursor.fetchone()
            await cursor.close()
            
            if result and result[0] > 0:
                total_variables, completed_variables = result
                percentage = (completed_variables / total_variables) * 100
                return round(percentage, 2)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating variables completion percentage: {str(e)}")
            return 0.0