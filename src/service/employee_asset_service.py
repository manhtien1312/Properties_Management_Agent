from sqlalchemy.orm import Session
from src.database.models import Employee, Asset
from src.schemas import EmployeeCreate, EmployeeUpdate, AssetCreate, AssetUpdate
from src.config import settings
from datetime import datetime
from typing import List, Optional, Dict, Any


class EmployeeService:
    """Service layer for Employee operations"""

    @staticmethod
    def create_employee(db: Session, employee: EmployeeCreate) -> Employee:
        """Create a new employee"""
        # Calculate tenure months
        tenure_months = 0
        if employee.hire_date:
            tenure_months = (datetime.now().date() - employee.hire_date).days // 30

        db_employee = Employee(
            **employee.dict(),
            tenure_months=tenure_months,
            employment_status="active"
        )
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee

    @staticmethod
    def get_employee(db: Session, employee_id: int) -> Optional[Employee]:
        """Get employee by ID"""
        return db.query(Employee).filter(Employee.employee_id == employee_id).first()

    @staticmethod
    def get_employee_by_email(db: Session, email: str) -> Optional[Employee]:
        """Get employee by email"""
        return db.query(Employee).filter(Employee.email == email).first()

    @staticmethod
    def get_all_employees(db: Session, skip: int = 0, limit: int = 100) -> List[Employee]:
        """Get all employees with pagination"""
        return db.query(Employee).offset(skip).limit(limit).all()

    @staticmethod
    def get_employees_by_department(db: Session, department: str) -> List[Employee]:
        """Get all employees in a specific department"""
        return db.query(Employee).filter(Employee.department == department).all()

    @staticmethod
    def get_employees_by_manager(db: Session, manager_id: int) -> List[Employee]:
        """Get all employees under a specific manager"""
        return db.query(Employee).filter(Employee.manager_id == manager_id).all()

    @staticmethod
    def get_active_employees(db: Session) -> List[Employee]:
        """Get all active employees"""
        return db.query(Employee).filter(Employee.employment_status == "active").all()

    @staticmethod
    def update_employee(db: Session, employee_id: int, employee_update: EmployeeUpdate) -> Optional[Employee]:
        """Update an employee"""
        db_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not db_employee:
            return None

        update_data = employee_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_employee, key, value)

        # Recalculate tenure if hire_date was updated
        if "hire_date" in update_data:
            tenure_months = (datetime.now().date() - db_employee.hire_date).days // 30
            db_employee.tenure_months = tenure_months

        db.commit()
        db.refresh(db_employee)
        return db_employee

    @staticmethod
    def delete_employee(db: Session, employee_id: int) -> bool:
        """Delete an employee and release all assigned assets"""
        db_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not db_employee:
            return False
        
        # Release all assigned assets - change status to 'available' and clear assignment
        assets = db.query(Asset).filter(Asset.assigned_to == employee_id).all()
        for asset in assets:
            asset.status = "available"
            asset.assigned_to = None
            asset.assignment_date = None
            asset.return_due_date = None
        
        db.delete(db_employee)
        db.commit()
        return True

    @staticmethod
    def count_employees(db: Session) -> int:
        """Get total employee count"""
        return db.query(Employee).count()


class AssetService:
    """Service layer for Asset operations"""

    @staticmethod
    def create_asset(db: Session, asset: AssetCreate) -> Asset:
        """Create a new asset"""
        db_asset = Asset(**asset.dict())
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        return db_asset

    @staticmethod
    def get_asset(db: Session, asset_id: int) -> Optional[Asset]:
        """Get asset by ID"""
        return db.query(Asset).filter(Asset.asset_id == asset_id).first()

    @staticmethod
    def get_asset_by_tag(db: Session, asset_tag: str) -> Optional[Asset]:
        """Get asset by asset tag"""
        return db.query(Asset).filter(Asset.asset_tag == asset_tag).first()

    @staticmethod
    def get_asset_by_serial(db: Session, serial_number: str) -> Optional[Asset]:
        """Get asset by serial number"""
        return db.query(Asset).filter(Asset.serial_number == serial_number).first()

    @staticmethod
    def get_all_assets(db: Session, skip: int = 0, limit: int = 100) -> List[Asset]:
        """Get all assets with pagination"""
        return db.query(Asset).offset(skip).limit(limit).all()

    @staticmethod
    def get_assets_by_type(db: Session, device_type: str) -> List[Asset]:
        """Get all assets of a specific type"""
        return db.query(Asset).filter(Asset.device_type == device_type).all()

    @staticmethod
    def get_assets_by_status(db: Session, status: str) -> List[Asset]:
        """Get all assets with a specific status"""
        return db.query(Asset).filter(Asset.status == status).all()

    @staticmethod
    def get_assets_by_employee(db: Session, employee_id: int) -> List[Asset]:
        """Get all assets assigned to a specific employee"""
        return db.query(Asset).filter(Asset.assigned_to == employee_id).all()

    @staticmethod
    def get_available_assets(db: Session) -> List[Asset]:
        """Get all available assets"""
        return db.query(Asset).filter(Asset.status == "available").all()

    @staticmethod
    def update_asset(db: Session, asset_id: int, asset_update: AssetUpdate) -> Optional[Asset]:
        """Update an asset"""
        db_asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
        if not db_asset:
            return None

        update_data = asset_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_asset, key, value)

        db.commit()
        db.refresh(db_asset)
        return db_asset

    @staticmethod
    def delete_asset(db: Session, asset_id: int) -> bool:
        """Delete an asset"""
        db_asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
        if not db_asset:
            return False
        db.delete(db_asset)
        db.commit()
        return True

    @staticmethod
    def count_assets(db: Session) -> int:
        """Get total asset count"""
        return db.query(Asset).count()

    @staticmethod
    def get_assets_by_condition(db: Session, condition: str) -> List[Asset]:
        """Get all assets with a specific condition"""
        return db.query(Asset).filter(Asset.condition == condition).all()
