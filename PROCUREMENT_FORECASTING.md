# Procurement Forecasting

## Overview

The **Procurement Forecasting** feature combines Asset Health Tracker and Churn Prediction data to calculate future asset demand and generate purchase recommendations.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│              PROCUREMENT FORECASTING                     │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌──────────────────┐            ┌──────────────────────┐
│ Asset Health     │            │ Churn Prediction     │
│ Tracker          │            │                      │
│                  │            │                      │
│ • Aging assets   │            │ • High-risk employees│
│   (>3 years)     │            │   (≥70% probability) │
│ • Urgent (≥5yr)  │            │ • Their assigned     │
│ • Recommended    │            │   assets             │
│   (3-5yr)        │            │                      │
└──────────────────┘            └──────────────────────┘
        │                                   │
        └─────────────────┬─────────────────┘
                          ▼
              ┌───────────────────────┐
              │  TOTAL ASSET DEMAND   │
              │                       │
              │  By Device Type       │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  COMPARE WITH         │
              │  AVAILABLE INVENTORY  │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  PURCHASE             │
              │  RECOMMENDATIONS      │
              │                       │
              │  • Device type        │
              │  • Quantity           │
              │  • Priority           │
              └───────────────────────┘
```

## Features

✅ **Combines two data sources:**
- Aging assets needing refresh (Asset Health Tracker)
- Assets at risk from employee churn (Churn Prediction)

✅ **Calculates total demand** by device type

✅ **Compares with available inventory**

✅ **Generates purchase recommendations** with:
- Device type
- Quantity needed
- Priority level (HIGH/MEDIUM/LOW)
- Justification message

✅ **Safety stock buffer** (default 20%)

## API Endpoints

### 1. Quick Summary

**GET `/api/procurement/summary`**

Simple message with purchase needs.

```bash
curl "http://localhost:8000/api/procurement/summary"
```

**Response:**
```json
{
  "success": true,
  "procurement_needed": true,
  "total_units_to_purchase": 53,
  "purchase_by_type": {
    "laptop": 31,
    "monitor": 22
  },
  "message": "Purchase needed: 31 laptop(s), 22 monitor(s)"
}
```

### 2. Full Forecast

**GET `/api/procurement/forecast`**

Detailed recommendations for each device type.

**Parameters:**
- `forecast_months` (default: 6) - Forecast period
- `safety_stock_percent` (default: 0.2) - Buffer percentage

```bash
curl "http://localhost:8000/api/procurement/forecast?forecast_months=6&safety_stock_percent=0.2"
```

**Response:**
```json
{
  "success": true,
  "forecast_period_months": 6,
  "safety_stock_percent": 0.2,
  "summary": {
    "total_device_types": 3,
    "types_needing_procurement": 2,
    "total_units_to_purchase": 53,
    "inventory_sufficient": false
  },
  "summary_message": "⚠️  Procurement needed for 2 device type(s):\\n  • laptop: Purchase 31 units (HIGH priority)\\n",
  "recommendations": [
    {
      "device_type": "laptop",
      "demand_breakdown": {
        "refresh_needed": 26,
        "churn_replacement": 1,
        "total_base_demand": 27,
        "safety_buffer": 5,
        "total_needed_with_buffer": 32
      },
      "inventory": {
        "available_stock": 1,
        "shortage": 31,
        "surplus": 0
      },
      "action_required": true,
      "purchase_quantity": 31,
      "priority": "HIGH",
      "recommendation": "Purchase 31 laptop(s) to meet demand. 26 aging assets need replacement and 1 assets at risk due to employee churn."
    }
  ]
}
```

### 3. Comprehensive Report

**GET `/api/procurement/report`**

Executive summary with demand drivers.

```bash
curl "http://localhost:8000/api/procurement/report"
```

**Response:**
```json
{
  "success": true,
  "executive_summary": {
    "procurement_needed": true,
    "total_units_to_purchase": 53,
    "device_types_affected": 2
  },
  "demand_drivers": {
    "aging_assets": {
      "total": 69,
      "by_type": {
        "laptop": {"urgent": 3, "recommended": 23, "total": 26}
      }
    },
    "employee_churn": {
      "high_risk_employees": 6,
      "assets_at_risk": 1
    }
  },
  "current_inventory": {
    "laptop": 1,
    "monitor": 3,
    "phone": 51
  }
}
```

### 4. Demand Details

**GET `/api/procurement/demand`**

Raw demand calculation without inventory comparison.

```bash
curl "http://localhost:8000/api/procurement/demand"
```

## Usage Examples

### Example 1: Monthly Procurement Check

```python
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
from src.database.database import get_db

agent = get_employee_lifecycle_agent()
db = next(get_db())

# Get forecast
result = agent.get_procurement_forecast(db, forecast_months=6)

if result['summary']['inventory_sufficient']:
    print("✅ Inventory is sufficient")
else:
    print(f"⚠️ Need to purchase {result['summary']['total_units_to_purchase']} units")
    
    # Print recommendations
    for rec in result['recommendations']:
        if rec['action_required']:
            print(f"  • {rec['device_type']}: {rec['purchase_quantity']} units ({rec['priority']} priority)")
