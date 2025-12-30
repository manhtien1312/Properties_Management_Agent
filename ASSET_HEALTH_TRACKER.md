
# Asset Health & Refresh Tracker - Documentation

## Overview

The **Asset Health & Refresh Tracker** monitors asset age and condition to predict when equipment needs replacement. It automatically identifies assets that have exceeded their typical useful life and provides comprehensive health metrics.

## Features

### 1. **Asset Refresh Tracking**
- Identifies all assets older than a specified threshold (default: 3 years)
- Categorizes assets by refresh urgency:
  - **URGENT**: 5+ years old (immediate replacement needed)
  - **RECOMMENDED**: 3-5 years old (plan replacement)
- Returns comprehensive asset information including value and condition

### 2. **Asset Health Summary**
Provides statistics on your entire asset portfolio:
- **Age Statistics**: Average, oldest, and newest asset ages
- **Age Categories**: Count of assets in different age ranges
- **Condition Distribution**: Count of assets in each condition level
- **Device Type Distribution**: Assets grouped by type
- **Depreciation Analysis**: Total value and depreciation percentage

### 3. **Age Range Filtering**
Query assets within specific age ranges for granular analysis

### 4. **Comprehensive Health Reports**
Executive-level reports combining all metrics with actionable recommendations

## Architecture

### Tools (src/agent/tools.py)

```python
class EmployeeLifecycleTools:
    # Asset Health Tools
    - get_assets_for_refresh(db, age_threshold_years=3)
    - get_asset_health_summary(db)
    - get_assets_by_age_range(db, min_years=0, max_years=10)
```

### Agent Methods (src/agent/asset_assignment_agent.py)

```python
class EmployeeLifecycleAgent:
    - track_asset_health(db, age_threshold_years=3)
    - get_asset_health_report(db)
```

### API Endpoints (src/api/assets.py)

```
GET /api/assets/health/refresh?age_years=3
GET /api/assets/health/report
GET /api/assets/health/summary
```

## API Usage

### 1. Get Assets for Refresh

**Endpoint:** `GET /api/assets/health/refresh`

**Query Parameters:**
- `age_years`: Age threshold in years (default: 3, min: 1, max: 20)

**Example:**
```bash
curl "http://localhost:8000/api/assets/health/refresh?age_years=3"
```

**Response:**
```json
{
  "success": true,
  "message": "Asset health tracking completed. Found 12 assets for refresh.",
  "refresh_count": 12,
  "total_assets": 200,
  "total_refresh_value": 8500.50,
  "age_threshold_years": 3,
  "refresh_assets": [
    {
      "asset_id": 5,
      "asset_tag": "AST-000005",
      "device_type": "laptop",
      "brand": "Dell",
      "model": "XPS 13",
      "purchase_date": "2021-06-15",
      "age_years": 3.6,
      "age_days": 1312,
      "condition": "fair",
      "current_value": 750.00,
      "purchase_value": 1500.00,
      "status": "assigned",
      "assigned_to": 5,
      "refresh_status": "RECOMMENDED"
    },
    {
      "asset_id": 8,
      "asset_tag": "AST-000008",
      "device_type": "laptop",
      "brand": "HP",
      "model": "ProBook 450",
      "purchase_date": "2019-03-10",
      "age_years": 5.8,
      "age_days": 2119,
      "condition": "poor",
      "current_value": 400.00,
      "purchase_value": 1200.00,
      "status": "assigned",
      "assigned_to": 8,
      "refresh_status": "URGENT"
    }
  ]
}
```

### 2. Get Comprehensive Health Report

**Endpoint:** `GET /api/assets/health/report`

**Example:**
```bash
curl "http://localhost:8000/api/assets/health/report"
```

**Response:**
```json
{
  "success": true,
  "report_date": "2025-12-30T14:30:00",
  "total_assets": 200,
  "health_metrics": {
    "age_statistics": {
      "average_age_years": 2.3,
      "oldest_asset_years": 5.8,
      "newest_asset_years": 0.1
    },
    "age_categories": {
      "new_0_1_years": 35,
      "mid_age_1_3_years": 89,
      "old_over_3_years": 76
    },
    "condition_distribution": {
      "excellent": 42,
      "good": 88,
      "fair": 50,
      "poor": 15,
      "damaged": 5
    },
    "device_type_distribution": {
      "laptop": 68,
      "monitor": 96,
      "phone": 36
    },
    "total_asset_value": 125750.00,
    "depreciation_percent": 38.5
  },
  "refresh_summary": {
    "total_for_refresh": 76,
    "urgent_refresh": 12,
    "recommended_refresh": 64,
    "total_refresh_value": 28500.00
  },
  "urgent_assets": [
    {
      "asset_tag": "AST-000008",
      "device_type": "laptop",
      "age_years": 5.8,
      "refresh_status": "URGENT"
    }
  ],
  "recommended_assets": [
    {
      "asset_tag": "AST-000005",
      "device_type": "laptop",
      "age_years": 3.6,
      "refresh_status": "RECOMMENDED"
    }
  ]
}
```

