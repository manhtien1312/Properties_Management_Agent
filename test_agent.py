"""
Test script for the Asset Assignment Agent
Run this to verify agent functionality
"""

import sys
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
from src.service.employee_asset_service import EmployeeService
from src.schemas import EmployeeCreate
from datetime import datetime


def test_agent_assignment():
    """Test the agent asset assignment"""
    
    db = SessionLocal()
    
    print("=" * 70)
    print("ASSET ASSIGNMENT AGENT - TEST")
    print("=" * 70)
    
    try:
        # Create test employees
        test_employees = [
            {
                "full_name": "Test IT Staff",
                "email": f"test.it.staff.{datetime.now().timestamp()}@company.com",
                "department": "it",
                "role": "staff",
                "hire_date": datetime.now().date(),
                "location": "New York",
                "work_mode": "hybrid"
            },
            {
                "full_name": "Test Marketing Staff",
                "email": f"test.marketing.staff.{datetime.now().timestamp()}@company.com",
                "department": "marketing",
                "role": "staff",
                "hire_date": datetime.now().date(),
                "location": "Los Angeles",
                "work_mode": "remote"
            },
            {
                "full_name": "Test IT Manager",
                "email": f"test.it.manager.{datetime.now().timestamp()}@company.com",
                "department": "it",
                "role": "manager",
                "hire_date": datetime.now().date(),
                "location": "Chicago",
                "work_mode": "office"
            }
        ]
        
        agent = get_employee_lifecycle_agent()
        
        for emp_data in test_employees:
            print(f"\n{'─' * 70}")
            print(f"Testing: {emp_data['full_name']} ({emp_data['department']}/{emp_data['role']})")
            print('─' * 70)
            
            # Create employee
            employee = EmployeeService.create_employee(db, EmployeeCreate(**emp_data))
            print(f"✓ Employee created: ID {employee.employee_id}")
            
            # Assign assets
            result = agent.assign_assets_to_employee(employee.employee_id, db)
            
            print(f"\nAssignment Result:")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Message: {result.get('message', 'N/A')}")
            
            if "assignment_summary" in result:
                summary = result["assignment_summary"]
                print(f"\nAssets Assigned: {summary.get('total_assets', 0)}")
                
                for asset_type, assets in summary.get("assets_by_type", {}).items():
                    print(f"\n  {asset_type.upper()} ({len(assets)}):")
                    for asset in assets:
                        print(f"    - {asset['asset_tag']} ({asset['condition']}) - {asset['brand']} {asset['model']}")
            
            if result.get("failed_assignments"):
                print(f"\nFailed Assignments:")
                for failed in result["failed_assignments"]:
                    print(f"  - {failed.get('message', failed)}")
        
        print(f"\n{'=' * 70}")
        print("TEST COMPLETED SUCCESSFULLY")
        print(f"{'=' * 70}\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def test_agent_availability():
    """Test if agent is properly configured"""
    
    print("=" * 70)
    print("AGENT CONFIGURATION CHECK")
    print("=" * 70)
    
    from src.config import settings
    
    print(f"\nAgent Enabled: {settings.agent_enabled}")
    print(f"Google API Key: {'✓ Set' if settings.google_api_key else '✗ Not Set'}")
    print(f"Gemini Model: {settings.gemini_model}")
    
    agent = get_employee_lifecycle_agent()
    print(f"LLM Initialized: {'✓ Yes' if agent.llm else '✗ No (Fallback mode)'}")
    
    if not agent.llm:
        print("\nNote: Running in fallback mode. LLM features will use deterministic logic.")
    else:
        print("\nNote: Running in full AI mode with Gemini.")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Check configuration first
    test_agent_availability()
    
    # Run tests
    test_agent_assignment()