```

**Output:**
```
⚠️ Need to purchase 53 units
  • laptop: 31 units (HIGH priority)
  • monitor: 22 units (HIGH priority)
```

### Example 2: Automated Purchase Orders

```python
forecast = agent.get_procurement_forecast(db)

for rec in forecast['recommendations']:
    if rec['action_required']:
        # Create purchase order
        create_purchase_order(
            item_type=rec['device_type'],
            quantity=rec['purchase_quantity'],
            priority=rec['priority'],
            justification=rec['recommendation'],
            estimated_cost=estimate_cost(rec['device_type'], rec['purchase_quantity'])
        )
```

### Example 3: Email Alert to Procurement

```python
forecast = agent.get_procurement_forecast(db)

if not forecast['summary']['inventory_sufficient']:
    email_body = f"""
    Asset Procurement Needed
    
    {forecast['summary_message']}
    
    Details:
    """
    
    for rec in forecast['recommendations']:
        if rec['action_required']:
            email_body += f"\n{rec['device_type']}: {rec['recommendation']}"
    
    send_email(
        to='procurement@company.com',
        subject='Asset Procurement Alert',
        body=email_body
    )
```

### Example 4: Budget Planning

```python
# Get forecast
result = agent.get_procurement_forecast(db)

# Calculate estimated costs
unit_costs = {'laptop': 1200, 'monitor': 300, 'phone': 800}

total_cost = 0
for rec in result['recommendations']:
    if rec['action_required']:
        device = rec['device_type']
        qty = rec['purchase_quantity']
        cost = unit_costs.get(device, 0) * qty
        total_cost += cost
        print(f"{device}: {qty} units x ${unit_costs[device]} = ${cost:,}")

print(f"\nTotal Budget Needed: ${total_cost:,}")
```

**Output:**
```
laptop: 31 units x $1200 = $37,200
monitor: 22 units x $300 = $6,600

Total Budget Needed: $43,800
```

## Test Results

Based on current database:

```
📊 DEMAND ANALYSIS:
   Aging Assets: 69 total
     • laptop: 26 (3 urgent, 23 recommended)
     • phone: 22 (1 urgent, 21 recommended)  
     • monitor: 21 (0 urgent, 21 recommended)
   
   Employee Churn: 6 high-risk employees
     • Assets at risk: 1 laptop

🛒 PROCUREMENT RECOMMENDATIONS:
   ⚠️  Purchase needed: 2 device types
   
   laptop: Purchase 31 units (HIGH priority)
     - Demand: 27 (26 refresh + 1 churn)
     - Buffer: 5 (20%)
     - Total needed: 32
     - Available: 1
     - Shortage: 31
   
   monitor: Purchase 22 units (HIGH priority)
     - Demand: 21 (21 refresh + 0 churn)
     - Buffer: 4 (20%)
     - Total needed: 25
     - Available: 3
     - Shortage: 22
   
   phone: ✅ Inventory sufficient
     - Available: 51
     - Surplus: 25
```

## Integration Points

### With Asset Health Tracker
- Uses `get_assets_for_refresh()` to identify aging assets
- Categorizes as URGENT (≥5 years) or RECOMMENDED (3-5 years)

### With Churn Prediction
- Uses `get_high_risk_employees()` to identify at-risk employees
- Counts their assigned assets by device type
- Assumes 70%+ churn probability within 6 months

### With Inventory Management
- Queries available assets (status='available')
- Compares demand vs supply
- Calculates shortage/surplus

## Priority Levels

| Priority | Criteria |
|----------|----------|
| **HIGH** | Urgent refresh needed (≥5 years) OR shortage ≥5 units |
| **MEDIUM** | Shortage 2-4 units OR total demand ≥3 |
| **LOW** | Shortage 1 unit OR low total demand |
| **NONE** | No shortage (inventory sufficient) |

## Safety Stock Buffer

Default: 20% additional buffer

**Formula:**
```
Total Needed = Base Demand × (1 + Safety Stock %)
Total Needed = 27 × 1.20 = 32.4 ≈ 32
```

Adjust via API parameter:
```bash
# 10% buffer
curl "http://localhost:8000/api/procurement/forecast?safety_stock_percent=0.1"

# 30% buffer
curl "http://localhost:8000/api/procurement/forecast?safety_stock_percent=0.3"
```

## Files Created

1. **src/agent/procurement_forecasting_tools.py** - Core forecasting logic
2. **src/api/procurement.py** - API endpoints (4 endpoints)
3. **test_procurement_forecast.py** - Comprehensive test suite

## Summary

The Procurement Forecasting feature provides **data-driven purchase recommendations** by:

1. ✅ Identifying aging assets (>3 years old)
2. ✅ Predicting asset needs from employee churn
3. ✅ Calculating total demand with safety buffer
4. ✅ Comparing with available inventory
5. ✅ Generating purchase orders with quantities and priorities

**Current Recommendation:** Purchase 31 laptops and 22 monitors (total 53 units, ~$43,800 estimated cost)
