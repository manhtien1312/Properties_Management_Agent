"""
Employee Lifecycle Agent for handling both onboarding (asset assignment) and offboarding (asset recovery)
Uses LangChain with Google Gemini 2.0 Flash model
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.llms.base import LLM
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings
from src.agent.tool.tools import EmployeeLifecycleTools
from src.agent.tool.churn_prediction_tools import ChurnPredictionTools
from src.agent.tool.procurement_forecasting_tools import ProcurementForecastingTools
from src.email_service import EmailService

logger = logging.getLogger(__name__)


class EmployeeLifecycleAgent:
    """AI Agent for managing employee lifecycle (onboarding and offboarding)"""
    
    def __init__(self):
        """Initialize the agent with LangChain tools"""
        self.tools = self._setup_tools()
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Google Gemini LLM"""
        if not settings.google_api_key:
            logger.warning("GOOGLE_API_KEY not set. Agent will operate in demo mode.")
            return
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.google_api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}")
            self.llm = None
    
    def _setup_tools(self) -> list:
        """Setup the tools for the agent"""
        tools = [
            Tool(
                name="get_asset_requirements",
                func=lambda emp_id: json.dumps(
                    EmployeeLifecycleTools.get_asset_requirements(int(emp_id), self.db_session)
                ),
                description="Get asset requirements for an employee based on their role and department. Input should be employee_id"
            ),
            Tool(
                name="find_available_assets",
                func=lambda input_str: json.dumps(
                    self._parse_and_find_assets(input_str)
                ),
                description="Find available assets of a specific type. Input should be JSON: {\"device_type\": \"laptop\", \"quantity\": 1}"
            ),
            Tool(
                name="assign_asset",
                func=lambda input_str: json.dumps(
                    self._parse_and_assign_asset(input_str)
                ),
                description="Assign an asset to an employee. Input should be JSON: {\"employee_id\": 1, \"asset_id\": 5}"
            ),
            Tool(
                name="get_assignment_summary",
                func=lambda emp_id: json.dumps(
                    EmployeeLifecycleTools.get_assignment_summary(int(emp_id), self.db_session)
                ),
                description="Get summary of assets currently assigned to an employee. Input should be employee_id"
            ),
            # Recovery tools
            Tool(
                name="get_employee_assets",
                func=lambda emp_id: json.dumps(
                    EmployeeLifecycleTools.get_employee_assets(int(emp_id), self.db_session)
                ),
                description="Get all assets held by an employee. Input should be employee_id"
            ),
            Tool(
                name="get_manager_info",
                func=lambda mgr_id: json.dumps(
                    EmployeeLifecycleTools.get_manager_info(int(mgr_id), self.db_session)
                ),
                description="Get manager information. Input should be manager_id"
            ),
            Tool(
                name="schedule_asset_returns",
                func=lambda input_str: json.dumps(
                    self._parse_and_schedule_returns(input_str)
                ),
                description="Schedule asset returns for an employee. Input should be JSON: {\"employee_id\": 1, \"return_due_date\": \"2025-01-22\"}"
            ),
            Tool(
                name="get_resignation_summary",
                func=lambda emp_id: json.dumps(
                    EmployeeLifecycleTools.get_resignation_summary(int(emp_id), self.db_session)
                ),
                description="Get resignation and asset recovery summary for an employee. Input should be employee_id"
            )
        ]
        return tools
    
    def _parse_and_find_assets(self, input_str: str) -> Dict[str, Any]:
        """Parse input and find assets"""
        try:
            data = json.loads(input_str) if isinstance(input_str, str) else input_str
            return EmployeeLifecycleTools.find_available_assets(
                data["device_type"],
                data["quantity"],
                self.db_session
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_and_assign_asset(self, input_str: str) -> Dict[str, Any]:
        """Parse input and assign asset"""
        try:
            data = json.loads(input_str) if isinstance(input_str, str) else input_str
            return EmployeeLifecycleTools.assign_asset_to_employee(
                int(data["employee_id"]),
                int(data["asset_id"]),
                self.db_session
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_and_schedule_returns(self, input_str: str) -> Dict[str, Any]:
        """Parse input and schedule asset returns"""
        try:
            data = json.loads(input_str) if isinstance(input_str, str) else input_str
            return EmployeeLifecycleTools.schedule_asset_returns(
                int(data["employee_id"]),
                data["return_due_date"],
                self.db_session
            )
        except Exception as e:
            return {"error": str(e)}
    
    def assign_assets_to_employee(self, employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Use the AI Agent to assign assets to a new employee
        
        Args:
            employee_id: ID of the newly onboarded employee
            db: Database session
            
        Returns:
            Dictionary with assignment results
        """
        self.db_session = db
        
        try:
            # If no LLM is configured, use fallback logic
            if not self.llm or not settings.google_api_key:
                return self._fallback_asset_assignment(employee_id, db)
            
            # Initialize the agent
            agent = initialize_agent(
                self.tools,
                self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,
                handle_parsing_errors=True,
                max_iterations=10
            )
            
            # Create the prompt for the agent
            prompt = f"""
            A new employee with ID {employee_id} has been onboarded. 
            
            Your task is to:
            1. Get the asset requirements for this employee based on their role and department
            2. Find available assets that match their requirements (prioritize: excellent > good > fair condition)
            3. Assign all required assets to the employee
            4. Return a summary of the assignment
            
            Important:
            - Assign assets matching the quantity required for their role/department
            - Prioritize assets in better condition when multiple are available
            - Make sure each asset is successfully assigned before moving to the next one
            - Return a clear summary of what was assigned and any failures
            """
            
            result = agent.run(prompt)
            
            # Get the final summary
            summary = EmployeeLifecycleTools.get_assignment_summary(employee_id, db)
            
            return {
                "success": True,
                "agent_output": result,
                "assignment_summary": summary,
                "message": f"Assets successfully assigned to employee {employee_id}"
            }
        
        except Exception as e:
            logger.error(f"Agent error: {e}")
            # Fallback to deterministic assignment
            return self._fallback_asset_assignment(employee_id, db)
    
    def _fallback_asset_assignment(self, employee_id: int, db: Session) -> Dict[str, Any]:
        """Fallback deterministic asset assignment when LLM is not available"""
        logger.info("Using fallback asset assignment (LLM not available)")
        
        # Get requirements
        requirements = EmployeeLifecycleTools.get_asset_requirements(employee_id, db)
        
        if "error" in requirements:
            return {"success": False, "error": requirements["error"]}
        
        assignments = []
        failed_assignments = []
        
        # Assign each required asset type
        for req in requirements["assets_needed"]:
            device_type = req["type"]
            quantity = req["quantity"]
            
            # Find available assets
            available = EmployeeLifecycleTools.find_available_assets(device_type, quantity, db)
            
            if available["available_count"] < quantity:
                failed_assignments.append({
                    "device_type": device_type,
                    "required": quantity,
                    "available": available["available_count"],
                    "message": f"Insufficient {device_type}s: need {quantity}, found {available['available_count']}"
                })
            
            # Assign available assets
            for asset in available["assets"]:
                result = EmployeeLifecycleTools.assign_asset_to_employee(
                    employee_id,
                    asset["asset_id"],
                    db
                )
                
                if result["success"]:
                    assignments.append(result)
                else:
                    failed_assignments.append(result)
        
        # Get final summary
        summary = EmployeeLifecycleTools.get_assignment_summary(employee_id, db)
        
        return {
            "success": len(failed_assignments) == 0,
            "assignment_summary": summary,
            "assignments_completed": len(assignments),
            "failed_assignments": failed_assignments,
            "message": f"Asset assignment completed for employee {employee_id}. {len(assignments)} assets assigned, {len(failed_assignments)} failed."
        }
    
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
        self.db_session = db
        
        try:
            # Get employee assets
            employee_info = EmployeeLifecycleTools.get_employee_assets(employee_id, db)
            
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
            
            return_due_date = EmployeeLifecycleTools.calculate_return_due_date(resignation_date, return_days)
            
            # Schedule asset returns
            schedule_result = EmployeeLifecycleTools.schedule_asset_returns(
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
                manager_info = EmployeeLifecycleTools.get_manager_info(
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
            summary = EmployeeLifecycleTools.get_resignation_summary(employee_id, db)
            
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
    
    def _fallback_asset_assignment(self, employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Fallback deterministic asset assignment when LLM is not available
        """
        logger.info("Using fallback asset assignment (LLM not available)")
        
        # Get requirements
        requirements = EmployeeLifecycleTools.get_asset_requirements(employee_id, db)
        
        if "error" in requirements:
            return {"success": False, "error": requirements["error"]}
        
        assignments = []
        failed_assignments = []
        
        # Assign each required asset type
        for req in requirements["assets_needed"]:
            device_type = req["type"]
            quantity = req["quantity"]
            
            # Find available assets
            available = EmployeeLifecycleTools.find_available_assets(device_type, quantity, db)
            
            if available["available_count"] < quantity:
                failed_assignments.append({
                    "device_type": device_type,
                    "required": quantity,
                    "available": available["available_count"],
                    "message": f"Insufficient {device_type}s: need {quantity}, found {available['available_count']}"
                })
            
            # Assign available assets
            for asset in available["assets"]:
                result = EmployeeLifecycleTools.assign_asset_to_employee(
                    employee_id,
                    asset["asset_id"],
                    db
                )
                
                if result["success"]:
                    assignments.append(result)
                else:
                    failed_assignments.append(result)
        
        # Get final summary
        summary = EmployeeLifecycleTools.get_assignment_summary(employee_id, db)
        
        return {
            "success": len(failed_assignments) == 0,
            "assignment_summary": summary,
            "assignments_completed": len(assignments),
            "failed_assignments": failed_assignments,
            "message": f"Asset assignment completed for employee {employee_id}. "
                      f"{len(assignments)} assets assigned, {len(failed_assignments)} failed."
        }
    
    def track_asset_health(
        self,
        db: Session,
        age_threshold_years: int = 3
    ) -> Dict[str, Any]:
        """
        Track asset health and identify assets needing refresh/replacement
        
        Args:
            db: Database session
            age_threshold_years: Age threshold for marking assets for refresh
            
        Returns:
            Dictionary with asset health tracking results
        """
        
        logger.info(f"Tracking asset health with {age_threshold_years} year threshold")
        
        try:
            # Get assets for refresh
            refresh_result = EmployeeLifecycleTools.get_assets_for_refresh(
                db,
                age_threshold_years
            )
            
            # Get health summary
            health_summary = EmployeeLifecycleTools.get_asset_health_summary(db)
            
            return {
                "success": True,
                "message": f"Asset health tracking completed. Found {refresh_result['refresh_count']} assets for refresh.",
                "refresh_assets": refresh_result["assets_for_refresh"],
                "refresh_count": refresh_result["refresh_count"],
                "total_refresh_value": refresh_result["total_refresh_value"],
                "age_threshold_years": age_threshold_years,
                "health_summary": health_summary.get("health_summary", {}),
                "total_assets": refresh_result["total_assets"]
            }
        
        except Exception as e:
            logger.error(f"Error tracking asset health: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_asset_health_report(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get comprehensive asset health report
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with comprehensive health report
        """
        
        logger.info("Generating comprehensive asset health report")
        
        try:
            health_summary = EmployeeLifecycleTools.get_asset_health_summary(db)
            refresh_result = EmployeeLifecycleTools.get_assets_for_refresh(db, 3)
            
            # Categorize refresh assets by urgency
            urgent_assets = [a for a in refresh_result["assets_for_refresh"] if a["refresh_status"] == "URGENT"]
            recommended_assets = [a for a in refresh_result["assets_for_refresh"] if a["refresh_status"] == "RECOMMENDED"]
            
            return {
                "success": True,
                "report_date": datetime.now().isoformat(),
                "total_assets": health_summary["total_assets"],
                "health_metrics": health_summary.get("health_summary", {}),
                "refresh_summary": {
                    "total_for_refresh": refresh_result["refresh_count"],
                    "urgent_refresh": len(urgent_assets),
                    "recommended_refresh": len(recommended_assets),
                    "total_refresh_value": refresh_result["total_refresh_value"]
                },
                "urgent_assets": urgent_assets,
                "recommended_assets": recommended_assets
            }
        
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def predict_employee_churn(
        self,
        employee_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Predict churn risk for a specific employee
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with churn prediction results
        """
        
        logger.info(f"Predicting churn for employee {employee_id}")
        
        try:
            result = ChurnPredictionTools.predict_employee_churn(employee_id, db)
            return result
        
        except Exception as e:
            logger.error(f"Error predicting churn: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_high_risk_employees(
        self,
        db: Session,
        min_probability: float = 0.7
    ) -> Dict[str, Any]:
        """
        Get all employees with high churn risk
        
        Args:
            db: Database session
            min_probability: Minimum probability threshold
            
        Returns:
            Dictionary with high-risk employees
        """
        
        logger.info(f"Getting high risk employees (threshold: {min_probability})")
        
        try:
            result = ChurnPredictionTools.get_high_risk_employees(db, min_probability)
            return result
        
        except Exception as e:
            logger.error(f"Error getting high risk employees: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def predict_department_churn(
        self,
        department: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Predict churn for all employees in a specific department
        
        Args:
            department: Department name
            db: Database session
            
        Returns:
            Dictionary with department churn analysis
        """
        
        logger.info(f"Predicting churn for department: {department}")
        
        try:
            result = ChurnPredictionTools.predict_department_churn(department, db)
            return result
        
        except Exception as e:
            logger.error(f"Error predicting department churn: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_procurement_forecast(
        self,
        db: Session,
        forecast_months: int = 6,
        safety_stock_percent: float = 0.2
    ) -> Dict[str, Any]:
        """
        Get procurement forecast based on asset health and churn predictions
        
        Args:
            db: Database session
            forecast_months: Number of months to forecast
            safety_stock_percent: Safety stock buffer percentage
            
        Returns:
            Dictionary with procurement recommendations
        """
        
        logger.info(f"Generating procurement forecast for {forecast_months} months")
        
        try:
            result = ProcurementForecastingTools.get_procurement_recommendations(
                db, forecast_months, safety_stock_percent
            )
            return result
        
        except Exception as e:
            logger.error(f"Error generating procurement forecast: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_procurement_report(
        self,
        db: Session,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive procurement report
        
        Args:
            db: Database session
            include_details: Include detailed asset and employee information
            
        Returns:
            Dictionary with comprehensive procurement report
        """
        
        logger.info("Generating procurement report")
        
        try:
            result = ProcurementForecastingTools.get_procurement_report(
                db, include_details
            )
            return result
        
        except Exception as e:
            logger.error(f"Error generating procurement report: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_lifecycle_agent_instance = None


def get_employee_lifecycle_agent() -> EmployeeLifecycleAgent:
    """Get or create the singleton agent instance"""
    global _lifecycle_agent_instance
    if _lifecycle_agent_instance is None:
        _lifecycle_agent_instance = EmployeeLifecycleAgent()
    return _lifecycle_agent_instance


# Backward compatibility aliases
def get_asset_assignment_agent():
    """Backward compatibility alias for get_employee_lifecycle_agent"""
    return get_employee_lifecycle_agent()
