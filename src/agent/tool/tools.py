"""
Tool definitions for the Employee Lifecycle Agent
Handles both asset assignment (onboarding) and asset recovery (offboarding)
"""

import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.database.models import Employee, Asset
from datetime import datetime, timedelta


class EmployeeLifecycleTools:
    """Tools for employee lifecycle operations (onboarding and offboarding)"""
    
    # ===== ASSET ASSIGNMENT TOOLS (Onboarding) =====
    
    @staticmethod
    def get_asset_requirements(employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Get the asset requirements based on employee role and department
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with asset requirements
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            return {"error": f"Employee {employee_id} not found"}
        
        requirements = {
            "employee_id": employee_id,
            "employee_name": employee.full_name,
            "department": employee.department,
            "role": employee.role,
            "assets_needed": []
        }
        
        # IT employees: 1 laptop + 2 monitors
        if employee.department == "it":
            requirements["assets_needed"] = [
                {"type": "laptop", "quantity": 1, "priority": 1},
                {"type": "monitor", "quantity": 2, "priority": 2}
            ]
        # Marketing employees: 1 laptop + 1 monitor
        elif employee.department == "marketing":
            requirements["assets_needed"] = [
                {"type": "laptop", "quantity": 1, "priority": 1},
                {"type": "monitor", "quantity": 1, "priority": 2}
            ]
        
        # Managers get an additional phone
        if employee.role == "manager":
            requirements["assets_needed"].append(
                {"type": "phone", "quantity": 1, "priority": 3}
            )
        
        return requirements

    @staticmethod
    def find_available_assets(device_type: str, quantity: int, db: Session) -> Dict[str, Any]:
        """
        Find available assets of a specific type, ordered by condition preference
        (excellent > good > fair)
        
        Args:
            device_type: Type of device (laptop, monitor, phone)
            quantity: Number of assets needed
            db: Database session
            
        Returns:
            Dictionary with available assets
        """
        # Define condition priority (higher number = better)
        condition_order = {"excellent": 3, "good": 2, "fair": 1, "poor": 0, "damaged": -1}
        
        assets = db.query(Asset).filter(
            Asset.device_type == device_type,
            Asset.status == "available",
            Asset.assigned_to.is_(None),
            Asset.condition.in_(["excellent", "good", "fair"])
        ).all()
        
        # Sort by condition priority
        assets_sorted = sorted(
            assets,
            key=lambda a: condition_order.get(a.condition, 0),
            reverse=True
        )
        
        available = assets_sorted[:quantity]
        
        return {
            "device_type": device_type,
            "requested_quantity": quantity,
            "available_count": len(available),
            "assets": [
                {
                    "asset_id": a.asset_id,
                    "asset_tag": a.asset_tag,
                    "serial_number": a.serial_number,
                    "condition": a.condition,
                    "brand": a.brand,
                    "model": a.model
                }
                for a in available
            ]
        }

    @staticmethod
    def assign_asset_to_employee(employee_id: int, asset_id: int, db: Session) -> Dict[str, Any]:
        """
        Assign an asset to an employee
        
        Args:
            employee_id: Employee ID
            asset_id: Asset ID
            db: Database session
            
        Returns:
            Dictionary with assignment result
        """
        try:
            asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
            
            if not asset:
                return {"error": f"Asset {asset_id} not found", "success": False}
            
            if asset.status != "available" or asset.assigned_to is not None:
                return {"error": f"Asset {asset_id} is not available", "success": False}
            
            employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                return {"error": f"Employee {employee_id} not found", "success": False}
            
            # Assign asset
            asset.assigned_to = employee_id
            asset.assignment_date = datetime.now().date()
            asset.status = "assigned"
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Asset {asset.asset_tag} assigned to {employee.full_name}",
                "asset_id": asset_id,
                "asset_tag": asset.asset_tag,
                "employee_id": employee_id,
                "employee_name": employee.full_name,
                "device_type": asset.device_type,
                "condition": asset.condition
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    @staticmethod
    def get_assignment_summary(employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Get summary of assets assigned to an employee
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with assignment summary
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            return {"error": f"Employee {employee_id} not found"}
        
        assets = db.query(Asset).filter(
            Asset.assigned_to == employee_id,
            Asset.status == "assigned"
        ).all()
        
        summary = {
            "employee_id": employee_id,
            "employee_name": employee.full_name,
            "department": employee.department,
            "role": employee.role,
            "total_assets": len(assets),
            "assets_by_type": {}
        }
        
        for asset in assets:
            if asset.device_type not in summary["assets_by_type"]:
                summary["assets_by_type"][asset.device_type] = []
            
            summary["assets_by_type"][asset.device_type].append({
                "asset_tag": asset.asset_tag,
                "serial_number": asset.serial_number,
                "condition": asset.condition,
                "brand": asset.brand,
                "model": asset.model
            })
        
        return summary
    
    # ===== ASSET RECOVERY TOOLS (Offboarding) =====
    
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
    # ===== ASSET HEALTH & REFRESH TRACKER TOOLS =====
    
    @staticmethod
    def get_assets_for_refresh(db: Session, age_threshold_years: int = 3) -> Dict[str, Any]:
        """
        Get all assets that need refresh/replacement based on age
        Assets older than age_threshold_years are marked for refresh
        
        Args:
            db: Database session
            age_threshold_years: Age threshold in years (default 3)
            
        Returns:
            Dictionary with assets marked for refresh
        """
        today = datetime.now().date()
        age_threshold_days = age_threshold_years * 365
        
        all_assets = db.query(Asset).all()
        
        refresh_assets = []
        for asset in all_assets:
            asset_age_days = (today - asset.purchase_date).days
            
            if asset_age_days > age_threshold_days:
                age_years = asset_age_days / 365
                refresh_assets.append({
                    "asset_id": asset.asset_id,
                    "asset_tag": asset.asset_tag,
                    "serial_number": asset.serial_number,
                    "device_type": asset.device_type,
                    "brand": asset.brand,
                    "model": asset.model,
                    "purchase_date": asset.purchase_date.isoformat(),
                    "age_years": round(age_years, 1),
                    "age_days": asset_age_days,
                    "purchase_value": float(asset.purchase_value),
                    "current_value": float(asset.current_value),
                    "condition": asset.condition,
                    "assigned_to": asset.assigned_to,
                    "status": asset.status,
                    "refresh_status": "URGENT" if age_years > 5 else "RECOMMENDED"
                })
        
        # Sort by age (oldest first)
        refresh_assets_sorted = sorted(refresh_assets, key=lambda x: x["age_years"], reverse=True)
        
        return {
            "success": True,
            "total_assets": len(all_assets),
            "refresh_count": len(refresh_assets_sorted),
            "age_threshold_years": age_threshold_years,
            "assets_for_refresh": refresh_assets_sorted,
            "total_refresh_value": round(sum(a["current_value"] for a in refresh_assets_sorted), 2)
        }
    
    @staticmethod
    def get_asset_health_summary(db: Session) -> Dict[str, Any]:
        """
        Get comprehensive asset health and age summary
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with asset health metrics
        """
        today = datetime.now().date()
        all_assets = db.query(Asset).all()
        
        if not all_assets:
            return {
                "success": True,
                "total_assets": 0,
                "health_summary": {}
            }
        
        # Calculate age statistics
        ages_days = [(today - asset.purchase_date).days for asset in all_assets]
        ages_years = [age / 365 for age in ages_days]
        
        # Categorize by age
        new_assets = [a for a in all_assets if (today - a.purchase_date).days <= 365]
        mid_age_assets = [a for a in all_assets if 365 < (today - a.purchase_date).days <= 3*365]
        old_assets = [a for a in all_assets if (today - a.purchase_date).days > 3*365]
        
        # Categorize by condition
        by_condition = {}
        for condition in ["excellent", "good", "fair", "poor", "damaged"]:
            count = len([a for a in all_assets if a.condition == condition])
            if count > 0:
                by_condition[condition] = count
        
        # Categorize by type
        by_type = {}
        for asset_type in ["laptop", "monitor", "phone"]:
            count = len([a for a in all_assets if a.device_type == asset_type])
            if count > 0:
                by_type[asset_type] = count
        
        return {
            "success": True,
            "total_assets": len(all_assets),
            "health_summary": {
                "age_statistics": {
                    "average_age_years": round(sum(ages_years) / len(ages_years), 1),
                    "oldest_asset_years": round(max(ages_years), 1),
                    "newest_asset_years": round(min(ages_years), 1)
                },
                "age_categories": {
                    "new_0_1_years": len(new_assets),
                    "mid_age_1_3_years": len(mid_age_assets),
                    "old_over_3_years": len(old_assets)
                },
                "condition_distribution": by_condition,
                "device_type_distribution": by_type,
                "total_asset_value": round(sum(float(a.current_value) for a in all_assets), 2),
                "depreciation_percent": round(
                    (1 - (sum(float(a.current_value) for a in all_assets) / 
                          sum(float(a.purchase_value) for a in all_assets))) * 100, 1
                ) if sum(float(a.purchase_value) for a in all_assets) > 0 else 0
            }
        }
    
    @staticmethod
    def get_assets_by_age_range(
        db: Session,
        min_years: int = 0,
        max_years: int = 10
    ) -> Dict[str, Any]:
        """
        Get assets within a specific age range
        
        Args:
            db: Database session
            min_years: Minimum age in years
            max_years: Maximum age in years
            
        Returns:
            Dictionary with assets in age range
        """
        today = datetime.now().date()
        min_days = min_years * 365
        max_days = max_years * 365
        
        all_assets = db.query(Asset).all()
        
        assets_in_range = []
        for asset in all_assets:
            asset_age_days = (today - asset.purchase_date).days
            
            if min_days <= asset_age_days <= max_days:
                age_years = asset_age_days / 365
                assets_in_range.append({
                    "asset_id": asset.asset_id,
                    "asset_tag": asset.asset_tag,
                    "device_type": asset.device_type,
                    "brand": asset.brand,
                    "model": asset.model,
                    "purchase_date": asset.purchase_date.isoformat(),
                    "age_years": round(age_years, 1),
                    "condition": asset.condition,
                    "current_value": float(asset.current_value)
                })
        
        return {
            "success": True,
            "age_range": {"min_years": min_years, "max_years": max_years},
            "asset_count": len(assets_in_range),
            "assets": assets_in_range
        }