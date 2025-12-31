"""
Train Employee Churn Prediction Model
Uses XGBoost for binary classification
"""

import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import xgboost as xgb


def load_training_data(filepath='src/ml/churn_training_data.csv'):
    """Load training dataset"""
    print(f"Loading training data from {filepath}...")
    df = pd.read_csv(filepath)
    print(f"✓ Loaded {len(df)} records")
    return df


def prepare_features(df):
    """
    Prepare features and target for training
    
    Returns:
        X: Feature matrix
        y: Target variable
        feature_names: List of feature names
    """
    # Drop employee_id and target
    feature_cols = [col for col in df.columns if col not in ['employee_id', 'resigned_within_6m']]
    
    X = df[feature_cols].values
    y = df['resigned_within_6m'].values
    
    print(f"\n✓ Features prepared: {len(feature_cols)} features")
    print(f"  Feature names: {feature_cols}")
    
    return X, y, feature_cols


def train_xgboost_model(X_train, y_train, X_test, y_test):
    """
    Train XGBoost model with optimized parameters
    
    Returns:
        model: Trained XGBoost model
        metrics: Performance metrics
    """
    print(f"\n{'='*70}")
    print("TRAINING XGBOOST MODEL")
    print(f"{'='*70}")
    
    # Define model parameters
    params = {
        'objective': 'binary:logistic',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'eval_metric': 'logloss'
    }
    
    # Train model
    model = xgb.XGBClassifier(**params)
    
    print("Training in progress...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
    }
    
    print(f"\n✓ Model trained successfully!")
    print(f"\nModel Performance:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1 Score:  {metrics['f1_score']:.4f}")
    print(f"  ROC AUC:   {metrics['roc_auc']:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  {metrics['confusion_matrix']}")
    
    return model, metrics


def get_feature_importance(model, feature_names):
    """
    Extract feature importance from trained model
    
    Returns:
        Dictionary of feature importance scores
    """
    importance_scores = model.feature_importances_
    
    feature_importance = {}
    for name, score in zip(feature_names, importance_scores):
        feature_importance[name] = float(score)
    
    # Sort by importance
    feature_importance = dict(sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    ))
    
    print(f"\nTop 10 Feature Importances:")
    for i, (feature, score) in enumerate(list(feature_importance.items())[:10], 1):
        print(f"  {i:2d}. {feature:30s}: {score:.4f}")
    
    return feature_importance


def save_model(model, feature_names, feature_importance, metrics):
    """Save trained model and metadata"""
    
    # Save model
    model_path = 'src/ml/churn_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✓ Model saved to: {model_path}")
    
    # Save metadata
    metadata = {
        'model_type': 'XGBoost',
        'model_version': '1.0',
        'trained_date': datetime.now().isoformat(),
        'feature_names': feature_names,
        'feature_importance': feature_importance,
        'metrics': metrics,
        'n_features': len(feature_names)
    }
    
    metadata_path = 'src/ml/churn_model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved to: {metadata_path}")


def main():
    """Main training pipeline"""
    print(f"\n{'='*70}")
    print("EMPLOYEE CHURN PREDICTION MODEL TRAINING")
    print(f"{'='*70}\n")
    
    # Load data
    df = load_training_data()
    
    # Prepare features
    X, y, feature_names = prepare_features(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nDataset Split:")
    print(f"  Training samples: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
    print(f"  Test samples:     {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
    print(f"  Train churn rate: {y_train.mean()*100:.1f}%")
    print(f"  Test churn rate:  {y_test.mean()*100:.1f}%")
    
    # Train model
    model, metrics = train_xgboost_model(X_train, y_train, X_test, y_test)
    
    # Get feature importance
    feature_importance = get_feature_importance(model, feature_names)
    
    # Save model and metadata
    save_model(model, feature_names, feature_importance, metrics)
    
    print(f"\n{'='*70}")
    print("TRAINING COMPLETED SUCCESSFULLY!")
    print(f"{'='*70}\n")
    
    return metrics


if __name__ == "__main__":
    metrics = main()
