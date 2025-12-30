"""
Tools for Asset Recovery Agent
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.database.models import Employee, Asset
from datetime import datetime, timedelta


class AssetRecoveryTools:
    """Tools for asset recovery operations"""
    
    @staticmethod
    def get_employee_assets(employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Get all assets assigned to an employee
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with employee and their assets
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            return {"error": f"Employee {employee_id} not found"}
        
        assets = db.query(Asset).filter(
            Asset.assigned_to == employee_id,
            Asset.status == "assigned"
        ).all()
        
        return {
            "employee_id": employee_id,
            "employee_name": employee.full_name,
            "employee_email": employee.email,
            "manager_id": employee.manager_id,
            "resignation_date": employee.resignation_date.isoformat() if employee.resignation_date else None,
            "employment_status": employee.employment_status,
            "total_assets": len(assets),
            "assets": [
                {
                    "asset_id": a.asset_id,
                    "asset_tag": a.asset_tag,
                    "serial_number": a.serial_number,
                    "device_type": a.device_type,
                    "brand": a.brand,
                    "model": a.model,
                    "condition": a.condition,
                    "purchase_value": float(a.purchase_value),
                    "current_value": float(a.current_value)
                }
                for a in assets
            ]
        }
    
    @staticmethod
    def get_manager_info(manager_id: int, db: Session) -> Dict[str, Any]:
        """
        Get manager information
        
        Args:
            manager_id: Manager employee ID
            db: Database session
            
        Returns:
            Dictionary with manager info
        """
        manager = db.query(Employee).filter(Employee.employee_id == manager_id).first()
        
        if not manager:
            return {"error": f"Manager {manager_id} not found", "manager_id": manager_id}
        
        return {
            "manager_id": manager.employee_id,
            "manager_name": manager.full_name,
            "manager_email": manager.email,
            "department": manager.department
        }
    
    @staticmethod
    def schedule_asset_returns(
        employee_id: int,
        return_due_date: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Schedule asset returns for an employee
        
        Args:
            employee_id: Employee ID
            return_due_date: Return due date (ISO format)
            db: Database session
            
        Returns:
            Dictionary with update results
        """
        try:
            due_date = datetime.fromisoformat(return_due_date).date()
            
            assets = db.query(Asset).filter(
                Asset.assigned_to == employee_id,
                Asset.status == "assigned"
            ).all()
            
            updated_count = 0
            for asset in assets:
                asset.return_due_date = due_date
                asset.status = "assigned"  # Keep assigned but with return due date
                updated_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Return dates scheduled for {updated_count} assets",
                "employee_id": employee_id,
                "return_due_date": return_due_date,
                "assets_affected": updated_count
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "employee_id": employee_id
            }
    
    @staticmethod
    def calculate_return_due_date(resignation_date: str, days: int = 7) -> str:
        """
        Calculate return due date based on resignation date
        
        Args:
            resignation_date: Resignation date (ISO format)
            days: Days to add (default 7)
            
        Returns:
            Return due date as ISO format string
        """
        date = datetime.fromisoformat(resignation_date).date()
        return_date = date + timedelta(days=days)
        return return_date.isoformat()
    
    @staticmethod
    def get_resignation_summary(employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Get resignation and asset recovery summary
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with resignation summary
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            return {"error": f"Employee {employee_id} not found"}
        
        assets = db.query(Asset).filter(
            Asset.assigned_to == employee_id,
            Asset.status == "assigned"
        ).all()
        
        # Count by type
        assets_by_type = {}
        total_value = 0
        for asset in assets:
            if asset.device_type not in assets_by_type:
                assets_by_type[asset.device_type] = 0
            assets_by_type[asset.device_type] += 1
            total_value += float(asset.current_value)
        
        manager = None
        if employee.manager_id:
            manager = db.query(Employee).filter(Employee.employee_id == employee.manager_id).first()
        
        return {
            "employee_id": employee.employee_id,
            "employee_name": employee.full_name,
            "employee_email": employee.email,
            "resignation_date": employee.resignation_date.isoformat() if employee.resignation_date else None,
            "last_working_day": employee.last_working_day.isoformat() if employee.last_working_day else None,
            "employment_status": employee.employment_status,
            "manager_name": manager.full_name if manager else None,
            "manager_email": manager.email if manager else None,
            "total_assets": len(assets),
            "assets_by_type": assets_by_type,
            "total_asset_value": round(total_value, 2),
            "assets": [
                {
                    "asset_tag": a.asset_tag,
                    "device_type": a.device_type,
                    "brand": a.brand,
                    "model": a.model,
                    "condition": a.condition,
                    "current_value": float(a.current_value),
                    "return_due_date": a.return_due_date.isoformat() if a.return_due_date else None
                }
                for a in assets
            ]
        }
