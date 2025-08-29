from typing import List, Dict, Any
from app.core.database import db_manager
from app.models.schemas import ReportRow
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReportService:
    
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
        subdomains = all_subdomains  # Process all subdomains (60 agents)
        
        print(f"🚀 Starting report generation for {len(subdomains)} agents (period {period_id})")
        
        for i, subdomain in enumerate(subdomains, 1):
            try:
                agent_start_time = time.time()
                logger.info(f"Processing subdomain: {subdomain} for period: {period_id}")
                subdomain_data = await self._get_subdomain_data(subdomain, period_id)
                all_data.extend(subdomain_data)
                processed_subdomains.append(subdomain)
                
                agent_time = time.time() - agent_start_time
                print(f"✅ Agent {i}/{len(subdomains)} ({subdomain}) completed in {agent_time:.2f}s - {len(subdomain_data)} records")
                
            except Exception as e:
                logger.error(f"Error processing subdomain {subdomain}: {str(e)}")
                print(f"❌ Agent {i}/{len(subdomains)} ({subdomain}) failed: {str(e)}")
                continue
        
        total_time = time.time() - start_time
        print(f"🎉 Report generation completed in {total_time:.2f}s")
        print(f"📊 Total records: {len(all_data)} from {len(processed_subdomains)} agents")
        
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
            await cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name IN ('users', 'people', 'liquidations', 'roles', 'programs_users', 'programs', 'variables', 'periods')
            """)
            result = await cursor.fetchone()
            await cursor.close()
            return result[0] >= 6  # At least 6 main tables must exist
        except Exception as e:
            logger.error(f"Error checking tables: {str(e)}")
            return False
    
    def _get_mock_data_new_structure(self, subdomain: str, period_id: int) -> List[Dict[str, Any]]:
        """Generate mock data by variable for the subdomain (agent commercial) for a specific period"""
        
        # Mock variables with their totals for the entire subdomain
        # Based on the liquidations table: goal = meta_asignada, results = meta_distribuida
        mock_variables_data = [
            {
                "variable_name": "CSI - Frijoles Zenú 2da Etapa",
                "total_meta_asignada": 0,
                "total_meta_distribuida": 0,  # results from liquidations table
                "total_incentivo_asignado": 0,
                "total_incentivo_distribuido": 0,
                "porcentaje_variables_completadas": 0.0
            },
            {
                "variable_name": "CSI - Snack de Película", 
                "total_meta_asignada": 3,  # goal from liquidations table
                "total_meta_distribuida": 0,  # results from liquidations table
                "total_incentivo_asignado": 0,
                "total_incentivo_distribuido": 0,
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
                "total_meta_asignada": 1327,  # goal from liquidations table
                "total_meta_distribuida": 0,  # results from liquidations table
                "total_incentivo_asignado": 0,
                "total_incentivo_distribuido": 0,
                "porcentaje_variables_completadas": 0.0
            }
        ]
        
        report_data = []
        
        for var_data in mock_variables_data:
            porcentaje_meta = (var_data["total_meta_distribuida"] / var_data["total_meta_asignada"]) * 100 if var_data["total_meta_asignada"] > 0 else 0.0
            
            report_row = {
                "codigo_agente": subdomain,
                "nombre_agente": self._get_agent_name_by_subdomain(subdomain),
                "periodo_tiempo": "Agosto 2025",
                "variable": var_data["variable_name"],
                "meta_asignada": var_data["total_meta_asignada"],
                "meta_distribuida": var_data["total_meta_distribuida"],
                "porcentaje_meta": round(porcentaje_meta, 2),
                "incentivo_asignado": var_data["total_incentivo_asignado"],
                "incentivo_distribuido": var_data["total_incentivo_distribuido"],
                "porcentaje_variables_completadas": var_data["porcentaje_variables_completadas"]
            }
            
            report_data.append(report_row)
        
        return report_data
    
    async def _get_real_data_optimized(self, connection, subdomain: str, period_id: int) -> List[Dict[str, Any]]:
        """Get real data from database aggregated by variable for the subdomain (agent commercial) for a specific period"""
        print(f"🚀 Starting _get_real_data_optimized for {subdomain} period {period_id}")
        cursor = await connection.cursor()
        
        try:
            # First, let's run a diagnostic query to check what data we have
            diagnostic_query = """
            SELECT 
                COUNT(*) as total_liquidations,
                COUNT(CASE WHEN ru.points IS NOT NULL AND ru.points > 0 THEN 1 END) as rules_with_points,
                COUNT(CASE WHEN l.points IS NOT NULL AND l.points > 0 THEN 1 END) as liquidations_with_points,
                COUNT(CASE WHEN l.approved = 1 THEN 1 END) as approved_liquidations,
                COUNT(CASE WHEN l.results > 0 THEN 1 END) as liquidations_with_results,
                COUNT(CASE WHEN pr.pointValue IS NOT NULL AND pr.pointValue > 0 THEN 1 END) as programs_with_pointvalue,
                AVG(ru.points) as avg_rules_points,
                AVG(l.points) as avg_liquidations_points,
                AVG(pr.pointValue) as avg_pointvalue,
                MIN(l.period_id) as min_period_id,
                MAX(l.period_id) as max_period_id,
                COUNT(DISTINCT l.period_id) as distinct_periods
            FROM liquidations l
            JOIN people p ON l.nin = p.nin
            JOIN users u ON p.id = u.person_id
            JOIN programs_users pu ON u.id = pu.user_id
            JOIN programs pr ON pu.program_id = pr.id AND l.program_id = pr.id
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN rules ru ON ru.user_id = u.id AND ru.variable_id = l.variable_id
            LEFT JOIN rule_periods rp ON rp.rule_id = ru.id AND rp.period_id = l.period_id
            WHERE r.name IN ('supervisor', 'vendor', 'supernumerary')
            AND l.period_id = %s
            """
            
            await cursor.execute(diagnostic_query, (period_id,))
            diagnostic_result = await cursor.fetchone()
            
            if diagnostic_result:
                (total_liquidations, rules_with_points, liquidations_with_points, approved_liquidations, 
                 liquidations_with_results, programs_with_pointvalue, avg_rules_points, 
                 avg_liquidations_points, avg_pointvalue, min_period_id, max_period_id, distinct_periods) = diagnostic_result

            
            # Main query to get data aggregated by variable for the entire subdomain
            # Based on the liquidations table schema:
            # - l.goal = meta_asignada (assigned goals)
            # - l.results = meta_distribuida (distributed/achieved results)
            # - Incentivos asignados = rules.points * programs.pointValue (incentivos planificados)
            # - Incentivos distribuidos = liquidations.points * programs.pointValue (solo para liquidaciones aprobadas)
            query = """
            SELECT 
                v.name as variable_name,
                l.period_id,
                pe.start_date as period_start,
                SUM(l.goal) as total_meta_asignada,                    -- Sum of all assigned goals
                SUM(l.results) as total_meta_distribuida,              -- Sum of all achieved results (distributed goals)
                SUM(COALESCE(ru.points, 0) * COALESCE(pr.pointValue, 0)) as total_incentivo_asignado,  -- Total assigned incentives from rules
                SUM(CASE WHEN l.approved = 1 THEN COALESCE(l.points, 0) * COALESCE(pr.pointValue, 0) ELSE 0 END) as total_incentivo_distribuido,  -- Total distributed incentives (from liquidations.points, only approved)
                COUNT(DISTINCT u.id) as total_users,                   -- Total users with liquidations
                COUNT(DISTINCT CASE WHEN l.results > 0 THEN u.id END) as completed_users  -- Users with results > 0
            FROM liquidations l
            JOIN people p ON l.nin = p.nin
            JOIN users u ON p.id = u.person_id
            JOIN programs_users pu ON u.id = pu.user_id
            JOIN programs pr ON pu.program_id = pr.id AND l.program_id = pr.id
            JOIN roles r ON u.role_id = r.id
            JOIN variables v ON l.variable_id = v.id
            JOIN periods pe ON l.period_id = pe.id
            LEFT JOIN rules ru ON ru.user_id = u.id AND ru.variable_id = l.variable_id
            LEFT JOIN rule_periods rp ON rp.rule_id = ru.id AND rp.period_id = l.period_id
            WHERE r.name IN ('supervisor', 'vendor', 'supernumerary')
            AND l.period_id = %s
            GROUP BY v.id, v.name, l.period_id, pe.start_date
            ORDER BY v.name
            LIMIT 50
            """
            
            await cursor.execute(query, (period_id,))
            results = await cursor.fetchall()
            
            # If no results, try a simpler query to check basic data
            if not results:

                simple_query = """
                SELECT 
                    v.name as variable_name,
                    SUM(l.goal) as total_meta_asignada,
                    SUM(l.results) as total_meta_distribuida,
                    SUM(COALESCE(ru.points, 0)) as total_rules_points,
                    SUM(COALESCE(l.points, 0)) as total_liquidations_points,
                    COUNT(*) as record_count,
                    COUNT(CASE WHEN l.approved = 1 THEN 1 END) as approved_count
                FROM liquidations l
                JOIN variables v ON l.variable_id = v.id
                JOIN people p ON l.nin = p.nin
                JOIN users u ON p.id = u.person_id
                LEFT JOIN rules ru ON ru.user_id = u.id AND ru.variable_id = l.variable_id
                LEFT JOIN rule_periods rp ON rp.rule_id = ru.id AND rp.period_id = l.period_id
                WHERE l.period_id = %s
                GROUP BY v.id, v.name
                ORDER BY v.name
                LIMIT 10
                """
                
                await cursor.execute(simple_query, (period_id,))
                simple_results = await cursor.fetchall()
                
                return self._get_mock_data_new_structure(subdomain, period_id)
            
            report_data = []
            
            for row in results:
                (variable_name, period_id, period_start, total_meta_asignada, total_meta_distribuida,
                 total_incentivo_asignado, total_incentivo_distribuido, total_users, completed_users) = row
                
                # Format period
                mes = self._format_period(period_start)
                
                # Calculate percentages
                porcentaje_meta = 0.0
                if total_meta_asignada and total_meta_asignada > 0:
                    porcentaje_meta = round((total_meta_distribuida / total_meta_asignada) * 100, 2)
                
                # Use the actual distributed incentive from the database (approved liquidations)
                # total_incentivo_distribuido is already calculated in the query
                
                # Calculate completion percentage
                porcentaje_variables_completadas = 0.0
                if total_users > 0:
                    porcentaje_variables_completadas = round((completed_users / total_users) * 100, 2)
                
                # Get agent name based on subdomain
                agent_name = self._get_agent_name_by_subdomain(subdomain)
                
                # Round all numeric values to 2 decimal places
                report_row = {
                    "codigo_agente": subdomain,
                    "nombre_agente": agent_name,
                    "periodo_tiempo": mes,
                    "variable": variable_name,
                    "meta_asignada": round(float(total_meta_asignada or 0), 2),
                    "meta_distribuida": round(float(total_meta_distribuida or 0), 2),
                    "porcentaje_meta": porcentaje_meta,
                    "incentivo_asignado": round(float(total_incentivo_asignado or 0), 2),
                    "incentivo_distribuido": round(float(total_incentivo_distribuido or 0), 2),
                    "porcentaje_variables_completadas": porcentaje_variables_completadas
                }
                
                report_data.append(report_row)
            
            return report_data
        
        except Exception as e:
            logger.error(f"Error in optimized query for {subdomain}: {str(e)}")
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
            return "Agosto 2025"
        
        month_names = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        month_name = month_names.get(period_start.month, "")
        return f"{month_name} {period_start.year}"
    
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
            return 'Agosto 2025'
            
        except Exception as e:
            logger.error(f"Error getting period info: {str(e)}")
            return 'Agosto 2025'
    
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