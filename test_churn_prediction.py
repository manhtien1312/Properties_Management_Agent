"""
Comprehensive test suite for Employee Churn Prediction Agent
Tests dataset generation, model training, predictions, and API endpoints
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_dataset_generation():
    """Test synthetic dataset generation"""
    print("\n" + "="*70)
    print("TEST 1: Dataset Generation")
    print("="*70)
    
    try:
        # Import and run dataset generator
        from src.ml.generate_churn_dataset import generate_churn_dataset
        
        print("Generating dataset with 1000 samples...")
        df = generate_churn_dataset(n_samples=1000)
        
        # Validate dataset
        assert len(df) == 1000, "Dataset should have 1000 rows"
        assert len(df.columns) >= 17, "Dataset should have at least 17 columns (16 features + target)"
        assert 'resigned_within_6m' in df.columns, "Target column missing"
        
        # Check feature columns
        required_features = [
            'tenure_months', 'months_since_last_promotion', 'salary_change_percent_1y',
            'performance_rating_avg', 'performance_rating_trend', 'sick_days_ytd',
            'unplanned_leaves_ytd', 'engagement_score_latest', 'engagement_score_trend',
            'manager_changes', 'department_changes', 'training_hours_ytd',
            'overtime_hours_avg', 'remote_work_percent', 'project_count', 'reports_count'
        ]
        
        for feature in required_features:
            assert feature in df.columns, f"Missing feature: {feature}"
        
        # Check target distribution
        churn_rate = df['resigned_within_6m'].mean()
        print(f"✓ Dataset generated successfully")
        print(f"  - Total samples: {len(df)}")
        print(f"  - Features: {len(df.columns) - 1}")
        print(f"  - Churn rate: {churn_rate*100:.1f}%")
        
        # Check if file exists
        csv_path = Path("src/ml/churn_training_data.csv")
        if csv_path.exists():
            print(f"  - CSV file saved: {csv_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Dataset generation failed: {e}")
        return False


def test_model_training():
    """Test model training"""
    print("\n" + "="*70)
    print("TEST 2: Model Training")
    print("="*70)
    
    try:
        import pickle
        import json
        from pathlib import Path
        
        # Check if training data exists
        csv_path = Path("src/ml/churn_training_data.csv")
        if not csv_path.exists():
            print("Training data not found. Running dataset generation...")
            from src.ml.generate_churn_dataset import generate_churn_dataset
            generate_churn_dataset(n_samples=1000)
        
        # Train model
        print("Training XGBoost model...")
        import subprocess
        result = subprocess.run(
            [sys.executable, "src/ml/train_churn_model.py"],
            capture_output=True,
            text=True
        )
        
        # Validate metrics from metadata file
        metadata_path = Path("src/ml/churn_model_metadata.json")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        metrics = metadata['metrics']
        
        # Validate metrics
        print(f"✓ Model trained successfully")
        print(f"  - Accuracy:  {metrics['accuracy']:.3f}")
        print(f"  - Precision: {metrics['precision']:.3f}")
        print(f"  - Recall:    {metrics['recall']:.3f}")
        print(f"  - F1 Score:  {metrics['f1_score']:.3f}")
        print(f"  - ROC AUC:   {metrics['roc_auc']:.3f}")
        
        # Check if model files exist
        model_path = Path("src/ml/churn_model.pkl")
        metadata_path = Path("src/ml/churn_model_metadata.json")
        
        assert model_path.exists(), "Model file not saved"
        assert metadata_path.exists(), "Metadata file not saved"
        
        print(f"  - Model saved: {model_path}")
        print(f"  - Metadata saved: {metadata_path}")
        
        # Load and validate model
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert 'model_type' in metadata, "Metadata missing model_type"
        assert 'metrics' in metadata, "Metadata missing metrics"
        assert 'feature_importance' in metadata, "Metadata missing feature importance"
        
        print(f"✓ Model validation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prediction_tools():
    """Test churn prediction tools"""
    print("\n" + "="*70)
    print("TEST 3: Prediction Tools")
    print("="*70)
    
    try:
        from src.agent.tool.churn_prediction_tools import ChurnPredictionTools
        from src.database.database import get_db
        
        # Load model
        print("Loading trained model...")
        model_data = ChurnPredictionTools.load_model()
        
        assert model_data is not None, "Model failed to load"
        assert model_data is not False, "Model file not found"
        
        print(f"✓ Model loaded successfully")
        
        # Test with database
        db = next(get_db())
        
        try:
            # Get first employee (no status filter since we removed it)
            from src.database.models import Employee
            employee = db.query(Employee).first()
            
            if employee:
                print(f"\nTesting prediction for employee {employee.employee_id}...")
                
                # Extract features
                features = ChurnPredictionTools.extract_employee_features(employee.employee_id, db)
                
                if features and features.get('success'):
                    print(f"✓ Features extracted successfully")
                    feature_data = features['features']
                    print(f"  - Tenure: {feature_data['tenure_months']} months")
                    print(f"  - Performance: {feature_data['performance_rating_avg']:.2f}")
                    print(f"  - Engagement: {feature_data['engagement_score_latest']:.2f}")
                    
                    # Predict churn
                    prediction = ChurnPredictionTools.predict_churn(feature_data)
                    
                    print(f"✓ Prediction successful")
                    print(f"  - Probability: {prediction['probability']:.3f}")
                    print(f"  - Risk Category: {prediction['risk_category']}")
                    print(f"  - Top Factors: {len(prediction['top_factors'])}")
                    
                    # Test end-to-end prediction
                    result = ChurnPredictionTools.predict_employee_churn(employee.employee_id, db)
                    
                    assert result['employee_id'] == employee.employee_id
                    assert 'probability' in result
                    assert 'risk_category' in result
                    
                    print(f"✓ End-to-end prediction successful")
                    
                else:
                    print("⚠ No HR analytics data found for employee")
                    print("  This is expected if database has no HR records")
                    
            else:
                print("⚠ No active employees found in database")
                print("  This is expected for empty database")
            
            # Test high-risk detection
            print("\nTesting high-risk employee detection...")
            high_risk = ChurnPredictionTools.get_high_risk_employees(db, min_probability=0.7)
            
            print(f"✓ High-risk detection successful")
            print(f"  - Total employees scanned: {high_risk['total_employees']}")
            print(f"  - High-risk count: {high_risk['high_risk_count']}")
            
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Prediction tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test API endpoints (requires running server)"""
    print("\n" + "="*70)
    print("TEST 4: API Endpoints")
    print("="*70)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test server connection
        print("Testing server connection...")
        try:
            response = requests.get(f"{base_url}/docs", timeout=2)
            if response.status_code != 200:
                print("⚠ Server not running. Start with: python -m uvicorn src.main:app --reload")
                return False
        except requests.exceptions.ConnectionError:
            print("⚠ Server not running. Start with: python -m uvicorn src.main:app --reload")
            return False
        
        print("✓ Server is running")
        
        # Test model info endpoint
        print("\n1. Testing GET /api/churn/model/info...")
        response = requests.get(f"{base_url}/api/churn/model/info")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data['success'] == True
        assert 'model_type' in data
        assert 'metrics' in data
        
        print(f"✓ Model info endpoint working")
        print(f"  - Model type: {data['model_type']}")
        print(f"  - Accuracy: {data['metrics']['accuracy']:.3f}")
        
        # Test individual prediction
        print("\n2. Testing GET /api/churn/predict/{employee_id}...")
        
        # Get first employee (no status filter)
        from src.database.database import get_db
        from src.database.models import Employee
        db = next(get_db())
        employee = db.query(Employee).first()
        db.close()
        
        if employee:
            response = requests.get(f"{base_url}/api/churn/predict/{employee.employee_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            if data['success']:
                print(f"✓ Individual prediction endpoint working")
                print(f"  - Employee: {data['employee_name']}")
                print(f"  - Probability: {data['probability']:.3f}")
                print(f"  - Risk: {data['risk_category']}")
            else:
                print(f"⚠ Prediction failed: {data.get('error', 'Unknown error')}")
        else:
            print("⚠ No employees in database to test")
        
        # Test high-risk endpoint
        print("\n3. Testing GET /api/churn/high-risk...")
        response = requests.get(f"{base_url}/api/churn/high-risk?min_probability=0.7")
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"✓ High-risk endpoint working")
        print(f"  - Total employees: {data['total_employees']}")
        print(f"  - High-risk count: {data['high_risk_count']}")
        
        # Test chatbot endpoint
        print("\n4. Testing GET /api/churn/chatbot...")
        question = "What is employee churn?"
        response = requests.get(
            f"{base_url}/api/churn/chatbot",
            params={"question": question}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] == True
        assert 'answer' in data
        
        print(f"✓ Chatbot endpoint working")
        print(f"  - Question: {data['question']}")
        print(f"  - Answer length: {len(data['answer'])} chars")
        
        # Test batch prediction
        if employee:
            print("\n5. Testing POST /api/churn/batch-predict...")
            response = requests.post(
                f"{base_url}/api/churn/batch-predict",
                json=[employee.employee_id]
            )
            
            assert response.status_code == 200
            data = response.json()
            
            print(f"✓ Batch prediction endpoint working")
            if 'predictions' in data:
                print(f"  - Predictions: {len(data['predictions'])}")
            elif 'results' in data:
                print(f"  - Results: {len(data['results'])}")
            else:
                print(f"  - Response keys: {list(data.keys())}")
        
        print("\n✓ All API endpoints working correctly")
        return True
        
    except Exception as e:
        print(f"✗ API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_extraction():
    """Test feature extraction from database"""
    print("\n" + "="*70)
    print("TEST 5: Feature Extraction")
    print("="*70)
    
    try:
        from src.agent.tool.churn_prediction_tools import ChurnPredictionTools
        from src.database.database import get_db
        from src.database.models import Employee, HRAnalytic
        from datetime import datetime, timedelta
        
        db = next(get_db())
        
        try:
            # Create test employee if needed
            employee = db.query(Employee).first()
            
            if not employee:
                print("Creating test employee...")
                from src.database.models import Employee
                employee = Employee(
                    name="Test Employee",
                    email="test@example.com",
                    department="Engineering",
                    position="Senior Developer",
                    hire_date=datetime.now() - timedelta(days=730),  # 2 years ago
                    salary=75000
                )
                db.add(employee)
                db.commit()
                db.refresh(employee)
                print(f"✓ Test employee created: ID {employee.employee_id}")
            
            # Create test HR analytics if needed
            hr_record = db.query(HRAnalytic).filter(HRAnalytic.employee_id == employee.employee_id).first()
            
            if not hr_record:
                print("Creating test HR analytics record...")
                hr_record = HRAnalytic(
                    employee_id=employee.employee_id,
                    record_date=datetime.now(),
                    performance_rating=4.0,
                    engagement_score=4.5,
                    sick_days=2,
                    unplanned_leaves=1,
                    training_hours=40,
                    overtime_hours=10,
                    remote_work_days=15,
                    active_projects=3
                )
                db.add(hr_record)
                db.commit()
                print(f"✓ Test HR analytics created")
            
            # Extract features
            print(f"\nExtracting features for employee {employee.employee_id}...")
            features = ChurnPredictionTools.extract_employee_features(employee.employee_id, db)
            
            if features and features.get('success'):
                print(f"✓ Features extracted successfully")
                print("\nFeature values:")
                for key, value in features.items():
                    if key != 'features':  # Skip nested features dict for now
                        print(f"  - {key}: {value}")
                
                # Now validate the actual features
                feature_data = features['features']
                print("\nFeature data:")
                for feature, value in feature_data.items():
                    print(f"  - {feature}: {value}")
                
                # Validate feature ranges
                assert 0 <= feature_data['tenure_months'] <= 600, "Invalid tenure"
                assert 0 <= feature_data['performance_rating_avg'] <= 5, "Invalid performance"
                assert 0 <= feature_data['engagement_score_latest'] <= 5, "Invalid engagement"
                assert 0 <= feature_data['remote_work_percent'] <= 100, "Invalid remote work %"
                
                print("\n✓ Feature validation successful")
                return True
            else:
                print("⚠ Could not extract features (insufficient HR data)")
                return False
                
        finally:
            db.close()
        
    except Exception as e:
        print(f"✗ Feature extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("EMPLOYEE CHURN PREDICTION - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Run tests
    results['Dataset Generation'] = test_dataset_generation()
    results['Model Training'] = test_model_training()
    results['Prediction Tools'] = test_prediction_tools()
    results['Feature Extraction'] = test_feature_extraction()
    results['API Endpoints'] = test_api_endpoints()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Churn prediction system is working correctly.")
    else:
        print("\n⚠ Some tests failed. Review output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
