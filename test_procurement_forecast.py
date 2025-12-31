"""
Test script for Procurement Forecasting feature
Demonstrates asset demand calculation and procurement recommendations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.database import get_db
from src.agent.tool.procurement_forecasting_tools import ProcurementForecastingTools
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent


def test_asset_demand():
    """Test asset demand calculation"""
    
    print("\n" + "="*80)
    print("ASSET DEMAND CALCULATION TEST")
    print("="*80)
    
    db = next(get_db())
    
    try:
        result = ProcurementForecastingTools.calculate_asset_demand(db, forecast_months=6)
        
        if not result.get('success'):
            print(f"❌ Error: {result.get('error')}")
            return
        
        print(f"\n📊 DEMAND ANALYSIS (6-month forecast)")
        print(f"   Report Date: {result['forecast_date']}")
        
        # Print refresh assets
        print(f"\n🔧 AGING ASSETS NEEDING REFRESH:")
        print(f"   Total: {result['refresh_assets']['total_count']} assets")
        
        for device_type, data in result['refresh_assets']['summary'].items():
            print(f"\n   {device_type.upper()}:")
            print(f"      Urgent (≥5 years): {data['urgent']}")
            print(f"      Recommended (3-5 years): {data['recommended']}")
            print(f"      Total: {data['total']}")
        
        # Print churn replacement
        print(f"\n👥 CHURN REPLACEMENT NEEDS:")
        print(f"   High-risk employees: {result['churn_replacement']['high_risk_employees']}")
        print(f"   Assets at risk: {result['churn_replacement']['total_assets_at_risk']}")
        
        if result['churn_replacement']['by_type']:
            print(f"\n   By device type:")
            for device_type, count in result['churn_replacement']['by_type'].items():
                print(f"      {device_type}: {count} assets")
        
        # Print total demand
        print(f"\n📈 TOTAL DEMAND BY DEVICE TYPE:")
        for device_type, data in result['total_demand'].items():
            print(f"\n   {device_type.upper()}:")
            print(f"      Refresh needed: {data['refresh_needed']}")
            print(f"      Churn replacement: {data['churn_replacement']}")
            print(f"      Total demand: {data['total_demand']}")
        
        print(f"\n✅ Asset demand calculation completed!")
        
    finally:
        db.close()


def test_procurement_recommendations():
    """Test procurement recommendations"""
    
    print("\n" + "="*80)
    print("PROCUREMENT RECOMMENDATIONS TEST")
    print("="*80)
    
    db = next(get_db())
    
    try:
        result = ProcurementForecastingTools.get_procurement_recommendations(
            db, 
            forecast_months=6,
            safety_stock_percent=0.2
        )
        
        if not result.get('success'):
            print(f"❌ Error: {result.get('error')}")
            return
        
        print(f"\n📋 PROCUREMENT FORECAST")
        print(f"   Forecast Period: {result['forecast_period_months']} months")
        print(f"   Safety Stock Buffer: {result['safety_stock_percent']*100:.0f}%")
        
        # Print summary
        summary = result['summary']
        print(f"\n📊 SUMMARY:")
        print(f"   Device Types Analyzed: {summary['total_device_types']}")
        print(f"   Types Needing Procurement: {summary['types_needing_procurement']}")
        print(f"   Total Units to Purchase: {summary['total_units_to_purchase']}")
        print(f"   Inventory Sufficient: {'Yes ✅' if summary['inventory_sufficient'] else 'No ⚠️'}")
        
        # Print summary message
        print(f"\n{result['summary_message']}")
        
        # Print detailed recommendations
        print(f"\n📦 DETAILED RECOMMENDATIONS:")
        
        for rec in result['recommendations']:
            device_type = rec['device_type']
            print(f"\n{'='*60}")
            print(f"Device Type: {device_type.upper()}")
            print(f"{'='*60}")
            
            # Demand breakdown
            demand = rec['demand_breakdown']
            print(f"\n  Demand Breakdown:")
            print(f"    • Refresh needed: {demand['refresh_needed']}")
            print(f"    • Churn replacement: {demand['churn_replacement']}")
            print(f"    • Base demand: {demand['total_base_demand']}")
            print(f"    • Safety buffer: {demand['safety_buffer']}")
            print(f"    • Total with buffer: {demand['total_needed_with_buffer']}")
            
            # Inventory status
            inventory = rec['inventory']
            print(f"\n  Inventory Status:")
            print(f"    • Available stock: {inventory['available_stock']}")
            print(f"    • Shortage: {inventory['shortage']}")
            print(f"    • Surplus: {inventory['surplus']}")
            
            # Action
            print(f"\n  Action Required: {'Yes ⚠️' if rec['action_required'] else 'No ✅'}")
            
            if rec['action_required']:
                print(f"  Purchase Quantity: {rec['purchase_quantity']} units")
                print(f"  Priority: {rec['priority']}")
            
            print(f"\n  Recommendation:")
            print(f"    {rec['recommendation']}")
        
        print(f"\n✅ Procurement recommendations completed!")
        
    finally:
        db.close()


def test_procurement_report():
    """Test comprehensive procurement report"""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE PROCUREMENT REPORT TEST")
    print("="*80)
    
    db = next(get_db())
    
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.get_procurement_report(db, include_details=False)
        
        if not result.get('success'):
            print(f"❌ Error: {result.get('error')}")
            return
        
        print(f"\n📄 EXECUTIVE SUMMARY")
        print(f"   Report Date: {result['report_date']}")
        print(f"   Forecast Period: {result['forecast_period']}")
        
        summary = result['executive_summary']
        print(f"\n   Procurement Needed: {'Yes ⚠️' if summary['procurement_needed'] else 'No ✅'}")
        print(f"   Total Units to Purchase: {summary['total_units_to_purchase']}")
        print(f"   Device Types Affected: {summary['device_types_affected']}")
        
        print(f"\n{summary['summary_message']}")
        
        # Demand drivers
        print(f"\n📊 DEMAND DRIVERS:")
        
        drivers = result['demand_drivers']
        
        print(f"\n  Aging Assets:")
        print(f"    Total: {drivers['aging_assets']['total']}")
        for device_type, data in drivers['aging_assets']['by_type'].items():
            print(f"      {device_type}: {data['total']} (urgent: {data['urgent']}, recommended: {data['recommended']})")
        
        print(f"\n  Employee Churn:")
        print(f"    High-risk employees: {drivers['employee_churn']['high_risk_employees']}")
        print(f"    Assets at risk: {drivers['employee_churn']['assets_at_risk']}")
        for device_type, count in drivers['employee_churn']['by_type'].items():
            print(f"      {device_type}: {count}")
        
        # Current inventory
        print(f"\n📦 CURRENT INVENTORY:")
        for device_type, count in result['current_inventory'].items():
            print(f"    {device_type}: {count} available")
        
        print(f"\n✅ Comprehensive report generated!")
        
    finally:
        db.close()


def test_api_endpoints():
    """Test procurement API endpoints"""
    
    print("\n" + "="*80)
    print("API ENDPOINTS TEST")
    print("="*80)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Check server
        try:
            response = requests.get(f"{base_url}/docs", timeout=2)
            if response.status_code != 200:
                print("⚠️  Server not running. Start with: python -m uvicorn src.main:app --reload")
                return
        except requests.exceptions.ConnectionError:
            print("⚠️  Server not running. Start with: python -m uvicorn src.main:app --reload")
            return
        
        print("✅ Server is running\n")
        
        # Test 1: Summary endpoint
        print("1. Testing GET /api/procurement/summary...")
        response = requests.get(f"{base_url}/api/procurement/summary")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Summary endpoint working")
                print(f"   Procurement needed: {data['procurement_needed']}")
                print(f"   Total units: {data['total_units_to_purchase']}")
                print(f"   Message: {data['message']}")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ Status code: {response.status_code}")
        
        # Test 2: Forecast endpoint
        print(f"\n2. Testing GET /api/procurement/forecast...")
        response = requests.get(f"{base_url}/api/procurement/forecast?forecast_months=6&safety_stock_percent=0.2")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Forecast endpoint working")
                print(f"   Summary: {data['summary_message'][:100]}...")
                print(f"   Recommendations: {len(data['recommendations'])} device types")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ Status code: {response.status_code}")
        
        # Test 3: Report endpoint
        print(f"\n3. Testing GET /api/procurement/report...")
        response = requests.get(f"{base_url}/api/procurement/report")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Report endpoint working")
                print(f"   Executive summary available: {bool(data.get('executive_summary'))}")
                print(f"   Recommendations: {len(data.get('recommendations', []))}")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ Status code: {response.status_code}")
        
        # Test 4: Demand endpoint
        print(f"\n4. Testing GET /api/procurement/demand...")
        response = requests.get(f"{base_url}/api/procurement/demand")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Demand endpoint working")
                print(f"   Refresh assets: {data['refresh_assets']['total_count']}")
                print(f"   High-risk employees: {data['churn_replacement']['high_risk_employees']}")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ Status code: {response.status_code}")
        
        print(f"\n✅ All API endpoints tested!")
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")


def show_usage_examples():
    """Show usage examples"""
    
    print("\n" + "="*80)
    print("USAGE EXAMPLES")
    print("="*80)
    
    print("""