### 3. Get Asset Health Summary

**Endpoint:** `GET /api/assets/health/summary`

**Example:**
```bash
curl "http://localhost:8000/api/assets/health/summary"
```

**Response:**
```json
{
  "success": true,
  "total_assets": 200,
  "health_summary": {
    "age_statistics": {
      "average_age_years": 2.3,
      "oldest_asset_years": 5.8,
      "newest_asset_years": 0.1
    },
    "age_categories": {
      "new_0_1_years": 35,
      "mid_age_1_3_years": 89,
      "old_over_3_years": 76
    },
    "condition_distribution": {
      "excellent": 42,
      "good": 88,
      "fair": 50,
      "poor": 15,
      "damaged": 5
    },
    "device_type_distribution": {
      "laptop": 68,
      "monitor": 96,
      "phone": 36
    },
    "total_asset_value": 125750.00,
    "depreciation_percent": 38.5
  }
}
```

## Testing

Run the test script to verify the feature:

```bash
python test_asset_health.py
```

This will test:
1. ✓ Asset refresh tracking with 3-year threshold
2. ✓ Asset health summary generation
3. ✓ Comprehensive health reports
4. ✓ Age range filtering

## Use Cases

### 1. Annual Budget Planning
Track total refresh value to plan IT budget:
```bash
curl "http://localhost:8000/api/assets/health/report"
```
Check `refresh_summary.total_refresh_value` to allocate budget

### 2. Asset Replacement Scheduling
Identify urgent replacements:
```bash
curl "http://localhost:8000/api/assets/health/refresh?age_years=5"
```
Focus on URGENT assets first

### 3. Depreciation Analysis
Monitor equipment value:
```bash
curl "http://localhost:8000/api/assets/health/summary"
```
Check `health_summary.depreciation_percent` to adjust replacement strategy

### 4. Condition Assessment
Combine with condition tracking:
```bash
# Get assets by condition
curl "http://localhost:8000/api/assets/?condition=fair"

# Get old assets in poor condition
curl "http://localhost:8000/api/assets/health/refresh?age_years=3"
```

## Business Logic

### Age Calculation
```python
age_days = (current_date - purchase_date).days
age_years = age_days / 365
```

### Refresh Status Determination
- **URGENT**: age_years > 5
- **RECOMMENDED**: 3 ≤ age_years ≤ 5

### Depreciation Calculation
```python
depreciation_percent = (1 - (total_current_value / total_purchase_value)) * 100
```

## Configuration

The default age threshold is **3 years**. To customize:

**For API calls:**
```bash
curl "http://localhost:8000/api/assets/health/refresh?age_years=5"
```

**In code:**
```python
agent = get_employee_lifecycle_agent()
result = agent.track_asset_health(db, age_threshold_years=5)
```

## Integration Examples

### With Employee Offboarding
When an employee resigns, check if their assets are due for refresh:

```python
# Employee resignation
asset_recovery = agent.process_resignation(employee_id, db)

# Check if assets should be refreshed instead of reassigned
refresh_assets = agent.track_asset_health(db)
```

### With Asset Assignment
Before assigning assets to new employees, prioritize assets NOT in refresh list:

```python
# Get assets not marked for refresh
all_refresh = agent.track_asset_health(db)
refresh_asset_ids = [a["asset_id"] for a in all_refresh["refresh_assets"]]

# Filter out refresh assets when assigning
available_assets = [a for a in available if a.asset_id not in refresh_asset_ids]
```

## Monitoring & Alerts

Monitor these KPIs:
- **Refresh Rate**: percentage of assets needing replacement
- **Average Age**: trend of equipment aging
- **Depreciation Rate**: value loss over time
- **Condition Trend**: how conditions are changing

## Future Enhancements

- [ ] Predictive replacement timeline based on usage patterns
- [ ] Warranty expiry alerts
- [ ] Maintenance schedule tracking
- [ ] ROI analysis for replacement decisions
- [ ] Bulk replacement batch recommendations
- [ ] Asset lifecycle cost analysis
- [ ] Recurring refresh reminders (monthly/quarterly)
- [ ] Export reports to Excel/PDF

## API Error Handling

All endpoints return appropriate HTTP status codes:

| Status | Scenario |
|--------|----------|
| 200 | Success |
| 400 | Invalid query parameters |
| 500 | Server error |

Example error response:
```json
{
  "detail": "Database connection error"
}
```
