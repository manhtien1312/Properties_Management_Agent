# Employee Lifecycle Agent - Complete Documentation

## Overview

The **Employee Lifecycle Agent** is a unified AI agent that manages the complete employee lifecycle:

### **Onboarding (Asset Assignment)**
- Automatically assigns equipment to new hires
- Considers role, department, and employee type
- Prioritizes assets by condition

### **Offboarding (Asset Recovery)**
- Tracks all equipment held by departing employees
- Schedules asset returns with deadline
- Sends notifications to employee and manager
- Generates recovery documentation

## Architecture

The agent is built with:
- **LangChain** - Agent orchestration framework
- **Google Gemini 2.0 Flash** - AI reasoning (optional)
- **SQLAlchemy ORM** - Database abstraction
- **Email Service** - SMTP notifications

### Components

1. **EmployeeLifecycleTools** (`src/agent/tools.py`)
   - Unified tools for both onboarding and offboarding
   - Asset assignment tools
   - Asset recovery tools

2. **EmployeeLifecycleAgent** (`src/agent/asset_assignment_agent.py`)
   - Main orchestrator
   - LLM integration
   - Fallback deterministic logic

3. **Email Service** (`src/email_service.py`)
   - HTML email formatting
   - SMTP integration
   - Professional templates

4. **API Endpoints** (`src/api/employees.py`)
   - Create employee (triggers assignment)
   - Resign employee (triggers recovery)

## Setup

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file (copy from `.env.example`):

```env
# AI Model
GOOGLE_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash

# Agent
AGENT_ENABLED=true

# Email (optional)
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com

# Company Info
COMPANY_NAME=Your Company
SUPPORT_EMAIL=support@company.com
```

### 3. Run Server

```bash
python -m uvicorn src.main:app --reload
```

## Features

### Onboarding Flow

**When new employee is created:**

```
POST /api/employees/
{
  "full_name": "Jane Smith",
  "email": "jane.smith@company.com",
  "department": "it",
  "role": "staff",
  "hire_date": "2025-01-15",
  "location": "New York",
  "work_mode": "hybrid"
}
```

**Agent automatically:**
1. ✅ Determines asset requirements (1 laptop + 2 monitors for IT staff)
2. ✅ Searches for available assets (prioritizing excellent > good > fair condition)
3. ✅ Assigns matching assets
4. ✅ Returns assignment summary

**Response:**
```json
{
  "employee": {...},
  "asset_assignment": {
    "success": true,
    "assignment_summary": {
      "total_assets": 3,
      "assets_by_type": {
        "laptop": 1,
        "monitor": 2
      },
      "assets": [...]
    }
  }
}
```

### Offboarding Flow

**When employee resigns:**

```
POST /api/employees/1/resign
{
  "resignation_date": "2025-01-15",
  "last_working_day": "2025-01-22"
}
```

**Agent automatically:**
1. ✅ Finds all assigned assets
2. ✅ Sets return due date (7 days from resignation)
3. ✅ Sends email to employee with:
   - Complete asset list
   - Return due date
   - Return instructions
   - Contact information
4. ✅ CC's manager for awareness
5. ✅ Generates recovery summary

**Response:**
```json
{
  "employee": {...},
  "asset_recovery": {
    "success": true,
    "message": "Asset recovery initiated",
    "total_assets": 3,
    "return_due_date": "2025-01-22",
    "email_sent": true,
    "summary": {
      "total_assets": 3,
      "total_asset_value": 3500.00,
      "assets_by_type": {
        "laptop": 1,
        "monitor": 2
      }
    }
  }
}
```

## Asset Requirements Policy

### By Department & Role

| Department | Role | Laptop | Monitor | Phone |
|-----------|------|--------|---------|-------|
| IT | Staff | 1 | 2 | - |
| IT | Manager | 1 | 2 | 1 |
| Marketing | Staff | 1 | 1 | - |
| Marketing | Manager | 1 | 1 | 1 |

### Asset Selection Priority

When multiple assets available, preference order:
1. **Excellent** condition
2. **Good** condition  
3. **Fair** condition

