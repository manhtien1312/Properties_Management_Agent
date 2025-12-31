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
    question: str = Query(..., description="Your question about churn prediction"),
    employee_id: int = Query(None, description="Optional employee ID for context"),
    db: Session = Depends(get_db)
):
    """
    Conversational chatbot for churn prediction questions
    
    Query Parameters:
    - question: Your question (required)
    - employee_id: Optional employee ID for context-specific answers
    
    Examples:
    - "What is the churn risk for employee 5?"
    - "Why might employee 10 be at risk of leaving?"
    - "Which employees are most likely to resign?"
    - "What can we do to reduce churn?"
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config import settings
        
        # Get context if employee_id provided
        context_data = None
        if employee_id:
            result = ChurnPredictionTools.predict_employee_churn(employee_id, db)
            if result.get('success'):
                context_data = result
        
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
        
        # Build prompt
        system_prompt = f"""You are an HR Analytics AI Assistant specialized in employee churn prediction.

You have access to a trained XGBoost model that predicts whether an employee will resign within 6 months.

Model Features:
- tenure_months, months_since_last_promotion, salary_change_percent_1y
- performance_rating_avg, performance_rating_trend
- sick_days_ytd, unplanned_leaves_ytd
- engagement_score_latest, engagement_score_trend
- manager_changes, department_changes
- training_hours_ytd, overtime_hours_avg
- remote_work_percent, project_count, reports_count

Risk Categories:
- High (70%+): Immediate intervention needed
- Medium (40-70%): Monitor closely, consider retention actions
- Low (<40%): No immediate concern

"""
        
        if context_data:
            system_prompt += f"""
Current Employee Context:
- Employee: {context_data.get('employee_name')}
- Churn Probability: {context_data.get('probability')*100:.1f}%
- Risk Category: {context_data.get('risk_category')}
- Top Risk Factors: {', '.join([f['feature'] for f in context_data.get('top_factors', [])[:3]])}
"""
        
        user_message = f"{system_prompt}\n\nUser Question: {question}\n\nProvide a helpful, actionable answer:"
        
        # Get response from LLM
        response = llm.invoke(user_message)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "success": True,
            "question": question,
            "answer": answer,
            "context": {
                "employee_id": employee_id,
                "has_prediction_data": context_data is not None
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
