"""
Test script for department-level churn prediction
Demonstrates batch prediction by department
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.database import get_db
from src.agent.tool.churn_prediction_tools import ChurnPredictionTools
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
from src.database.models import Employee


def test_department_churn_prediction():
    """Test department-level churn prediction"""
    
    print("\n" + "="*80)
    print("DEPARTMENT CHURN PREDICTION TEST")
    print("="*80)
    
    db = next(get_db())
    
    try:
        # Get all departments
        departments = db.query(Employee.department).distinct().all()
        departments = [d[0] for d in departments if d[0]]
        
        print(f"\nFound {len(departments)} departments: {', '.join(departments)}\n")
        
        # Test each department
        for dept in departments:
            print("\n" + "-"*80)
            print(f"DEPARTMENT: {dept}")
            print("-"*80)
            
            # Get prediction
            result = ChurnPredictionTools.predict_department_churn(dept, db)
            
            if not result.get('success'):
                print(f"❌ Error: {result.get('error')}")
                continue
            
            # Print summary
            print(f"\n📊 DEPARTMENT SUMMARY:")
            print(f"   Total Employees: {result['total_employees']}")
            print(f"   Average Churn Probability: {result['average_churn_probability']*100:.1f}%")
            print(f"   Predictions Generated: {result['predictions_count']}")
            
            # Print risk summary
            print(f"\n🎯 RISK BREAKDOWN:")
            risk_summary = result['risk_summary']
            print(f"   🔴 High Risk:   {risk_summary['high_risk']} employees")
            print(f"   🟡 Medium Risk: {risk_summary['medium_risk']} employees")
            print(f"   🟢 Low Risk:    {risk_summary['low_risk']} employees")
            
            # Print common risk factors
            if result['common_risk_factors']:
                print(f"\n⚠️  COMMON RISK FACTORS:")
                for i, factor in enumerate(result['common_risk_factors'][:5], 1):
                    print(f"   {i}. {factor['feature']}")
                    print(f"      - Affects {factor['affected_employees']} employees")
                    print(f"      - Avg importance: {factor['avg_importance']:.3f}")
            
            # Print high-risk employees
            high_risk = [p for p in result['predictions'] if p.get('risk_category') == 'High']
            if high_risk:
                print(f"\n🚨 HIGH RISK EMPLOYEES ({len(high_risk)}):")
                for emp in high_risk[:5]:  # Show top 5
                    print(f"   • {emp['employee_name']} (ID: {emp['employee_id']})")
                    print(f"     Probability: {emp['probability']*100:.1f}%")
                    if emp.get('top_factors'):
                        top_factor = emp['top_factors'][0]
                        print(f"     Top Factor: {top_factor['feature']} (value: {top_factor['value']})")
            
            # Show sample predictions
            print(f"\n📋 SAMPLE PREDICTIONS:")
            for emp in result['predictions'][:3]:
                if 'probability' in emp:
                    print(f"   • {emp['employee_name']}: {emp['probability']*100:.1f}% ({emp['risk_category']})")
                else:
                    print(f"   • {emp['employee_name']}: Error - {emp.get('error', 'Unknown')}")
        
        print("\n" + "="*80)
        print("✅ Department churn prediction test completed!")
        print("="*80)
        
    finally:
        db.close()


def test_api_endpoint():
    """Test department churn prediction via API"""
    
    print("\n" + "="*80)
    print("API ENDPOINT TEST")
    print("="*80)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Check if server is running
        try:
            response = requests.get(f"{base_url}/docs", timeout=2)
            if response.status_code != 200:
                print("⚠️  Server not running. Start with: python -m uvicorn src.main:app --reload")
                return
        except requests.exceptions.ConnectionError:
            print("⚠️  Server not running. Start with: python -m uvicorn src.main:app --reload")
            return
        
        print("✅ Server is running\n")
        
        # Get departments
        db = next(get_db())
        departments = db.query(Employee.department).distinct().all()
        departments = [d[0] for d in departments if d[0]]
        db.close()
        
        if not departments:
            print("⚠️  No departments found in database")
            return
        
        # Test first department
        test_dept = departments[0]
        print(f"Testing endpoint: GET /api/churn/department/{test_dept}\n")
        
        response = requests.get(f"{base_url}/api/churn/department/{test_dept}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("✅ API endpoint working!\n")
                print(f"Department: {data['department']}")
                print(f"Total Employees: {data['total_employees']}")
                print(f"Average Churn: {data['average_churn_probability']*100:.1f}%")
                print(f"\nRisk Summary:")
                print(f"  High: {data['risk_summary']['high_risk']}")
                print(f"  Medium: {data['risk_summary']['medium_risk']}")
                print(f"  Low: {data['risk_summary']['low_risk']}")
            else:
                print(f"❌ API returned error: {data.get('error')}")
        else:
            print(f"❌ API returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")


def show_usage_examples():
    """Show usage examples"""
    
    print("\n" + "="*80)
    print("USAGE EXAMPLES")
    print("="*80)
    
    print("""
1. Via Python API:
   
   from src.agent.churn_prediction_tools import ChurnPredictionTools
   from src.database.database import get_db
   
   db = next(get_db())
   result = ChurnPredictionTools.predict_department_churn('Engineering', db)
   
   print(f"Average churn risk: {result['average_churn_probability']*100:.1f}%")
   print(f"High risk employees: {result['risk_summary']['high_risk']}")

2. Via Agent:
   
   from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
   from src.database.database import get_db
   
   agent = get_employee_lifecycle_agent()
   db = next(get_db())
   
   result = agent.predict_department_churn('Marketing', db)

3. Via REST API:
   
   curl "http://localhost:8000/api/churn/department/IT"
   
   # Response includes:
   # - Average churn probability
   # - Risk breakdown (high/medium/low)
   # - Common risk factors across department
   # - Individual predictions for each employee

4. Compare Departments:
   
   departments = ['IT', 'Marketing', 'Engineering']
   
   for dept in departments:
       result = ChurnPredictionTools.predict_department_churn(dept, db)
       print(f"{dept}: {result['average_churn_probability']*100:.1f}% avg churn")

5. Use for Strategic Planning:
   
   # Identify departments with high churn risk
   result = ChurnPredictionTools.predict_department_churn('Engineering', db)
   
   if result['average_churn_probability'] > 0.5:
       print("⚠️  Engineering has high churn risk!")
       print("Common factors:", result['common_risk_factors'][:3])
       
       # Take action based on common factors
       for factor in result['common_risk_factors']:
           if factor['feature'] == 'engagement_score_latest':
               print("→ Plan team engagement activities")
           elif factor['feature'] == 'overtime_hours_avg':
               print("→ Review workload distribution")
""")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DEPARTMENT CHURN PREDICTION - BATCH PREDICTION BY DEPARTMENT")
    print("="*80)
    
    # Run tests
    test_department_churn_prediction()
    
    # Test API endpoint
    test_api_endpoint()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n✨ Complete!")
