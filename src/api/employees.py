from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from src.database.database import get_db
from src.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from src.service.employee_asset_service import EmployeeService
from src.config import settings
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.post("/", response_model=dict, status_code=201)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """Create a new employee and auto-assign assets if available"""
    # Check if email already exists
    existing = EmployeeService.get_employee_by_email(db, employee.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_employee = EmployeeService.create_employee(db, employee)
    
    response = {
        "employee": EmployeeResponse.from_orm(db_employee).dict(),
        "asset_assignment": None
    }
    
    # Trigger asset assignment agent if enabled
    if settings.agent_enabled:
        try:
            agent = get_employee_lifecycle_agent()
            assignment_result = agent.assign_assets_to_employee(db_employee.employee_id, db)
            response["asset_assignment"] = assignment_result
        except Exception as e:
            response["asset_assignment"] = {
                "success": False,
                "error": str(e),
                "message": "Asset assignment failed, but employee was created successfully"
            }
    
    return response


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """Get employee by ID"""
    db_employee = EmployeeService.get_employee(db, employee_id)
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee


@router.get("/", response_model=List[EmployeeResponse])
def get_all_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: str = Query(None),
    manager_id: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get all employees with optional filters"""
    if department:
        employees = EmployeeService.get_employees_by_department(db, department)
    elif manager_id:
        employees = EmployeeService.get_employees_by_manager(db, manager_id)
    elif status == "active":
        employees = EmployeeService.get_active_employees(db)
    else:
        employees = EmployeeService.get_all_employees(db, skip=skip, limit=limit)
    
    return employees


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """Update an employee"""
    db_employee = EmployeeService.update_employee(db, employee_id, employee_update)
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee


@router.delete("/{employee_id}", status_code=204)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """Delete an employee"""
    success = EmployeeService.delete_employee(db, employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return None


@router.get("/count/", response_model=dict)
def count_employees(db: Session = Depends(get_db)):
    """Get total employee count"""
    count = EmployeeService.count_employees(db)
    return {"total_employees": count}


@router.post("/{employee_id}/resign", response_model=dict, status_code=200)
def resign_employee(
    employee_id: int,
    resignation_data: dict,
    db: Session = Depends(get_db)
):
    """
    Process employee resignation and initiate asset recovery
    
    Request body:
    {
        "resignation_date": "2025-01-15",  # ISO format
        "last_working_day": "2025-01-20",  # Optional, ISO format
        "reason": "Personal reasons"  # Optional
    }
    """
    # Get employee
    db_employee = EmployeeService.get_employee(db, employee_id)
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Update employment status
    resignation_date = resignation_data.get("resignation_date")
    if not resignation_date:
        raise HTTPException(status_code=400, detail="resignation_date is required")
    
    update_data = EmployeeUpdate(
        employment_status="resigned",
        resignation_date=resignation_date,
        last_working_day=resignation_data.get("last_working_day")
    )
    
    db_employee = EmployeeService.update_employee(db, employee_id, update_data)
    
    response = {
        "employee": EmployeeResponse.from_orm(db_employee).dict(),
        "asset_recovery": None
    }
    
    # Trigger asset recovery if enabled
    if settings.agent_enabled:
        try:
            agent = get_employee_lifecycle_agent()
            recovery_result = agent.process_resignation(employee_id, db, return_days=7)
            response["asset_recovery"] = recovery_result
        except Exception as e:
            response["asset_recovery"] = {
                "success": False,
                "error": str(e),
                "message": "Asset recovery failed, but employee status was updated"
            }
    
    return response
