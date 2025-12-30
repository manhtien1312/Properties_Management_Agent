from pydantic import BaseModel, EmailStr, Field
from datetime import date
from decimal import Decimal
from typing import Optional


# ===== EMPLOYEE SCHEMAS =====

class EmployeeBase(BaseModel):
    full_name: str
    email: EmailStr
    department: str  # marketing, it
    role: str  # staff, manager
    manager_id: Optional[int] = None
    hire_date: date
    location: Optional[str] = None
    work_mode: str  # remote, hybrid, office


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    role: Optional[str] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employment_status: Optional[str] = None
    resignation_date: Optional[date] = None
    last_working_day: Optional[date] = None
    exit_interview_completed: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    employee_id: int
    tenure_months: Optional[int] = None
    employment_status: str
    resignation_date: Optional[date] = None
    last_working_day: Optional[date] = None
    exit_interview_completed: bool

    class Config:
        from_attributes = True


# ===== ASSET SCHEMAS =====

class AssetBase(BaseModel):
    asset_tag: str
    serial_number: str
    device_type: str  # laptop, monitor, phone
    brand: str
    model: str
    purchase_date: date
    purchase_value: Decimal = Field(decimal_places=2)
    current_value: Decimal = Field(decimal_places=2)
    location: str
    warranty_expiry: date


class AssetCreate(AssetBase):
    assigned_to: Optional[int] = None
    assignment_date: Optional[date] = None
    status: str = "available"  # assigned, returned, lost, damaged, available
    condition: str = "good"  # excellent, good, fair, poor, damaged
    condition_notes: Optional[str] = None
    return_date: Optional[date] = None
    return_due_date: Optional[date] = None
    last_maintenance: Optional[date] = None


class AssetUpdate(BaseModel):
    asset_tag: Optional[str] = None
    serial_number: Optional[str] = None
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_value: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    assigned_to: Optional[int] = None
    assignment_date: Optional[date] = None
    status: Optional[str] = None
    return_date: Optional[date] = None
    return_due_date: Optional[date] = None
    condition: Optional[str] = None
    condition_notes: Optional[str] = None
    location: Optional[str] = None
    warranty_expiry: Optional[date] = None
    last_maintenance: Optional[date] = None


class AssetResponse(AssetBase):
    asset_id: int
    assigned_to: Optional[int] = None
    assignment_date: Optional[date] = None
    status: str
    return_date: Optional[date] = None
    return_due_date: Optional[date] = None
    condition: str
    condition_notes: Optional[str] = None
    last_maintenance: Optional[date] = None

    class Config:
        from_attributes = True
