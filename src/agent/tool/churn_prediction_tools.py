"""
Churn Prediction Tools for Employee Lifecycle Agent
Provides ML-based predictions for employee resignation risk
"""

import pickle
import json
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.database.models import Employee, HRAnalytic
from datetime import datetime, timedelta


class ChurnPredictionTools:
    """Tools for employee churn prediction"""
    
    MODEL_PATH = 'src/ml/churn_model.pkl'
    METADATA_PATH = 'src/ml/churn_model_metadata.json'
    
    _model = None
    _metadata = None
    
    @classmethod
    def load_model(cls):
        """Load trained churn prediction model"""
        if cls._model is None:
            try:
                with open(cls.MODEL_PATH, 'rb') as f:
                    cls._model = pickle.load(f)
                
                with open(cls.METADATA_PATH, 'r') as f:
                    cls._metadata = json.load(f)
                
                print(f"✓ Churn model loaded: {cls._metadata.get('model_type')}")
            except FileNotFoundError:
                print("⚠ Churn model not found. Run training script first.")
                return False
        
        return True
    
    @classmethod
    def extract_employee_features(cls, employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Extract features for an employee from database
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Dictionary with features and metadata
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        if not employee:
            return {"error": f"Employee {employee_id} not found"}
        
        # Get HR analytics data for this employee
        hr_records = db.query(HRAnalytic).filter(
            HRAnalytic.employee_id == employee_id
        ).order_by(HRAnalytic.record_date.desc()).limit(24).all()  # Last 2 years
        
        if not hr_records:
            return {"error": f"No HR analytics data found for employee {employee_id}"}
        
        # Calculate features from HR data
        latest_record = hr_records[0]
        
        # Performance ratings (last 2 years)
        perf_ratings = [r.performance_rating for r in hr_records if r.performance_rating]
        performance_rating_avg = np.mean(perf_ratings) if perf_ratings else 3.0
        
        # Performance trend
        if len(perf_ratings) >= 2:
            performance_rating_trend = perf_ratings[0] - perf_ratings[-1]
        else:
            performance_rating_trend = 0.0
        
        # Engagement scores
        eng_scores = [r.engagement_score for r in hr_records if r.engagement_score]
        engagement_score_latest = eng_scores[0] if eng_scores else 3.0
        
        # Engagement trend
        if len(eng_scores) >= 2:
            engagement_score_trend = eng_scores[0] - eng_scores[-1]
        else:
            engagement_score_trend = 0.0
        
        # Manager and department changes (last 2 years)
        manager_changes = sum(1 for r in hr_records if r.manager_changes) or 0
        department_changes = sum(1 for r in hr_records if r.department_changes) or 0
        
        # Calculate salary change (last year)
        salary_changes = [r.salary_change_percent for r in hr_records[:12] if r.salary_change_percent]
        salary_change_percent_1y = np.mean(salary_changes) if salary_changes else 5.0
        
        # Overtime average
        overtime_values = [r.overtime_hours for r in hr_records if r.overtime_hours]
        overtime_hours_avg = np.mean(overtime_values) if overtime_values else 10.0
        
        # Build feature dictionary
        features = {
            'tenure_months': employee.tenure_months or 12,
            'months_since_last_promotion': latest_record.months_since_last_promotion or 12,
            'salary_change_percent_1y': salary_change_percent_1y,
            'performance_rating_avg': performance_rating_avg,
            'performance_rating_trend': performance_rating_trend,
            'sick_days_ytd': latest_record.sick_days_ytd or 5,
            'unplanned_leaves_ytd': latest_record.unplanned_leaves or 2,
            'engagement_score_latest': engagement_score_latest,
            'engagement_score_trend': engagement_score_trend,
            'manager_changes': manager_changes,
            'department_changes': department_changes,
            'training_hours_ytd': latest_record.training_hours or 40,
            'overtime_hours_avg': overtime_hours_avg,
            'remote_work_percent': latest_record.remote_work_percent or 50.0,
            'project_count': latest_record.project_count or 3,
            'reports_count': 0  # TODO: Calculate from employee hierarchy
        }
        
        return {
            'success': True,
            'employee_id': employee_id,
            'employee_name': employee.full_name,
            'features': features
        }
    
    @classmethod
    def predict_churn(cls, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict churn probability for given features
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Dictionary with prediction results
        """
        # Load model if not loaded
        if not cls.load_model():
            return {"error": "Model not available"}
        
        # Prepare feature vector
        feature_names = cls._metadata['feature_names']
        X = np.array([[features.get(name, 0) for name in feature_names]])
        
        # Make prediction
        probability = float(cls._model.predict_proba(X)[0][1])
        prediction = int(cls._model.predict(X)[0])
        
        # Determine risk category
        if probability >= 0.7:
            risk_category = "High"
            risk_level = 3
        elif probability >= 0.4:
            risk_category = "Medium"
            risk_level = 2
        else:
            risk_category = "Low"
            risk_level = 1
        
        # Get feature importance
        feature_importance = cls._metadata.get('feature_importance', {})
        
        # Calculate top contributing factors for this prediction
        top_factors = cls._get_top_risk_factors(features, feature_importance)
        
        return {
            'success': True,
            'prediction': prediction,
            'probability': round(probability, 3),
            'risk_category': risk_category,
            'risk_level': risk_level,
            'top_factors': top_factors,
            'model_info': {
                'model_type': cls._metadata.get('model_type'),
                'model_version': cls._metadata.get('model_version'),
                'accuracy': cls._metadata.get('metrics', {}).get('accuracy')
            }
        }
    
    @classmethod
    def _get_top_risk_factors(cls, features: Dict[str, float], feature_importance: Dict[str, float], top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top contributing factors to churn risk"""
        factors = []
        
        # Get top important features
        for feature_name, importance in list(feature_importance.items())[:top_n]:
            value = features.get(feature_name, 0)
            
            # Determine if this feature increases or decreases risk
            risk_indicators = {
                'months_since_last_promotion': lambda x: x > 24,
                'salary_change_percent_1y': lambda x: x < 5,
                'performance_rating_trend': lambda x: x < 0,
                'engagement_score_latest': lambda x: x < 3.5,
                'engagement_score_trend': lambda x: x < 0,
                'manager_changes': lambda x: x > 1,
                'sick_days_ytd': lambda x: x > 10,
                'training_hours_ytd': lambda x: x < 30
            }
            
            is_risk_factor = risk_indicators.get(feature_name, lambda x: False)(value)
            
            factors.append({
                'feature': feature_name,
                'value': round(value, 2),
                'importance': round(importance, 3),
                'is_risk_factor': is_risk_factor
            })
        
        return factors
    
    @classmethod
    def predict_employee_churn(cls, employee_id: int, db: Session) -> Dict[str, Any]:
        """
        End-to-end churn prediction for an employee
        
        Args:
            employee_id: Employee ID
            db: Database session
            
        Returns:
            Complete prediction results
        """
        # Extract features
        feature_result = cls.extract_employee_features(employee_id, db)
        
        if 'error' in feature_result:
            return feature_result
        
        # Make prediction
        prediction_result = cls.predict_churn(feature_result['features'])
        
        if 'error' in prediction_result:
            return prediction_result
        
        # Combine results
        return {
            'success': True,
            'employee_id': employee_id,
            'employee_name': feature_result['employee_name'],
            'prediction': prediction_result['prediction'],
            'probability': prediction_result['probability'],
            'risk_category': prediction_result['risk_category'],
            'risk_level': prediction_result['risk_level'],
            'top_factors': prediction_result['top_factors'],
            'features': feature_result['features'],
            'model_info': prediction_result['model_info']
        }
    
    @classmethod
    def get_high_risk_employees(cls, db: Session, min_probability: float = 0.7) -> Dict[str, Any]:
        """
        Get all employees with high churn risk
        
        Args:
            db: Database session
            min_probability: Minimum probability threshold
            
        Returns:
            List of high-risk employees
        """
        # Get all active employees
        from src.database.models import Employee
        employees = db.query(Employee).filter(
            Employee.employment_status == 'active'
        ).all()
        
        high_risk_employees = []
        
        for employee in employees:
            try:
                result = cls.predict_employee_churn(employee.employee_id, db)
                
                if result.get('success') and result.get('probability', 0) >= min_probability:
                    high_risk_employees.append({
                        'employee_id': result['employee_id'],
                        'employee_name': result['employee_name'],
                        'probability': result['probability'],
                        'risk_category': result['risk_category'],
                        'top_factor': result['top_factors'][0] if result['top_factors'] else None
                    })
            except Exception as e:
                continue
        
        # Sort by probability
        high_risk_employees.sort(key=lambda x: x['probability'], reverse=True)
        
        return {
            'success': True,
            'total_employees': len(employees),
            'high_risk_count': len(high_risk_employees),
            'high_risk_employees': high_risk_employees,
            'threshold': min_probability
        }
    
    @classmethod
    def predict_department_churn(cls, department: str, db: Session) -> Dict[str, Any]:
        """
        Predict churn for all employees in a specific department
        
        Args:
            department: Department name
            db: Database session
            
        Returns:
            Department churn analysis with predictions for all employees
        """
        from src.database.models import Employee
        
        # Get all employees in department
        employees = db.query(Employee).filter(
            Employee.department == department
        ).all()
        
        if not employees:
            return {
                'success': False,
                'error': f'No employees found in department: {department}'
            }
        
        predictions = []
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        total_probability = 0.0
        
        for employee in employees:
            try:
                result = cls.predict_employee_churn(employee.employee_id, db)
                
                if result.get('success'):
                    predictions.append({
                        'employee_id': result['employee_id'],
                        'employee_name': result['employee_name'],
                        'probability': result['probability'],
                        'risk_category': result['risk_category'],
                        'risk_level': result['risk_level'],
                        'top_factors': result['top_factors'][:3]  # Top 3 factors
                    })
                    
                    total_probability += result['probability']
                    
                    # Count by risk category
                    if result['risk_category'] == 'High':
                        high_risk_count += 1
                    elif result['risk_category'] == 'Medium':
                        medium_risk_count += 1
                    else:
                        low_risk_count += 1
                        
            except Exception as e:
                # Skip employees without sufficient data
                predictions.append({
                    'employee_id': employee.employee_id,
                    'employee_name': employee.full_name,
                    'error': str(e)
                })
        
        # Sort by probability (highest risk first)
        predictions_with_prob = [p for p in predictions if 'probability' in p]
        predictions_with_errors = [p for p in predictions if 'error' in p]
        predictions_with_prob.sort(key=lambda x: x['probability'], reverse=True)
        
        # Calculate average churn probability for department
        avg_probability = total_probability / len(predictions_with_prob) if predictions_with_prob else 0.0
        
        # Identify common risk factors across department
        all_factors = {}
        for pred in predictions_with_prob:
            if 'top_factors' in pred:
                for factor in pred['top_factors']:
                    feature = factor['feature']
                    if feature not in all_factors:
                        all_factors[feature] = {'count': 0, 'importance_sum': 0.0}
                    all_factors[feature]['count'] += 1
                    all_factors[feature]['importance_sum'] += factor['importance']
        
        # Get top common risk factors
        common_factors = [
            {
                'feature': feature,
                'affected_employees': data['count'],
                'avg_importance': data['importance_sum'] / data['count']
            }
            for feature, data in all_factors.items()
        ]
        common_factors.sort(key=lambda x: x['affected_employees'], reverse=True)
        
        return {
            'success': True,
            'department': department,
            'total_employees': len(employees),
            'predictions_count': len(predictions_with_prob),
            'errors_count': len(predictions_with_errors),
            'average_churn_probability': round(avg_probability, 3),
            'risk_summary': {
                'high_risk': high_risk_count,
                'medium_risk': medium_risk_count,
                'low_risk': low_risk_count
            },
            'common_risk_factors': common_factors[:5],  # Top 5 common factors
            'predictions': predictions_with_prob + predictions_with_errors
        }
