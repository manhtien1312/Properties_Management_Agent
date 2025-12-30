"""
Test script for the Asset Recovery Agent
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
from src.agent.tools import EmployeeLifecycleTools
from src.service.employee_asset_service import EmployeeService, AssetService


def test_recovery_agent():
    """Test the asset recovery agent"""
    
    db = SessionLocal()
    
    print("=" * 70)
    print("ASSET RECOVERY AGENT - TEST")
    print("=" * 70)
    
    try:
        # Get an active employee with assets (ID 1 or 2 usually have assets)
        active_employees = EmployeeService.get_active_employees(db)
        
        if not active_employees:
            print("✗ No active employees found")
            db.close()
            return
        
        # Find one with assets
        employee_with_assets = None
        for emp in active_employees[:10]:  # Check first 10
            assets = AssetService.get_assets_by_employee(db, emp.employee_id)
            if assets:
                employee_with_assets = emp
                break
        
        if not employee_with_assets:
            print("✗ No active employees with assets found")
            db.close()
            return
        
        emp_id = employee_with_assets.employee_id
        emp_name = employee_with_assets.full_name
        
        print(f"\nTesting with Employee: {emp_name} (ID: {emp_id})\n")
        
        # Get current assets
        print("Current Assets:")
        assets_before = AssetService.get_assets_by_employee(db, emp_id)
        print(f"  Total: {len(assets_before)} assets")
        for asset in assets_before[:5]:  # Show first 5
            print(f"    - {asset.asset_tag}: {asset.device_type} ({asset.condition})")
        if len(assets_before) > 5:
            print(f"    ... and {len(assets_before) - 5} more")
        
        # Set resignation date on employee
        resignation_date = datetime.now().date()
        last_working_day = resignation_date + timedelta(days=7)
        
        print(f"\n{'─' * 70}")
        print(f"Setting Resignation Date: {resignation_date}")
        print(f"Expected Return Date: {last_working_day}")
        print('─' * 70)
        
        # Update employee
        from src.schemas import EmployeeUpdate
        update_data = EmployeeUpdate(
            employment_status="resigned",
            resignation_date=resignation_date,
            last_working_day=last_working_day
        )
        EmployeeService.update_employee(db, emp_id, update_data)
        
        # Process resignation
        print("\nProcessing Resignation...")
        agent = get_employee_lifecycle_agent()
        result = agent.process_resignation(emp_id, db, return_days=7)
        
        print(f"\nRecovery Result:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Message: {result.get('message', 'N/A')}")
        print(f"  Total Assets: {result.get('total_assets', 0)}")
        print(f"  Assets Scheduled: {result.get('assets_scheduled', 0)}")
        print(f"  Return Due Date: {result.get('return_due_date', 'N/A')}")
        print(f"  Email Sent: {result.get('email_sent', False)}")
        
        if result.get("email_message"):
            print(f"  Email Status: {result['email_message']}")
        
        # Get summary
        if "summary" in result:
            summary = result["summary"]
            print(f"\nAsset Recovery Summary:")
            print(f"  Employee: {summary.get('employee_name')}")
            print(f"  Status: {summary.get('employment_status')}")
            print(f"  Total Assets to Return: {summary.get('total_assets')}")
            print(f"  Total Asset Value: ${summary.get('total_asset_value', 0):.2f}")
            
            if summary.get("assets_by_type"):
                print(f"  Assets by Type:")
                for asset_type, count in summary["assets_by_type"].items():
                    print(f"    - {asset_type.title()}: {count}")
            
            if summary.get("manager_name"):
                print(f"  Manager: {summary['manager_name']}")
            
            print(f"\n  Assets to Return:")
            for asset in summary.get("assets", [])[:5]:
                print(f"    - {asset['asset_tag']}: {asset['device_type']} ({asset['brand']} {asset['model']})")
                print(f"      Condition: {asset['condition']}, Due: {asset['return_due_date']}")
            
            if len(summary.get("assets", [])) > 5:
                print(f"    ... and {len(summary['assets']) - 5} more")
        
        print(f"\n{'=' * 70}")
        print("TEST COMPLETED")
        print(f"{'=' * 70}\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def test_recovery_tools():
    """Test individual recovery tools"""
    
    db = SessionLocal()
    
    print("=" * 70)
    print("ASSET RECOVERY TOOLS - TEST")
    print("=" * 70)
    
    try:
        # Get first employee with assets
        from src.database.models import Employee, Asset
        
        emp = db.query(Employee).first()
        if not emp:
            print("✗ No employees found")
            db.close()
            return
        
        print(f"\nTesting Tools with Employee: {emp.full_name} (ID: {emp.employee_id})\n")
        
        # Test get_employee_assets
        print("Test 1: Get Employee Assets")
        assets_info = EmployeeLifecycleTools.get_employee_assets(emp.employee_id, db)
        print(f"  ✓ Found {assets_info.get('total_assets', 0)} assets")
        
        # Test calculate_return_due_date
        print("\nTest 2: Calculate Return Due Date")
        resignation_date = "2025-01-15"
        return_date = EmployeeLifecycleTools.calculate_return_due_date(resignation_date, 7)
        print(f"  ✓ Resignation: {resignation_date} → Return Due: {return_date}")
        
        # Test get_resignation_summary
        print("\nTest 3: Get Resignation Summary")
        summary = EmployeeLifecycleTools.get_resignation_summary(emp.employee_id, db)
        if "error" not in summary:
            print(f"  ✓ Employee: {summary.get('employee_name')}")
            print(f"  ✓ Total Assets: {summary.get('total_assets')}")
            print(f"  ✓ Manager: {summary.get('manager_name', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("TOOLS TEST COMPLETED")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    # Test tools first
    test_recovery_tools()
    
    # Then test full agent
    test_recovery_agent()
