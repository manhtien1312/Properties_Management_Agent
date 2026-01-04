"""
Churn Prediction API Endpoints
Provides employee churn risk assessment and predictions
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from src.database.database import get_db
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
from src.agent.tool.churn_prediction_tools import ChurnPredictionTools

router = APIRouter(prefix="/api/churn", tags=["churn-prediction"])


@router.get("/predict/{employee_id}", response_model=dict)
def predict_employee_churn(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Predict churn risk for a specific employee
    
    Returns:
    - Probability score (0.0 to 1.0)
    - Risk category (High/Medium/Low)
    - Top contributing factors
    - Feature importance
    """
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.predict_employee_churn(employee_id, db)
        
        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error', 'Prediction failed'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-risk", response_model=dict)
def get_high_risk_employees(
    min_probability: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Get all employees with high churn risk
    
    Query Parameters:
    - min_probability: Minimum probability threshold (default 0.7)
    
    Returns list of high-risk employees with their churn probabilities
    """
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.get_high_risk_employees(db, min_probability)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to get high-risk employees'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info", response_model=dict)
def get_model_info():
    """
    Get information about the churn prediction model
    
    Returns:
    - Model type and version
    - Training metrics
    - Feature list
    - Feature importance
    """
    try:
        if not ChurnPredictionTools.load_model():
            raise HTTPException(status_code=503, detail="Model not available")
        
        metadata = ChurnPredictionTools._metadata
        
        return {
            "success": True,
            "model_type": metadata.get('model_type'),
            "model_version": metadata.get('model_version'),
            "trained_date": metadata.get('trained_date'),
            "n_features": metadata.get('n_features'),
            "feature_names": metadata.get('feature_names'),
            "metrics": metadata.get('metrics'),
            "top_features": list(metadata.get('feature_importance', {}).items())[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-predict", response_model=dict)
def batch_predict_churn(
    employee_ids: list[int],
    db: Session = Depends(get_db)
):
    """
    Predict churn risk for multiple employees
    
    Request body:
    - employee_ids: List of employee IDs
    
    Returns predictions for all specified employees
    """
    try:
        results = []
        
        for emp_id in employee_ids:
            try:
                result = ChurnPredictionTools.predict_employee_churn(emp_id, db)
                if result.get('success'):
                    results.append({
                        'employee_id': emp_id,
                        'employee_name': result.get('employee_name'),
                        'probability': result.get('probability'),
                        'risk_category': result.get('risk_category')
                    })
            except:
                continue
        
        return {
            "success": True,
            "requested": len(employee_ids),
            "predictions_made": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatbot", response_model=dict)
def churn_chatbot(
    question: str = Query(..., description="Your question about employees, assets, or churn prediction"),
    employee_id: int = Query(None, description="Optional employee ID for context"),
    db: Session = Depends(get_db)
):
    """
    Unified conversational chatbot for HR and asset management questions
    
    Query Parameters:
    - question: Your question (required)
    - employee_id: Optional employee ID for context-specific answers
    
    Examples:
    - "How many assets is employee 5 currently using?"
    - "If employee 10 resigns, what assets must be returned and do they need refresh?"
    - "What is the churn risk for employee 5?"
    - "Which employees are most likely to resign?"
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config import settings
        from src.agent.tool.chatbot_tools import UnifiedChatbotTools
        
        # Classify question type
        question_type = UnifiedChatbotTools.classify_question_type(question)
        
        # Extract employee_id from question if not provided
        if not employee_id:
            employee_id = UnifiedChatbotTools.extract_employee_id(question)
        
        # Extract department if question is department-specific
        department = UnifiedChatbotTools.extract_department(question)
        
        # Get context based on question type
        context_data = None
        if question_type == "churn_list":
            # Get all high-risk employees
            context_data = ChurnPredictionTools.get_high_risk_employees(db, min_probability=0.7)
        elif question_type == "churn_department" and department:
            # Get churn predictions for specific department
            context_data = ChurnPredictionTools.predict_department_churn(department, db)
        elif employee_id:
            if question_type == "asset_count":
                context_data = UnifiedChatbotTools.get_employee_asset_count(employee_id, db)
            elif question_type == "resignation_assets":
                context_data = UnifiedChatbotTools.get_resignation_assets_info(employee_id, db)
            elif question_type == "churn_prediction":
                # Call the churn prediction tool
                context_data = ChurnPredictionTools.predict_employee_churn(employee_id, db)
        
        # If churn prediction but no employee_id, explain
        if question_type == "churn_prediction" and not employee_id:
            return {
                "success": False,
                "error": "Employee ID required for churn prediction",
                "answer": "To predict churn risk, please provide an employee ID. For example: 'What is the churn risk for employee 5?'"
            }
        
        # If department churn but no department found, explain
        if question_type == "churn_department" and not department:
            return {
                "success": False,
                "error": "Department not specified",
                "answer": "Please specify a department (IT or Marketing). For example: 'Which employees are most likely to resign in the IT department?'"
            }
        
        # Initialize LLM
        if not settings.google_api_key:
            return {
                "success": False,
                "error": "Chatbot unavailable - Google API key not configured",
                "answer": "I'm sorry, but the AI chatbot is not configured. Please provide predictions directly via the /predict endpoint."
            }
        
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.7
        )
        
        # Build prompt based on question type
        system_prompt = """You are an HR Analytics and Asset Management AI Assistant with DIRECT ACCESS to the company's employee and asset management database.

IMPORTANT INSTRUCTIONS:
- You have ALREADY QUERIED the database - the data is provided below
- DO NOT say you need to "check the system" or "access the database" 
- DO NOT say you need permissions or data access
- PROVIDE SPECIFIC, CONCRETE ANSWERS using the data given
- Answer questions directly and factually based on the retrieved data
- If no data is provided, only then say the employee was not found

You can help with:
1. Employee Asset Management - Track assets assigned to employees
2. Asset Health & Refresh - Determine if returned assets need replacement (>3 years old)
3. Churn Prediction - Predict employee turnover risk using ML

"""
        
        if question_type == "asset_count" and context_data:
            if context_data.get('success'):
                system_prompt += f"""
=== DATABASE QUERY RESULTS (ALREADY RETRIEVED) ===

Employee Information:
- Name: {context_data.get('employee_name')}
- ID: {context_data.get('employee_id')}
- Department: {context_data.get('department')}
- Email: {context_data.get('employee_email')}

ASSET ASSIGNMENT SUMMARY:
- Total Assets Currently Assigned: {context_data.get('total_assets')}
- Asset Count by Type: {context_data.get('count_by_type')}
- Total Asset Value: ${context_data.get('total_asset_value', 0):,.2f}

DETAILED ASSET LIST:
"""
                for device_type, items in context_data.get('assets_by_type', {}).items():
                    system_prompt += f"\n{device_type.upper()} ({len(items)} item{'s' if len(items) != 1 else ''}):\n"
                    for item in items:
                        system_prompt += f"  - Asset Tag: {item['asset_tag']}\n"
                        system_prompt += f"    Brand/Model: {item['brand']} {item['model']}\n"
                        system_prompt += f"    Condition: {item['condition']}\n"
                        system_prompt += f"    Value: ${item['current_value']:,.2f}\n"
            else:
                system_prompt += f"\nERROR: {context_data.get('error')}\n"
        
        elif question_type == "resignation_assets" and context_data:
            if context_data.get('success'):
                system_prompt += f"""
=== DATABASE QUERY RESULTS (ALREADY RETRIEVED) ===

Employee Information:
- Name: {context_data.get('employee_name')}
- ID: {context_data.get('employee_id')}
- Department: {context_data.get('department')}
- Email: {context_data.get('employee_email')}
- Employment Status: {context_data.get('employment_status', 'active')}

RESIGNATION & ASSET RETURN ANALYSIS:
- Total Assets to Return: {context_data.get('total_assets_to_return')}
- Assets Needing Refresh (>3 years old): {context_data.get('assets_need_refresh')}
- Assets OK to Reassign: {context_data.get('assets_ok_to_reassign')}
- Total Asset Value: ${context_data.get('total_asset_value', 0):,.2f}

BREAKDOWN BY DEVICE TYPE:
"""
                for device_type, stats in context_data.get('summary_by_type', {}).items():
                    system_prompt += f"\n{device_type.upper()}:\n"
                    system_prompt += f"  - Total to return: {stats['total']}\n"
                    system_prompt += f"  - Need refresh (>3 years): {stats['needs_refresh']}\n"
                    system_prompt += f"  - OK to reassign (<3 years): {stats['ok_to_reassign']}\n"
                
                system_prompt += f"\nRECOMMENDATION:\n{context_data.get('recommendation', '')}\n"
                
                # Add detailed asset list
                system_prompt += "\nDETAILED ASSET LIST:\n"
                for asset in context_data.get('assets', [])[:10]:  # First 10 assets
                    system_prompt += f"\n- {asset['asset_tag']} ({asset['device_type']})\n"
                    system_prompt += f"  Brand/Model: {asset['brand']} {asset['model']}\n"
                    system_prompt += f"  Age: {asset['age_years']} years\n"
                    system_prompt += f"  Condition: {asset['condition']}\n"
                    system_prompt += f"  Refresh Status: {asset['refresh_status']}\n"
                    system_prompt += f"  Reason: {asset['refresh_reason']}\n"
            else:
                system_prompt += f"\nERROR: {context_data.get('error')}\n"
        
        elif question_type == "churn_prediction" and context_data:
            if context_data.get('success'):
                system_prompt += f"""
=== DATABASE QUERY RESULTS (ALREADY RETRIEVED) ===

CHURN PREDICTION ANALYSIS:
Model: XGBoost Binary Classifier (79% accuracy)
Prediction Window: Next 6 months

Employee Information:
- Name: {context_data.get('employee_name')}
- ID: {context_data.get('employee_id')}

PREDICTION RESULTS:
- Churn Probability: {context_data.get('probability', 0)*100:.1f}%
- Risk Category: {context_data.get('risk_category')}
- Prediction: {'WILL LIKELY RESIGN' if context_data.get('prediction') == 1 else 'LIKELY TO STAY'}

TOP RISK FACTORS:
"""
                for i, factor in enumerate(context_data.get('top_factors', [])[:5], 1):
                    system_prompt += f"{i}. {factor.get('feature', 'N/A')}: {factor.get('value', 'N/A')}\n"
                
                system_prompt += f"""
RISK LEVEL INTERPRETATION:
- HIGH (70%+): Immediate intervention needed - schedule 1-on-1, discuss retention
- MEDIUM (40-70%): Monitor closely, consider retention actions  
- LOW (<40%): No immediate concern

ACTIONABLE RECOMMENDATIONS:
"""
                if context_data.get('probability', 0) >= 0.7:
                    system_prompt += "- URGENT: Schedule immediate 1-on-1 meeting\n"
                    system_prompt += "- Review compensation and career development\n"
                    system_prompt += "- Address work-life balance concerns\n"
                elif context_data.get('probability', 0) >= 0.4:
                    system_prompt += "- Monitor employee engagement closely\n"
                    system_prompt += "- Schedule regular check-ins\n"
                    system_prompt += "- Consider retention strategies\n"
                else:
                    system_prompt += "- Continue standard engagement practices\n"
                    system_prompt += "- Maintain positive work environment\n"
            else:
                # Handle error case
                error_msg = context_data.get('error', 'Unknown error')
                system_prompt += f"""
=== ERROR ===
Unable to predict churn for employee {employee_id}: {error_msg}

Possible reasons:
- Employee not found in database
- Insufficient HR analytics data
- Employee may not be active

Please verify the employee ID and try again.
"""
        
        elif question_type == "churn_list" and context_data:
            if context_data.get('success'):
                high_risk_employees = context_data.get('high_risk_employees', [])
                system_prompt += f"""
=== DATABASE QUERY RESULTS (ALREADY RETRIEVED) ===

HIGH-RISK EMPLOYEE LIST:
Analysis: All active employees analyzed for churn risk
Threshold: {context_data.get('threshold', 0.7)*100:.0f}% probability
Total Employees Analyzed: {context_data.get('total_employees', 0)}
High-Risk Employees Found: {context_data.get('high_risk_count', 0)}

EMPLOYEES MOST LIKELY TO RESIGN:
"""
                if high_risk_employees:
                    for i, emp in enumerate(high_risk_employees[:15], 1):  # Top 15
                        system_prompt += f"\n{i}. {emp['employee_name']} (ID: {emp['employee_id']})\n"
                        system_prompt += f"   - Churn Probability: {emp['probability']*100:.1f}%\n"
                        system_prompt += f"   - Risk Category: {emp['risk_category']}\n"
                        if emp.get('top_factor'):
                            system_prompt += f"   - Top Risk Factor: {emp['top_factor'].get('feature', 'N/A')}\n"
                else:
                    system_prompt += "\nNo high-risk employees found. All employees appear stable.\n"
                
                system_prompt += f"""
SUMMARY:
- Total analyzed: {context_data.get('total_employees', 0)} active employees
- High risk (≥70%): {context_data.get('high_risk_count', 0)} employees
- Percentage at risk: {(context_data.get('high_risk_count', 0) / max(context_data.get('total_employees', 1), 1))*100:.1f}%

RECOMMENDED ACTIONS:
- Immediate interventions for employees with >80% probability
- Regular check-ins for employees with 70-80% probability
- Review retention strategies and employee engagement programs
"""
            else:
                system_prompt += f"\nERROR: {context_data.get('error')}\n"
        
        elif question_type == "churn_department" and context_data:
            if context_data.get('success'):
                predictions = context_data.get('predictions', [])
                system_prompt += f"""
=== DATABASE QUERY RESULTS (ALREADY RETRIEVED) ===

DEPARTMENT CHURN ANALYSIS:
Department: {context_data.get('department', 'Unknown').upper()}
Total Employees: {context_data.get('total_employees', 0)}
Average Churn Probability: {context_data.get('average_probability', 0)*100:.1f}%

RISK BREAKDOWN:
- High Risk (≥70%): {context_data.get('high_risk_count', 0)} employees
- Medium Risk (40-70%): {context_data.get('medium_risk_count', 0)} employees
- Low Risk (<40%): {context_data.get('low_risk_count', 0)} employees

HIGH-RISK EMPLOYEES IN THIS DEPARTMENT:
"""
                # Show high-risk employees
                high_risk = [p for p in predictions if p.get('probability', 0) >= 0.7]
                if high_risk:
                    for i, emp in enumerate(high_risk[:10], 1):  # Top 10
                        system_prompt += f"\n{i}. {emp['employee_name']} (ID: {emp['employee_id']})\n"
                        system_prompt += f"   - Probability: {emp['probability']*100:.1f}%\n"
                        system_prompt += f"   - Risk: {emp['risk_category']}\n"
                else:
                    system_prompt += "\nNo high-risk employees in this department.\n"
                
                system_prompt += f"""
DEPARTMENT INSIGHTS:
{context_data.get('department_insights', 'Analysis complete.')}

RECOMMENDED ACTIONS:
- Focus retention efforts on high-risk employees listed above
- Review department-wide engagement and satisfaction
- Address common risk factors across the team
"""
            else:
                system_prompt += f"\nERROR: {context_data.get('error')}\n"
        
        user_message = f"""{system_prompt}

=== USER QUESTION ===
{question}

=== INSTRUCTIONS ===
Based on the database query results provided above, answer the user's question directly and specifically.
DO NOT say you need to check anything - you already have all the data.
Provide concrete numbers, names, and details from the retrieved data.
Be helpful and actionable in your response.

Your answer:"""
        
        # Get response from LLM
        response = llm.invoke(user_message)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "success": True,
            "question": question,
            "question_type": question_type,
            "answer": answer,
            "context": {
                "employee_id": employee_id,
                "has_context_data": context_data is not None,
                "data": context_data
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "answer": f"I encountered an error: {str(e)}"
        }


@router.get("/department/{department}")
async def predict_department_churn(
    department: str,
    db: Session = Depends(get_db)
):
    """
    Predict churn for all employees in a specific department
    
    Args:
        department: Department name (e.g., 'IT', 'Marketing', 'Engineering')
    
    Returns:
        Department-level churn analysis with predictions for all employees
    
    Example:
        GET /api/churn/department/Engineering
        
        Response:
        {
            "success": true,
            "department": "Engineering",
            "total_employees": 25,
            "average_churn_probability": 0.423,
            "risk_summary": {
                "high_risk": 3,
                "medium_risk": 8,
                "low_risk": 14
            },
            "common_risk_factors": [
                {
                    "feature": "engagement_score_latest",
                    "affected_employees": 15,
                    "avg_importance": 0.18
                }
            ],
            "predictions": [...]
        }
    """
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.predict_department_churn(department, db)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
