from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from app.services.report_service import ReportService
from app.services.excel_service import ExcelService
from app.models.schemas import ReportResponse
import io
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/reports/{period_id}", response_model=ReportResponse)
async def generate_report(period_id: int):
    """
    Generate report by aggregating data from all subdomains for a specific period
    """
    try:
        import asyncio
        
        # Add timeout to prevent hanging
        report_service = ReportService()
        report_data = await asyncio.wait_for(
            report_service.generate_report(period_id), 
            timeout=300.0  # 5 minutes timeout
        )
        
        # Create response with cache-busting headers
        response = ReportResponse(**report_data)
        
        # Add cache-busting headers to prevent stale data
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Last-Modified": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
            "ETag": f'"{int(time.time())}-{period_id}"'
        }
        
        return Response(
            content=response.model_dump_json(),
            media_type="application/json",
            headers=headers
        )
        
    except asyncio.TimeoutError:
        logger.error("Report generation timed out after 5 minutes")
        raise HTTPException(status_code=408, detail="Report generation timed out after 5 minutes. Please try again.")
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.get("/reports/{period_id}/excel")
async def generate_excel_report(period_id: int):
    """
    Generate Excel report by aggregating data from all subdomains for a specific period
    """
    try:
        import asyncio
        
        report_service = ReportService()
        excel_service = ExcelService()
        
        # Get report data with timeout
        report_data = await asyncio.wait_for(
            report_service.generate_report(period_id), 
            timeout=300.0  # 5 minutes timeout
        )
        
        # Generate Excel file
        excel_buffer = excel_service.create_excel_report(report_data['data'])
        
        # Add cache-busting headers to prevent stale data
        headers = {
            "Content-Disposition": f"attachment; filename=nutresa_report_period_{period_id}_{int(time.time())}.xlsx",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Last-Modified": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
            "ETag": f'"{int(time.time())}-{period_id}"'
        }
        
        # Return Excel file as streaming response
        return StreamingResponse(
            io.BytesIO(excel_buffer),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
        
    except asyncio.TimeoutError:
        logger.error("Excel report generation timed out after 5 minutes")
        raise HTTPException(status_code=408, detail="Excel report generation timed out after 5 minutes. Please try again.")
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating Excel report: {str(e)}")

@router.get("/periods")
async def get_periods():
    """
    Get list of available periods
    """
    try:
        from app.core.database import db_manager
        # Get periods from the first available subdomain as a sample
        subdomains = db_manager.get_available_subdomains()
        if not subdomains:
            return {"periods": [], "message": "No subdomains available"}
        
        connection = await db_manager.get_connection(subdomains[0])
        cursor = await connection.cursor()
        
        await cursor.execute("""
            SELECT id, start_date, end_date, name 
            FROM periods 
            ORDER BY start_date DESC 
            LIMIT 20
        """)
        results = await cursor.fetchall()
        await cursor.close()
        
        periods = []
        for row in results:
            periods.append({
                "id": row[0],
                "start_date": row[1].isoformat() if row[1] else None,
                "end_date": row[2].isoformat() if row[2] else None,
                "name": row[3] or f"Period {row[0]}"
            })
        
        return {"periods": periods}
        
    except Exception as e:
        logger.error(f"Error getting periods: {str(e)}")
        # Return mock periods if database query fails
        return {
            "periods": [
                {"id": 1, "start_date": "2025-08-01", "end_date": "2025-08-31", "name": "Agosto 2025"},
                {"id": 2, "start_date": "2025-07-01", "end_date": "2025-07-31", "name": "Julio 2025"},
                {"id": 3, "start_date": "2025-06-01", "end_date": "2025-06-30", "name": "Junio 2025"}
            ],
            "message": "Using mock data - database connection failed"
        }

@router.get("/subdomains")
async def get_subdomains():
    """
    Get list of available subdomains
    """
    try:
        from app.core.database import db_manager
        subdomains = db_manager.get_available_subdomains()
        return {"subdomains": subdomains}
        
    except Exception as e:
        logger.error(f"Error getting subdomains: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting subdomains: {str(e)}")

@router.get("/test-subdomains")
async def test_subdomains_connection():
    """
    Test connection to all configured subdomains (first 5 only)
    Each subdomain is a database within the main MySQL server
    """
    try:
        from app.core.database import db_manager
        subdomain_results = await db_manager.test_all_subdomains()
        return subdomain_results
        
    except Exception as e:
        logger.error(f"Error testing subdomains: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
