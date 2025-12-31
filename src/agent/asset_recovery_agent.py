"""
Asset Recovery Agent for handling employee resignation and asset return scheduling
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.config import settings
from src.agent.tools.recovery_tools import AssetRecoveryTools
from src.email_service import EmailService

logger = logging.getLogger(__name__)


class AssetRecoveryAgent:
    """AI Agent for handling asset recovery on employee resignation"""
    
    def __init__(self):
        """Initialize the recovery agent"""
        pass
    
    def process_resignation(
        self,
        employee_id: int,
        db: Session,
        return_days: int = 7
    ) -> Dict[str, Any]:
        """
        Process employee resignation and initiate asset recovery
        
        Args:
            employee_id: ID of resigning employee
            db: Database session
            return_days: Days until return due (default 7)
            
        Returns:
            Dictionary with recovery process results
        """
        
        logger.info(f"Processing resignation for employee {employee_id}")
        
        try:
            # Get employee assets
            employee_info = AssetRecoveryTools.get_employee_assets(employee_id, db)
            
            if "error" in employee_info:
                return {
                    "success": False,
                    "error": employee_info["error"]
                }
            
            # If no assets, just return success
            if employee_info["total_assets"] == 0:
                logger.info(f"Employee {employee_id} has no assets to recover")
                return {
                    "success": True,
                    "message": f"Employee {employee_info['employee_name']} has no assigned assets",
                    "total_assets": 0,
                    "assets_scheduled": 0,
                    "email_sent": False
                }
            
            # Calculate return due date
            resignation_date = employee_info["resignation_date"]
            if not resignation_date:
                logger.error(f"Employee {employee_id} has no resignation date set")
                return {
                    "success": False,
                    "error": "Employee resignation date not set"
                }
            
            return_due_date = AssetRecoveryTools.calculate_return_due_date(resignation_date, return_days)
            
            # Schedule asset returns
            schedule_result = AssetRecoveryTools.schedule_asset_returns(
                employee_id,
                return_due_date,
                db
            )
            
            if not schedule_result["success"]:
                return {
                    "success": False,
                    "error": schedule_result["error"]
                }
            
            # Get manager info
            manager_info = {}
            if employee_info["manager_id"]:
                manager_info = AssetRecoveryTools.get_manager_info(
                    employee_info["manager_id"],
                    db
                )
            
            # Send email notifications
            email_result = self._send_recovery_emails(
                employee_info,
                manager_info,
                return_due_date,
                return_days
            )
            
            # Get final summary
            summary = AssetRecoveryTools.get_resignation_summary(employee_id, db)
            
            return {
                "success": True,
                "message": f"Asset recovery initiated for {employee_info['employee_name']}",
                "employee_id": employee_id,
                "employee_name": employee_info["employee_name"],
                "resignation_date": resignation_date,
                "return_due_date": return_due_date,
                "total_assets": employee_info["total_assets"],
                "assets_scheduled": schedule_result["assets_affected"],
                "email_sent": email_result.get("success", False),
                "email_message": email_result.get("message", ""),
                "summary": summary
            }
        
        except Exception as e:
            logger.error(f"Error processing resignation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _send_recovery_emails(
        self,
        employee_info: Dict[str, Any],
        manager_info: Dict[str, Any],
        return_due_date: str,
        return_days: int
    ) -> Dict[str, Any]:
        """
        Send asset return notification emails
        
        Args:
            employee_info: Employee information
            manager_info: Manager information
            return_due_date: Return due date
            return_days: Days for return
            
        Returns:
            Dictionary with email results
        """
        
        try:
            resignation_date = employee_info["resignation_date"]
            manager_email = manager_info.get("manager_email") if manager_info and "error" not in manager_info else None
            
            # Format dates for display
            resign_dt = datetime.fromisoformat(resignation_date)
            due_dt = datetime.fromisoformat(return_due_date)
            
            resign_str = resign_dt.strftime("%B %d, %Y")
            due_str = due_dt.strftime("%B %d, %Y")
            
            # Send email
            result = EmailService.send_asset_return_notice(
                employee_name=employee_info["employee_name"],
                employee_email=employee_info["employee_email"],
                manager_email=manager_email,
                resignation_date=resign_str,
                return_due_date=due_str,
                assets=employee_info["assets"]
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error sending recovery emails: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_recovery_agent_instance = None


def get_asset_recovery_agent() -> AssetRecoveryAgent:
    """Get or create the singleton recovery agent instance"""
    global _recovery_agent_instance
    if _recovery_agent_instance is None:
        _recovery_agent_instance = AssetRecoveryAgent()
    return _recovery_agent_instance
