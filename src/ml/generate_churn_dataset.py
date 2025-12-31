"""
Generate synthetic dataset for Employee Churn Prediction
Creates realistic training data with 16 features and binary target
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random

random.seed(42)
np.random.seed(42)


def generate_churn_dataset(n_samples=1000):
    """
    Generate synthetic employee churn dataset
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with features and target variable
    """
    
    print(f"Generating {n_samples} employee records for churn prediction...")
    
    data = []
    
    for i in range(n_samples):
        # Generate features
        tenure_months = np.random.randint(1, 120)  # 0-10 years
        
        # Resignation likelihood increases with certain patterns
        is_high_risk = random.random() < 0.3  # 30% will be high risk
        
        if is_high_risk:
            # High churn risk patterns
            months_since_last_promotion = np.random.randint(24, 60)  # Long time since promotion
            salary_change_percent_1y = np.random.uniform(-2, 3)  # Low/negative salary change
            performance_rating_avg = np.random.uniform(2.0, 3.5)  # Lower performance
            performance_rating_trend = np.random.uniform(-0.5, 0.1)  # Declining
            sick_days_ytd = np.random.randint(8, 25)  # More sick days
            unplanned_leaves_ytd = np.random.randint(4, 15)  # More unplanned leaves
            engagement_score_latest = np.random.uniform(1.5, 3.0)  # Low engagement
            engagement_score_trend = np.random.uniform(-1.0, -0.1)  # Declining engagement
            manager_changes = np.random.randint(2, 5)  # Multiple manager changes
            department_changes = np.random.randint(1, 4)  # Multiple transfers
            training_hours_ytd = np.random.randint(0, 20)  # Low training
            overtime_hours_avg = np.random.uniform(20, 60)  # High overtime
            remote_work_percent = np.random.uniform(0, 40)  # Low remote work
            project_count = np.random.randint(0, 2)  # Few projects
            reports_count = np.random.randint(0, 2)  # Few direct reports
            
            # 70% chance of resignation within 6 months for high risk
            resigned_within_6m = 1 if random.random() < 0.7 else 0
            
        else:
            # Low/Medium churn risk patterns
            months_since_last_promotion = np.random.randint(0, 36)  # Recent promotion
            salary_change_percent_1y = np.random.uniform(2, 15)  # Good salary growth
            performance_rating_avg = np.random.uniform(3.5, 5.0)  # Good performance
            performance_rating_trend = np.random.uniform(-0.2, 0.8)  # Stable/improving
            sick_days_ytd = np.random.randint(0, 10)  # Normal sick days
            unplanned_leaves_ytd = np.random.randint(0, 5)  # Few unplanned leaves
            engagement_score_latest = np.random.uniform(3.0, 5.0)  # Good engagement
            engagement_score_trend = np.random.uniform(-0.3, 1.0)  # Stable/improving
            manager_changes = np.random.randint(0, 2)  # Stable management
            department_changes = np.random.randint(0, 2)  # Stable department
            training_hours_ytd = np.random.randint(20, 100)  # Good training
            overtime_hours_avg = np.random.uniform(0, 25)  # Reasonable overtime
            remote_work_percent = np.random.uniform(40, 100)  # Good remote flexibility
            project_count = np.random.randint(2, 10)  # Active projects
            reports_count = np.random.randint(0, 8)  # Varies by role
            
            # Only 15% chance of resignation for low risk
            resigned_within_6m = 1 if random.random() < 0.15 else 0
        
        # Create record
        record = {
            'employee_id': f'EMP-{i+1:04d}',
            'tenure_months': tenure_months,
            'months_since_last_promotion': months_since_last_promotion,
            'salary_change_percent_1y': round(salary_change_percent_1y, 2),
            'performance_rating_avg': round(performance_rating_avg, 2),
            'performance_rating_trend': round(performance_rating_trend, 2),
            'sick_days_ytd': sick_days_ytd,
            'unplanned_leaves_ytd': unplanned_leaves_ytd,
            'engagement_score_latest': round(engagement_score_latest, 2),
            'engagement_score_trend': round(engagement_score_trend, 2),
            'manager_changes': manager_changes,
            'department_changes': department_changes,
            'training_hours_ytd': training_hours_ytd,
            'overtime_hours_avg': round(overtime_hours_avg, 1),
            'remote_work_percent': round(remote_work_percent, 1),
            'project_count': project_count,
            'reports_count': reports_count,
            'resigned_within_6m': resigned_within_6m
        }
        
        data.append(record)
    
    df = pd.DataFrame(data)
    
    # Print dataset statistics
    print(f"\n{'='*70}")
    print("DATASET STATISTICS")
    print(f"{'='*70}")
    print(f"Total Samples: {len(df)}")
    print(f"Resigned within 6 months: {df['resigned_within_6m'].sum()} ({df['resigned_within_6m'].mean()*100:.1f}%)")
    print(f"Retained: {(df['resigned_within_6m']==0).sum()} ({(df['resigned_within_6m']==0).mean()*100:.1f}%)")
    print(f"\nFeature Summary:")
    print(df.describe())
    
    return df


def save_dataset(df, filepath='src/ml/churn_training_data.csv'):
    """Save dataset to CSV"""
    df.to_csv(filepath, index=False)
    print(f"\n✓ Dataset saved to: {filepath}")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")


if __name__ == "__main__":
    # Generate dataset
    df = generate_churn_dataset(n_samples=1000)
    
    # Save to file
    save_dataset(df)
    
    print(f"\n{'='*70}")
    print("Dataset generation completed successfully!")
    print(f"{'='*70}\n")
