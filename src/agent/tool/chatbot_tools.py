"""
Unified chatbot tools for answering various HR and asset management questions
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from src.database.models import Employee, Asset
from src.agent.tool.churn_prediction_tools import ChurnPredictionTools
from src.agent.tool.tools import EmployeeLifecycleTools
from sentence_transformers import SentenceTransformer
import numpy as np


class UnifiedChatbotTools:
    """Tools for answering various chatbot questions"""
    
    # Class-level model and embeddings (loaded once)
    _model = None
    _category_embeddings = None
    _categories = None
    
    # Example questions for each category
    EXAMPLE_QUESTIONS = {
        "send_recovery_email": [
            "send email to employee 10",
            "send recovery email",
            "yes, send the email",
            "notify the employee",
            "please send email notification",
            "email him about asset return",
            "send asset return notification"
        ],
        "procurement_forecast": [
            "do we need to buy more assets?",
            "should we purchase more laptops?",
            "is there an asset shortage?",
            "what assets need to be procured?",
            "show procurement forecast",
            "do i need to buy more equipment?",
            "asset demand forecast"
        ],
        "asset_health": [
            "show asset health report",
            "what is the condition of our assets?",
            "show assets that need refresh",
            "asset health summary",
            "which assets are aging?",
            "asset condition report",
            "show asset age distribution"
        ],
        "asset_count": [
            "how many assets does employee 5 have?",
            "what assets are assigned to employee 10?",
            "list assets for employee 3",
            "show me employee 7's assets",
            "assets held by employee 12",
            "what equipment does employee 15 use?"
        ],
        "resignation_assets": [
            "if employee 5 resigns, what needs to be returned?",
            "what assets must employee 10 return?",
            "asset return for employee 20",
            "resignation asset analysis for employee 8",
            "which assets need to come back when employee 3 leaves?",
            "what equipment will employee 12 return?"
        ],
        "churn_prediction": [
            "what is the churn risk for employee 5?",
            "is employee 10 likely to resign?",
            "predict turnover for employee 3",
            "resignation probability for employee 7",
            "will employee 15 leave?",
            "churn analysis for employee 20"
        ],
        "churn_list": [
            "which employees are most likely to resign?",
            "show high-risk employees",
            "who might leave the company?",
            "list employees at risk of turnover",
            "which staff are likely to quit?",
            "show me employees with high churn risk"
        ],
        "churn_department": [
            "which IT employees are at risk of leaving?",
            "show churn risk in marketing department",
            "who in IT might resign?",
            "high-risk employees in marketing",
            "turnover analysis for IT department",
            "resignation risk in the marketing team"
        ],
        "assign_asset": [
            "what assets can be assigned to new employee?",
            "which assets are available for employee 5?",
            "show available assets for new hire",
            "what equipment can I assign to employee 10?",
            "available assets for onboarding employee 3",
            "which assets can be given to employee 7?",
            "what can I assign to new employee 15?",
            "his role is developer and he is in IT department",
            "she is a marketing manager",
            "IT developer role"
        ]
    }
    
    @classmethod
    def _load_model(cls):
        """Load the sentence transformer model and compute category embeddings"""
        if cls._model is None:
            # Use a small, fast model optimized for semantic similarity
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Prepare category examples
            cls._categories = []
            category_texts = []
            
            for category, examples in cls.EXAMPLE_QUESTIONS.items():
                cls._categories.append(category)
                # Combine all examples for this category into one representative text
                category_texts.append(" | ".join(examples))
            
            # Compute embeddings for all categories
            cls._category_embeddings = cls._model.encode(category_texts, convert_to_tensor=False)
        
        return cls._model
    
    @classmethod
    def classify_question_with_ml(cls, question: str, threshold: float = 0.4) -> Tuple[str, float]:
        """
        Classify question using sentence embeddings and cosine similarity
        
        Args:
            question: User's question
            threshold: Minimum similarity score to accept classification (default 0.4)
            
        Returns:
            Tuple of (question_type, confidence_score)
        """
        # Load model if not already loaded
        cls._load_model()
        
        # Encode the question
        question_embedding = cls._model.encode([question], convert_to_tensor=False)[0]
        
        # Compute cosine similarity with all categories
        similarities = []
        for cat_embedding in cls._category_embeddings:
            similarity = np.dot(question_embedding, cat_embedding) / (
                np.linalg.norm(question_embedding) * np.linalg.norm(cat_embedding)
            )
            similarities.append(similarity)
        
        # Find the best match
        max_similarity = max(similarities)
        best_category_idx = similarities.index(max_similarity)
        best_category = cls._categories[best_category_idx]
        
        # If similarity is too low, return 'general'
        if max_similarity < threshold:
            return "general", max_similarity
        
        return best_category, max_similarity
    
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
    def get_available_assets_for_new_employee(
        employee_id: Optional[int] = None, 
        db: Session = None,
        role: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get available assets that can be assigned to a new employee based on their role
        
        Args:
            employee_id: Employee ID (optional if role and department provided)
            db: Database session
            role: Employee role (optional if employee_id provided)
            department: Employee department (optional if employee_id provided)
            
        Returns:
            Dictionary with available assets organized by requirements
        """
        try:
            from src.agent.tool.tools import EmployeeLifecycleTools
            
            employee_name = "New Employee"
            employee_dept = department
            employee_role = role
            emp_id = employee_id
            
            # Get employee info from database if employee_id is provided
            if employee_id:
                employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
                
                if employee:
                    employee_name = employee.full_name
                    employee_dept = employee.department
                    employee_role = employee.role
                    emp_id = employee.employee_id
            
            # Check if we have required information
            if not employee_dept or not employee_role:
                return {
                    "success": False,
                    "needs_info": True,
                    "missing_fields": {
                        "role": not employee_role,
                        "department": not employee_dept
                    },
                    "message": "To determine asset requirements, please provide the employee's role and department."
                }
            
            # Build a temporary employee-like structure for requirements
            # We'll directly calculate requirements instead of using get_asset_requirements
            # to avoid needing an actual employee record
            
            assets_needed = []
            
            # IT employees: 1 laptop + 2 monitors
            if employee_dept.lower() == "it":
                assets_needed = [
                    {"type": "laptop", "quantity": 1, "priority": 1},
                    {"type": "monitor", "quantity": 2, "priority": 2}
                ]
            # Marketing employees: 1 laptop + 1 monitor
            elif employee_dept.lower() == "marketing":
                assets_needed = [
                    {"type": "laptop", "quantity": 1, "priority": 1},
                    {"type": "monitor", "quantity": 1, "priority": 2}
                ]
            
            # Managers get an additional phone
            if employee_role.lower() == "manager":
                assets_needed.append(
                    {"type": "phone", "quantity": 1, "priority": 3}
                )
            
            # Find available assets for each requirement
            available_assets = []
            total_available = 0
            total_needed = 0
            
            for req in assets_needed:
                device_type = req["type"]
                quantity = req["quantity"]
                priority = req["priority"]
                total_needed += quantity
                
                # Find available assets of this type
                assets_result = EmployeeLifecycleTools.find_available_assets(
                    device_type, quantity, db
                )
                
                available_count = assets_result["available_count"]
                total_available += available_count
                
                available_assets.append({
                    "device_type": device_type,
                    "required_quantity": quantity,
                    "available_quantity": available_count,
                    "priority": priority,
                    "sufficient": available_count >= quantity,
                    "assets": assets_result["assets"]
                })
            
            return {
                "success": True,
                "employee_id": emp_id,
                "employee_name": employee_name,
                "department": employee_dept,
                "role": employee_role,
                "total_needed": total_needed,
                "total_available": total_available,
                "can_fully_equip": total_available >= total_needed,
                "requirements": assets_needed,
                "available_assets": available_assets
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error retrieving available assets: {str(e)}"
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
    def extract_role_and_department(question: str) -> Dict[str, Optional[str]]:
        """
        Extract role and department from question text
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with role and department (None if not found)
        """
        import re
        
        question_lower = question.lower()
        
        # Extract department
        department = None
        if any(word in question_lower for word in ["it department", "in it", "it team", "it employee"]):
            department = "it"
        elif any(word in question_lower for word in ["marketing department", "in marketing", "marketing team", "marketing employee"]):
            department = "marketing"
        
        # Extract role
        role = None
        if any(word in question_lower for word in ["manager", "team lead", "head of"]):
            role = "manager"
        elif any(word in question_lower for word in ["developer", "engineer", "programmer", "software engineer"]):
            role = "developer"
        elif any(word in question_lower for word in ["specialist", "analyst", "coordinator", "staff"]):
            role = "specialist"
        
        return {
            "role": role,
            "department": department
        }
    
    @classmethod
    def classify_question_type(
        cls, 
        question: str, 
        use_ml: bool = True, 
        ml_threshold: float = 0.4,
        previous_question_type: Optional[str] = None
    ) -> str:
        """
        Classify the type of question being asked using ML or keyword fallback
        
        Args:
            question: User's question
            use_ml: Whether to use ML-based classification (default True)
            ml_threshold: Minimum confidence threshold for ML classification (default 0.4)
            previous_question_type: The question type from previous conversation turn (for context)
            
        Returns:
            Question type: 'asset_count', 'resignation_assets', 'churn_prediction', 
                          'churn_list', 'churn_department', 'asset_health', 
                          'procurement_forecast', 'send_recovery_email', 'assign_asset', or 'general'
        """
        # Debug logging
        print(f"[Classification] Question: '{question}'")
        print(f"[Classification] Previous question type: {previous_question_type}")
        
        # Check if this is a follow-up providing missing information
        # If previous question was assign_asset and current question provides role/dept info,
        # and doesn't clearly indicate a different topic, maintain assign_asset context
        if previous_question_type == 'assign_asset':
            question_lower = question.lower()
            
            # Check if this looks like a response providing role/department info
            # Check for explicit role/dept statements
            has_explicit_info = any(phrase in question_lower for phrase in [
                'role is', 'department is', 'position is', 'job is',
                'he is a', 'she is a', 'he is an', 'she is an',
                'they are a', 'they are an'
            ])
            
            # Check for department indicators
            has_department = any(dept in question_lower for dept in [
                'in it', 'in marketing', 'it department', 'marketing department',
                'it team', 'marketing team', 'from it', 'from marketing'
            ])
            
            # Check for role indicators
            has_role = any(role in question_lower for role in [
                'developer', 'manager', 'specialist', 'engineer', 'staff',
                'analyst', 'coordinator', 'programmer', 'team lead',
                'head of', 'software engineer'
            ])
            
            # Check if it's clearly NOT about a different topic
            is_clearly_different_topic = any(keyword in question_lower for keyword in [
                'churn', 'resign', 'quit', 'leave', 'turnover', 'attrition',
                'how many asset', 'asset count', 'procurement', 'buy',
                'asset health', 'send email', 'recovery', 'return',
                'what assets does', 'list assets', 'show assets'
            ])
            
            # If providing role/dept info and not clearly a different topic, stay with assign_asset
            has_role_dept_info = has_explicit_info or (has_department and has_role) or (has_department or has_role)
            
            if has_role_dept_info and not is_clearly_different_topic:
                print(f"[Context-Aware Classification] Maintaining assign_asset context from previous turn")
                print(f"[Context-Aware Classification] Detected - Explicit: {has_explicit_info}, Dept: {has_department}, Role: {has_role}")
                return 'assign_asset'
        # Try ML-based classification first
        if use_ml:
            try:
                question_type, confidence = cls.classify_question_with_ml(question, threshold=ml_threshold)
                
                # If confidence is good, return the result
                if confidence >= ml_threshold:
                    print(f"[ML Classification] Type: {question_type}, Confidence: {confidence:.3f}")
                    return question_type
                else:
                    print(f"[ML Classification] Low confidence ({confidence:.3f}), falling back to keyword matching")
            except Exception as e:
                print(f"[ML Classification] Error: {e}, falling back to keyword matching")
        
        # Fallback to keyword-based classification
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
        
        # Asset assignment for new employees
        if any(keyword in question_lower for keyword in [
            "assign asset", "available asset", "can be assigned", "what can i assign",
            "which assets available", "assets for new employee", "onboard", "new hire",
            "available for employee", "can assign to", "what equipment available",
            "available equipment"
        ]):
            return "assign_asset"
        
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
    
    @classmethod
    def extract_employee_id_with_ml(cls, question: str, use_ml: bool = True, confidence_threshold: float = 0.6) -> int:
        """
        Extract employee ID using ML-based context understanding
        
        Args:
            question: User's question
            use_ml: Whether to use ML validation (default True)
            confidence_threshold: Minimum confidence for ML validation (default 0.6)
            
        Returns:
            Employee ID if found, None otherwise
        """
        import re
        
        # Step 1: Find all numbers in the question
        all_numbers = re.findall(r'\b(\d+)\b', question)
        
        if not all_numbers:
            return None
        
        # Step 2: Try regex patterns first (high precision)
        regex_result = cls._extract_employee_id_regex(question)
        if regex_result is not None:
            return regex_result
        
        # Step 3: If regex fails and ML is enabled, use context-based validation
        if use_ml and len(all_numbers) > 0:
            try:
                cls._load_model()
                
                # Example phrases that indicate employee ID context
                employee_context_phrases = [
                    "employee {num}",
                    "employee with ID {num}",
                    "employee ID {num}",
                    "emp {num}",
                    "staff member {num}",
                    "worker {num}"
                ]
                
                # Compute embedding for the original question
                question_embedding = cls._model.encode([question], convert_to_tensor=False)[0]
                
                best_number = None
                best_score = 0
                
                # Check each number in context
                for number in all_numbers:
                    # Create context variants with this number
                    context_variants = [phrase.format(num=number) for phrase in employee_context_phrases]
                    
                    # Compute embeddings for all variants
                    variant_embeddings = cls._model.encode(context_variants, convert_to_tensor=False)
                    
                    # Find max similarity across all variants
                    max_similarity = 0
                    for variant_emb in variant_embeddings:
                        similarity = np.dot(question_embedding, variant_emb) / (
                            np.linalg.norm(question_embedding) * np.linalg.norm(variant_emb)
                        )
                        max_similarity = max(max_similarity, similarity)
                    
                    # Track the best matching number
                    if max_similarity > best_score:
                        best_score = max_similarity
                        best_number = number
                
                # If confidence is high enough, return the number
                if best_score >= confidence_threshold and best_number:
                    print(f"[ML ID Extraction] Extracted ID: {best_number}, Confidence: {best_score:.3f}")
                    return int(best_number)
                else:
                    print(f"[ML ID Extraction] Low confidence ({best_score:.3f}), no ID extracted")
                    
            except Exception as e:
                print(f"[ML ID Extraction] Error: {e}, falling back to regex")
        
        return None
    
    @staticmethod
    def _extract_employee_id_regex(question: str) -> int:
        """
        Extract employee ID using regex patterns (fallback method)
        
        Args:
            question: User's question
            
        Returns:
            Employee ID if found, None otherwise
        """
        import re
        
        # Comprehensive regex patterns ordered by specificity
        patterns = [
            # "employee with ID number 50", "employee with id 50"
            r'employee\s+with\s+(?:id|ID)\s+(?:number\s+)?(\d+)',
            
            # "employee ID number 50", "employee id number 50"
            r'employee\s+(?:id|ID)\s+(?:number\s+)?(\d+)',
            
            # "employee number 50", "employee no 50", "employee no. 50"
            r'employee\s+(?:number|no\.?|num\.?)\s+(\d+)',
            
            # "employee 5", "employee #5"
            r'employee\s+#?(\d+)',
            
            # "emp with ID 50", "emp ID 50"
            r'emp(?:loyee)?\s+(?:with\s+)?(?:id|ID)\s+(?:number\s+)?(\d+)',
            
            # "emp 5", "emp #5"
            r'emp\s+#?(\d+)',
            
            # "ID number 50", "id number 50"
            r'(?:id|ID)\s+(?:number|num|no\.?)\s+(\d+)',
            
            # "ID 50", "id 50" (only if followed by space or end to avoid matching random "id")
            r'(?:^|\s)(?:id|ID)\s+(\d+)(?:\s|$)',
            
            # "#50" (standalone)
            r'#(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    @classmethod
    def extract_employee_id(cls, question: str, use_ml: bool = True) -> int:
        """
        Extract employee ID from question text (wrapper method for backward compatibility)
        
        Args:
            question: User's question
            use_ml: Whether to use ML-based extraction (default True)
            
        Returns:
            Employee ID if found, None otherwise
        """
        return cls.extract_employee_id_with_ml(question, use_ml=use_ml)
    
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
