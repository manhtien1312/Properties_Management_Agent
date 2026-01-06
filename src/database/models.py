from sqlalchemy import Column, Integer, String, Date, Boolean, Numeric, ForeignKey, CheckConstraint, Text, DateTime
from sqlalchemy.orm import relationship
from src.database.database import Base
from datetime import date, datetime
from decimal import Decimal


class Employee(Base):
    __tablename__ = "Employee"

    employee_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    department = Column(String, nullable=False)  # marketing, it
    role = Column(String, nullable=False)  # staff, manager
    manager_id = Column(Integer, ForeignKey("Employee.employee_id"), nullable=True)
    hire_date = Column(Date, nullable=False)
    tenure_months = Column(Integer, nullable=True)
    employment_status = Column(String, nullable=False)  # active, resigned, notice_period
    resignation_date = Column(Date, nullable=True)
    last_working_day = Column(Date, nullable=True)
    exit_interview_completed = Column(Boolean, default=False)
    location = Column(String, nullable=True)
    work_mode = Column(String, nullable=False)  # remote, hybrid, office

    # Relationships
    assets = relationship("Asset", back_populates="assigned_employee", foreign_keys="Asset.assigned_to")
    hr_analytics = relationship("HRAnalytic", back_populates="employee")


class Asset(Base):
    __tablename__ = "Asset"

    asset_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asset_tag = Column(String, nullable=False, unique=True, index=True)
    serial_number = Column(String, nullable=False, unique=True, index=True)
    device_type = Column(String, nullable=False)  # laptop, monitor, phone
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=False)
    purchase_value = Column(Numeric(10, 2), nullable=False)
    current_value = Column(Numeric(10, 2), nullable=False)
    assigned_to = Column(Integer, ForeignKey("Employee.employee_id"), nullable=True)
    assignment_date = Column(Date, nullable=True)
    status = Column(String, nullable=False)  # assigned, returned, lost, damaged, available
    return_date = Column(Date, nullable=True)
    return_due_date = Column(Date, nullable=True)
    condition = Column(String, nullable=False)  # excellent, good, fair, poor, damaged
    condition_notes = Column(Text, nullable=True)
    location = Column(String, nullable=False)
    warranty_expiry = Column(Date, nullable=False)
    last_maintenance = Column(Date, nullable=True)

    # Relationships
    assigned_employee = relationship("Employee", back_populates="assets", foreign_keys=[assigned_to])


class HRAnalytic(Base):
    __tablename__ = "HR_Analytic"

    record_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("Employee.employee_id"), nullable=False, index=True)
    record_date = Column(Date, nullable=False)
    performance_rating = Column(Numeric(3, 1), nullable=True)
    promotion_count = Column(Integer, nullable=True)
    months_since_last_promotion = Column(Integer, nullable=True)
    salary_change_percent = Column(Numeric(5, 2), nullable=True)
    sick_days_ytd = Column(Integer, nullable=True)
    unplanned_leaves = Column(Integer, nullable=True)
    engagement_score = Column(Numeric(3, 1), nullable=True)
    training_hours = Column(Integer, nullable=True)
    manager_changes = Column(Integer, nullable=True)
    department_changes = Column(Integer, nullable=True)
    overtime_hours = Column(Integer, nullable=True)
    remote_work_percent = Column(Numeric(5, 2), nullable=True)
    project_count = Column(Integer, nullable=True)
    tenure_months = Column(Integer, nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="hr_analytics")


class ConversationThread(Base):
    __tablename__ = "ConversationThread"

    thread_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    messages = relationship("ConversationMessage", back_populates="thread", cascade="all, delete-orphan", order_by="ConversationMessage.timestamp")


class ConversationMessage(Base):
    __tablename__ = "ConversationMessage"

    message_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(String, ForeignKey("ConversationThread.thread_id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Metadata
    employee_id = Column(Integer, nullable=True)
    question_type = Column(String, nullable=True)
    has_context_data = Column(Boolean, nullable=True)
    
    # Store the full context data as JSON text
    context_data = Column(Text, nullable=True)  # Serialized JSON of context
    
    # Relationships
    thread = relationship("ConversationThread", back_populates="messages")