## Email Templates

### Asset Return Notice (Offboarding)

**To:** Employee  
**CC:** Manager

**Content:**
- Company header
- Employee greeting with dates
- Important notice about consequences
- Detailed asset table:
  - Asset Tag (e.g., AST-000001)
  - Device Type (Laptop, Monitor, Phone)
  - Model (brand and model)
  - Condition (excellent, good, fair, etc.)
- Return instructions:
  - Location (IT Department)
  - Data backup requirements
  - Factory reset instructions
  - Original packaging preference
  - Return receipt requirement
- Contact information
- Company details

## API Reference

### Create Employee (Onboarding)

**Endpoint:** `POST /api/employees/`

**Request:**
```json
{
  "full_name": "John Doe",
  "email": "john.doe@company.com",
  "department": "it",
  "role": "staff",
  "hire_date": "2025-01-15",
  "location": "New York",
  "work_mode": "hybrid"
}
```

**Response:** `201 Created`

### Process Resignation (Offboarding)

**Endpoint:** `POST /api/employees/{employee_id}/resign`

**Request:**
```json
{
  "resignation_date": "2025-01-15",
  "last_working_day": "2025-01-22",
  "reason": "Career change"
}
```

**Response:** `200 OK`

## Operational Modes

### Full AI Mode (With Gemini API)
- Uses LLM for reasoning
- More flexible handling
- Handles edge cases
- Requires `GOOGLE_API_KEY`

### Fallback Mode (Without Gemini)
- Deterministic algorithm
- Fast and reliable
- Follows fixed policy
- Works when API unavailable

### Demo Mode (Email Disabled)
- All operations proceed normally
- Emails logged instead of sent
- Useful for testing
- Set `EMAIL_ENABLED=false`

## Tools Reference

### Onboarding Tools

| Tool | Input | Output |
|------|-------|--------|
| `get_asset_requirements` | employee_id | Requirements object |
| `find_available_assets` | {device_type, quantity} | Available assets list |
| `assign_asset` | {employee_id, asset_id} | Assignment confirmation |
| `get_assignment_summary` | employee_id | Assets assigned summary |

### Offboarding Tools

| Tool | Input | Output |
|------|-------|--------|
| `get_employee_assets` | employee_id | All held assets |
| `get_manager_info` | manager_id | Manager details |
| `schedule_asset_returns` | {employee_id, return_due_date} | Schedule confirmation |
| `get_resignation_summary` | employee_id | Complete summary |

## Troubleshooting

### Issue: Assets not assigning on onboarding
**Solutions:**
- Verify `AGENT_ENABLED=true`
- Check available assets in database
- Review database permissions
- Check logs for specific errors

### Issue: Emails not sending
**Solutions:**
- Verify `EMAIL_ENABLED=true`
- Check SMTP credentials
- For Gmail: use App Password, not regular password
- Verify firewall/network access

### Issue: Agent timeout
**Solutions:**
- Check internet connection
- Verify API key validity
- Check rate limiting
- Increase timeout values if needed

## Performance Notes

- **Onboarding:** ~2-5 seconds with LLM, <1 second fallback
- **Offboarding:** ~3-8 seconds with LLM, <1 second fallback
- **Email:** ~1-2 seconds per email

## Future Enhancements

- [ ] Scheduled return reminders
- [ ] Return receipt workflow
- [ ] Damage assessment on return
- [ ] Automated deduction calculations
- [ ] Multi-language support
- [ ] Asset lifecycle analytics
- [ ] Compliance reporting
- [ ] Integration with payroll systems

## Testing

### Test Onboarding
```bash
python test_agent.py
```

### Test Offboarding
```bash
python test_recovery_agent.py
```

## Related Documentation

- [Asset Assignment Agent](AGENT_DOCUMENTATION.md) - Legacy/detailed onboarding docs
- [Asset Recovery Agent](ASSET_RECOVERY_AGENT.md) - Legacy/detailed offboarding docs
- [README.md](README.md) - General setup and API reference
