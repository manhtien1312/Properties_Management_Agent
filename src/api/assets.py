from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from src.database.database import get_db
from src.schemas import AssetCreate, AssetUpdate, AssetResponse
from src.service.employee_asset_service import AssetService
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("/", response_model=AssetResponse, status_code=201)
def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db)
):
    """Create a new asset"""
    # Check if asset tag already exists
    existing_tag = AssetService.get_asset_by_tag(db, asset.asset_tag)
    if existing_tag:
        raise HTTPException(status_code=400, detail="Asset tag already exists")

    # Check if serial number already exists
    existing_serial = AssetService.get_asset_by_serial(db, asset.serial_number)
    if existing_serial:
        raise HTTPException(status_code=400, detail="Serial number already exists")

    db_asset = AssetService.create_asset(db, asset)
    return db_asset


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Get asset by ID"""
    db_asset = AssetService.get_asset(db, asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset


@router.get("/", response_model=List[AssetResponse])
def get_all_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    device_type: str = Query(None),
    status: str = Query(None),
    employee_id: int = Query(None),
    condition: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get all assets with optional filters"""
    if device_type:
        assets = AssetService.get_assets_by_type(db, device_type)
    elif status:
        assets = AssetService.get_assets_by_status(db, status)
    elif employee_id:
        assets = AssetService.get_assets_by_employee(db, employee_id)
    elif condition:
        assets = AssetService.get_assets_by_condition(db, condition)
    else:
        assets = AssetService.get_all_assets(db, skip=skip, limit=limit)
    
    return assets


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    asset_update: AssetUpdate,
    db: Session = Depends(get_db)
):
    """Update an asset"""
    db_asset = AssetService.update_asset(db, asset_id, asset_update)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset


@router.delete("/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Delete an asset"""
    success = AssetService.delete_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return None


@router.get("/tag/{asset_tag}", response_model=AssetResponse)
def get_asset_by_tag(
    asset_tag: str,
    db: Session = Depends(get_db)
):
    """Get asset by asset tag"""
    db_asset = AssetService.get_asset_by_tag(db, asset_tag)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset


@router.get("/serial/{serial_number}", response_model=AssetResponse)
def get_asset_by_serial(
    serial_number: str,
    db: Session = Depends(get_db)
):
    """Get asset by serial number"""
    db_asset = AssetService.get_asset_by_serial(db, serial_number)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset


@router.get("/count/", response_model=dict)
def count_assets(db: Session = Depends(get_db)):
    """Get total asset count"""
    count = AssetService.count_assets(db)
    return {"total_assets": count}

@router.get("/health/refresh", response_model=dict)
def get_assets_for_refresh(
    age_years: int = Query(3, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get all assets that need refresh/replacement based on age
    
    Query Parameters:
    - age_years: Age threshold in years (default 3, min 1, max 20)
    
    Returns list of assets older than specified years marked for refresh
    """
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.track_asset_health(db, age_threshold_years=age_years)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/report", response_model=dict)
def get_asset_health_report(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive asset health report with metrics and recommendations
    
    Returns:
    - Total assets count
    - Health metrics (age statistics, condition distribution, etc.)
    - Assets marked for refresh (urgent and recommended)
    - Depreciation information
    """
    try:
        agent = get_employee_lifecycle_agent()
        result = agent.get_asset_health_report(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/summary", response_model=dict)
def get_asset_health_summary(
    db: Session = Depends(get_db)
):
    """
    Get asset health summary with age and condition statistics
    
    Returns:
    - Average asset age
    - Age categories (new, mid-age, old)
    - Condition distribution
    - Device type distribution
    - Total asset value and depreciation
    """
    from src.agent.tools import EmployeeLifecycleTools
    try:
        result = EmployeeLifecycleTools.get_asset_health_summary(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))