1. Quick Summary (REST API):
   
   curl "http://localhost:8000/api/procurement/summary"
   
   # Returns simple message like:
   # "Purchase needed: 5 laptop(s), 3 monitor(s)"

2. Full Forecast with Details:
   
   curl "http://localhost:8000/api/procurement/forecast?forecast_months=6"
   
   # Returns detailed recommendations for each device type
   # including priority levels and purchase quantities

3. Via Python Agent:
   
   from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
   from src.database.database import get_db
   
   agent = get_employee_lifecycle_agent()
   db = next(get_db())
   
   result = agent.get_procurement_forecast(db, forecast_months=6)
   
   if result['summary']['inventory_sufficient']:
       print("✅ Inventory is sufficient")
   else:
       print(f"⚠️ Need to purchase {result['summary']['total_units_to_purchase']} units")

4. Generate Monthly Report:
   
   result = agent.get_procurement_report(db)
   
   print(f"Aging assets: {result['demand_drivers']['aging_assets']['total']}")
   print(f"Churn risk: {result['demand_drivers']['employee_churn']['high_risk_employees']} employees")

5. Integration with Purchasing System:
   
   forecast = agent.get_procurement_forecast(db)
   
   for rec in forecast['recommendations']:
       if rec['action_required']:
           device_type = rec['device_type']
           quantity = rec['purchase_quantity']
           priority = rec['priority']
           
           # Send to purchasing system
           create_purchase_order(
               item=device_type,
               quantity=quantity,
               priority=priority,
               justification=rec['recommendation']
           )

6. Email Alert to Procurement:
   
   forecast = agent.get_procurement_forecast(db)
   
   if not forecast['summary']['inventory_sufficient']:
       message = forecast['summary_message']
       send_email(
           to='procurement@company.com',
           subject='Asset Procurement Needed',
           body=message
       )
""")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PROCUREMENT FORECASTING - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    # Run tests
    test_asset_demand()
    test_procurement_recommendations()
    test_procurement_report()
    test_api_endpoints()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n✨ All tests completed!")
