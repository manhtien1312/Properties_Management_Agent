"""
Unified chatbot tools for answering various HR and asset management questions
"""
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
from src.database.models import Employee, Asset
from src.agent.tool.churn_prediction_tools import ChurnPredictionTools
from src.agent.tool.tools import EmployeeLifecycleTools


class UnifiedChatbotTools:
    """Tools for answering various chatbot questions"""
    
    @staticmethod
    def get_employee_asset_count(employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Get count and details of assets currently assigned to an employee
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with asset count and details
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            return {
                "success": False,
                "error": f"Employee with ID {employee_id} not found"
            }
        
        assets = db.query(Asset).filter(
            Asset.assigned_to == employee_id,
            Asset.status == "assigned"
        ).all()
        
        # Group by device type
        assets_by_type = {}
        for asset in assets:
            if asset.device_type not in assets_by_type:
                assets_by_type[asset.device_type] = []
            
            assets_by_type[asset.device_type].append({
                "asset_tag": asset.asset_tag,
                "brand": asset.brand,
                "model": asset.model,
                "condition": asset.condition,
                "purchase_date": asset.purchase_date.isoformat(),
                "current_value": float(asset.current_value)
            })
        
        # Count by type
        count_by_type = {device_type: len(items) for device_type, items in assets_by_type.items()}
        
        return {
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee.full_name,
            "employee_email": employee.email,
            "department": employee.department,
            "total_assets": len(assets),
            "count_by_type": count_by_type,
            "assets_by_type": assets_by_type,
            "total_asset_value": round(sum(float(a.current_value) for a in assets), 2)
        }
    
    @staticmethod
    def get_resignation_assets_info(employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Get information about assets that must be returned if employee resigns
        and whether they need refresh
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with resignation asset info including refresh needs
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            return {
                "success": False,
                "error": f"Employee with ID {employee_id} not found"
            }
        
        # Get all assets assigned to employee
        assets = db.query(Asset).filter(
            Asset.assigned_to == employee_id,
            Asset.status == "assigned"
        ).all()
        
        if not assets:
            return {
                "success": True,
                "employee_id": employee_id,
                "employee_name": employee.full_name,
                "total_assets_to_return": 0,
                "message": "This employee has no assets to return"
            }
        
        # Analyze each asset for refresh needs (3+ years old)
        today = datetime.now().date()
        refresh_threshold_days = 3 * 365  # 3 years
        
        assets_to_return = []
        needs_refresh_count = 0
        total_value = 0
        
        for asset in assets:
            asset_age_days = (today - asset.purchase_date).days
            asset_age_years = asset_age_days / 365
            needs_refresh = asset_age_days > refresh_threshold_days
            
            if needs_refresh:
                needs_refresh_count += 1
            
            total_value += float(asset.current_value)
            
            refresh_status = "URGENT" if asset_age_years > 5 else ("RECOMMENDED" if needs_refresh else "OK")
            
            assets_to_return.append({
                "asset_tag": asset.asset_tag,
                "serial_number": asset.serial_number,
                "device_type": asset.device_type,
                "brand": asset.brand,
                "model": asset.model,
                "condition": asset.condition,
                "purchase_date": asset.purchase_date.isoformat(),
                "age_years": round(asset_age_years, 1),
                "current_value": float(asset.current_value),
                "needs_refresh": needs_refresh,
                "refresh_status": refresh_status,
                "refresh_reason": f"Asset is {asset_age_years:.1f} years old" if needs_refresh else "Asset is still within acceptable age"
            })
        
        # Group by device type with refresh status
        by_type_with_refresh = {}
        for asset in assets_to_return:
            device_type = asset["device_type"]
            if device_type not in by_type_with_refresh:
                by_type_with_refresh[device_type] = {
                    "total": 0,
                    "needs_refresh": 0,
                    "ok_to_reassign": 0
                }
            
            by_type_with_refresh[device_type]["total"] += 1
            if asset["needs_refresh"]:
                by_type_with_refresh[device_type]["needs_refresh"] += 1
            else:
                by_type_with_refresh[device_type]["ok_to_reassign"] += 1
        
        return {
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee.full_name,
            "employee_email": employee.email,
            "department": employee.department,
            "employment_status": employee.employment_status,
            "resignation_date": employee.resignation_date.isoformat() if employee.resignation_date else None,
            "total_assets_to_return": len(assets_to_return),
            "assets_need_refresh": needs_refresh_count,
            "assets_ok_to_reassign": len(assets_to_return) - needs_refresh_count,
            "total_asset_value": round(total_value, 2),
            "summary_by_type": by_type_with_refresh,
            "assets": assets_to_return,
            "recommendation": (
                f"When this employee resigns, {len(assets_to_return)} asset(s) must be returned. "
                f"{needs_refresh_count} asset(s) need refresh (>3 years old) and should be replaced. "
                f"{len(assets_to_return) - needs_refresh_count} asset(s) can be reassigned to new employees."
            )
        }
    
    @staticmethod
    def classify_question_type(question: str) -> str:
        """
        Classify the type of question being asked
        
        Args:
            question: User's question
            
        Returns:
            Question type: 'asset_count', 'resignation_assets', 'churn_prediction', 
                          'churn_list', 'churn_department', 'asset_health', 
                          'procurement_forecast', 'send_recovery_email', or 'general'
        """
        question_lower = question.lower()
        
        # Email sending for asset recovery
        if any(keyword in question_lower for keyword in [
            "send email", "send notification", "notify", "email notification",
            "yes send", "send recovery email", "send asset return", "email him",
            "email her", "send the email", "yes, send", "please send", 
            "okay send", "ok send", "sure send"
        ]):
            return "send_recovery_email"
        
        # Procurement forecasting questions
        if any(keyword in question_lower for keyword in [
            "asset shortage", "buy more assets", "need to buy", "purchase asset",
            "procurement", "should we buy", "do i need to buy", "need more assets",
            "shortage", "need to purchase", "asset demand", "procurement forecast"
        ]):
            return "procurement_forecast"
        
        # Asset health report questions
        if any(keyword in question_lower for keyword in [
            "asset health", "health report", "asset condition", "aging assets",
            "assets need refresh", "asset age", "asset status", "health summary",
            "show report about assets", "asset overview"
        ]):
            return "asset_health"
        
        # Asset count questions
        if any(keyword in question_lower for keyword in [
            "how many asset", "asset count", "assets using", "assets assigned",
            "what assets does", "list assets", "assets held by"
        ]):
            return "asset_count"
        
        # Resignation/return questions
        if any(keyword in question_lower for keyword in [
            "resign", "return", "offboard", "leave", "quit", "asset return",
            "must be returned", "need to return", "needs refresh", "replacement"
        ]):
            # Check if it's about listing multiple employees
            if any(keyword in question_lower for keyword in ["which employees", "who is", "list employees"]):
                # Check if department-specific
                if any(dept in question_lower for dept in ["it department", "marketing department", "in it", "in marketing"]):
                    return "churn_department"
                return "churn_list"
            return "resignation_assets"
        
        # Churn prediction list questions (which employees, who is likely)
        if any(keyword in question_lower for keyword in [
            "which employees", "who is likely", "who are likely", "list employees",
            "which staff", "who might", "employees at risk"
        ]):
            # Check if department-specific
            if any(dept in question_lower for dept in ["it department", "marketing department", "in it", "in marketing"]):
                return "churn_department"
            return "churn_list"
        
        # Single employee churn prediction questions
        if any(keyword in question_lower for keyword in [
            "churn", "resign risk", "risk", "leaving", "turnover", "attrition",
            "probability", "predict", "likely to leave"
        ]):
            return "churn_prediction"
        
        return "general"
    
    @staticmethod
    def extract_employee_id(question: str) -> int:
        """
        Extract employee ID from question text
        
        Args:
            question: User's question
            
        Returns:
            Employee ID if found, None otherwise
        """
        import re
        
        # Look for patterns like "employee 5", "employee ID 5", "employee #5", "emp 5"
        patterns = [
            r'employee\s+(?:id\s+)?#?(\d+)',
            r'emp\s+(?:id\s+)?#?(\d+)',
            r'id\s+(\d+)',
            r'#(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    @staticmethod
    def extract_department(question: str) -> str:
        """
        Extract department from question text
        
        Args:
            question: User's question
            
        Returns:
            Department name ('it' or 'marketing') if found, None otherwise
        """
        question_lower = question.lower()
        
        # Check for IT department
        if any(keyword in question_lower for keyword in [
            "it department", "information technology", "in it", "it dept"
        ]):
            return "it"
        
        # Check for Marketing department
        if any(keyword in question_lower for keyword in [
            "marketing department", "in marketing", "marketing dept"
        ]):
            return "marketing"
        
        return None
