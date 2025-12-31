"""
Procurement Forecasting API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.database import get_db
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


@router.get("/forecast")
async def get_procurement_forecast(
    forecast_months: int = 6,
    safety_stock_percent: float = 0.2,
    db: Session = Depends(get_db)
):
    """
    Get procurement forecast based on asset health and churn predictions
    
    Args:
        forecast_months: Number of months to forecast (default: 6)
        safety_stock_percent: Safety stock buffer as decimal (default: 0.2 = 20%)
    
    Returns:
        Procurement recommendations with purchase quantities by device type
    
    Example:
        GET /api/procurement/forecast?forecast_months=6&safety_stock_percent=0.2
        
        Response:
        {
            "success": true,
            "summary_message": "⚠️  Procurement needed for 2 device type(s):\\n  • laptop: Purchase 5 units (HIGH priority)\\n",
            "recommendations": [
                {
                    "device_type": "laptop",
                    "demand_breakdown": {
                        "refresh_needed": 3,
                        "churn_replacement": 2,
                        "total_needed_with_buffer": 6
                    },
                    "inventory": {
                        "available_stock": 1,
                        "shortage": 5
                    },
                    "action_required": true,
                    "purchase_quantity": 5,
                    "priority": "HIGH",
                    "recommendation": "Purchase 5 laptop(s) to meet demand..."
                }
            ]
        }
    """
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.get_procurement_forecast(db, forecast_months, safety_stock_percent)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/report")
async def get_procurement_report(
    include_details: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive procurement report
    
    Args:
        include_details: Include detailed asset and employee information (default: true)
    
    Returns:
        Comprehensive procurement forecast report with demand drivers
    
    Example:
        GET /api/procurement/report?include_details=true
        
        Response:
        {
            "success": true,
            "executive_summary": {
                "procurement_needed": true,
                "total_units_to_purchase": 8,
                "device_types_affected": 2
            },
            "recommendations": [...],
            "demand_drivers": {
                "aging_assets": {
                    "total": 5,
                    "by_type": {"laptop": 3, "monitor": 2}
                },
                "employee_churn": {
                    "high_risk_employees": 3,
                    "assets_at_risk": 4
                }
            }
        }
    """
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.get_procurement_report(db, include_details)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/demand")
async def get_asset_demand(
    forecast_months: int = 6,
    db: Session = Depends(get_db)
):
    """
    Get detailed asset demand breakdown
    
    Args:
        forecast_months: Number of months to forecast (default: 6)
    
    Returns:
        Detailed breakdown of asset demand from refresh and churn
    
    Example:
        GET /api/procurement/demand?forecast_months=6
        
        Response:
        {
            "success": true,
            "refresh_assets": {
                "total_count": 5,
                "by_type": {
                    "laptop": {
                        "urgent": 2,
                        "recommended": 1,
                        "assets": [...]
                    }
                }
            },
            "churn_replacement": {
                "high_risk_employees": 3,
                "total_assets_at_risk": 4,
                "by_type": {"laptop": 2, "monitor": 2}
            },
            "total_demand": {
                "laptop": {
                    "refresh_needed": 3,
                    "churn_replacement": 2,
                    "total_demand": 5
                }
            }
        }
    """
    try:
        from src.agent.tool.procurement_forecasting_tools import ProcurementForecastingTools
        
        result = ProcurementForecastingTools.calculate_asset_demand(db, forecast_months)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/summary")
async def get_procurement_summary(
    db: Session = Depends(get_db)
):
    """
    Get quick procurement summary (simplified view)
    
    Returns:
        Simplified procurement summary
    
    Example:
        GET /api/procurement/summary
        
        Response:
        {
            "success": true,
            "procurement_needed": true,
            "total_units_to_purchase": 8,
            "purchase_by_type": {
                "laptop": 5,
                "monitor": 3
            },
            "message": "Purchase needed: 5 laptop(s), 3 monitor(s)"
        }
    """
    try:
        agent = get_employee_lifecycle_agent()
        full_forecast = agent.get_procurement_forecast(db)
        
        if not full_forecast.get('success'):
            return full_forecast
        
        # Build simplified summary
        purchase_by_type = {}
        urgent_types = []
        
        for rec in full_forecast['recommendations']:
            if rec['action_required']:
                device_type = rec['device_type']
                quantity = rec['purchase_quantity']
                purchase_by_type[device_type] = quantity
                
                if rec['priority'] in ['HIGH', 'URGENT']:
                    urgent_types.append(f"{quantity} {device_type}(s)")
        
        if purchase_by_type:
            items = [f"{qty} {dtype}(s)" for dtype, qty in purchase_by_type.items()]
            message = f"Purchase needed: {', '.join(items)}"
        else:
            message = "Inventory sufficient for forecasted demand"
        
        return {
            "success": True,
            "procurement_needed": len(purchase_by_type) > 0,
            "total_units_to_purchase": sum(purchase_by_type.values()),
            "purchase_by_type": purchase_by_type,
            "urgent_items": urgent_types,
            "message": message,
            "forecast_period": f"{full_forecast['forecast_period_months']} months"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
