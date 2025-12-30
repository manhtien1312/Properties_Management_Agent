# Asset Recovery Agent - Documentation

## Overview

The Asset Recovery Agent automatically handles employee resignation workflows by:
1. **Identifying all assets** held by the resigning employee
2. **Scheduling asset returns** with a due date (default: 7 days after resignation)
3. **Notifying employees and managers** via email with return instructions
4. **Tracking asset status** throughout the recovery process

## Features

### 1. Automatic Asset Tracking
- Queries all assets currently assigned to resigning employee
- Categorizes assets by type (laptop, monitor, phone)
- Calculates total asset value

### 2. Return Scheduling
- Sets return due date automatically (7 days after resignation date by default)
- Updates asset status with return expectations
- Maintains asset condition records

### 3. Email Notifications
- **Detailed asset return notice** sent to employee
- **CC notification** to direct manager
- Includes:
  - Complete asset list with details
  - Return due date clearly stated
  - Return instructions and procedures
  - Company contact information

### 4. Comprehensive Documentation
- Resignation summary report
- Asset recovery tracking
- Manager notification logs

## Setup

### 1. Email Configuration (Optional)

To enable email notifications, configure SMTP settings in `.env`:

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SUPPORT_EMAIL=support@company.com
```

**Using Gmail:**
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an "App Password" at https://myaccount.google.com/apppasswords
3. Use the generated password as `SMTP_PASSWORD`

### 2. Company Information

Configure company details in `.env`:

```env
COMPANY_NAME=Properties Management
COMPANY_PHONE=+1-555-0123
COMPANY_ADDRESS=123 Business St, City, State 12345
SUPPORT_EMAIL=support@company.com
```

## API Usage

### Trigger Employee Resignation

**Endpoint:** `POST /api/employees/{employee_id}/resign`

**Request Body:**
```json
{
  "resignation_date": "2025-01-15",
  "last_working_day": "2025-01-20",
  "reason": "Personal reasons"
}
```

**Parameters:**
- `resignation_date` (required): ISO format date of resignation
- `last_working_day` (optional): ISO format date of last working day
- `reason` (optional): Resignation reason

**Example:**
```bash
curl -X POST "http://localhost:8000/api/employees/1/resign" \
  -H "Content-Type: application/json" \
  -d '{
    "resignation_date": "2025-01-15",
    "last_working_day": "2025-01-22",
    "reason": "Career change"
  }'
```

**Response:**
```json
{
  "employee": {
    "employee_id": 1,
    "full_name": "John Smith",
    "email": "john.smith@company.com",
    "employment_status": "resigned",
    "resignation_date": "2025-01-15",
    "last_working_day": "2025-01-22"
  },
  "asset_recovery": {
    "success": true,
    "message": "Asset recovery initiated for John Smith",
    "employee_name": "John Smith",
    "resignation_date": "2025-01-15",
    "return_due_date": "2025-01-22",
    "total_assets": 3,
    "assets_scheduled": 3,
    "email_sent": true,
    "summary": {
      "total_assets": 3,
      "assets_by_type": {
        "laptop": 1,
        "monitor": 2
      },
      "total_asset_value": 3500.00,
      "assets": [
        {
          "asset_tag": "AST-000001",
          "device_type": "laptop",
          "brand": "Dell",
          "model": "XPS 13",
          "condition": "good",
          "current_value": 1200.00,
          "return_due_date": "2025-01-22"
        },
        {
          "asset_tag": "AST-000002",
          "device_type": "monitor",
          "brand": "LG",
          "model": "27UP550",
          "condition": "excellent",
          "current_value": 1150.00,
          "return_due_date": "2025-01-22"
        },
        {
          "asset_tag": "AST-000003",
          "device_type": "monitor",
          "brand": "Dell",
          "model": "U2719D",
          "condition": "good",
          "current_value": 1150.00,
          "return_due_date": "2025-01-22"
        }
      ]
    }
  }
}
```

## Email Template

The Asset Return Notice email includes:

### Header
- Document title: "Asset Return Notice"
- Company name

### Body
- Employee greeting
- Resignation date and return due date
- Important notice about consequences
- Detailed asset table with:
  - Asset Tag
  - Device Type
  - Model
  - Condition

### Return Instructions
- Return location (IT Department)
- Data backup requirements
- Packaging instructions
- Receipt requirement

### Contact Information
- Email address
- Phone number (if configured)
- Company address (if configured)

### Footer
- Disclaimer (automated message)
- Address

## Example Scenarios

### Scenario 1: Resignation with 3 Assets

```
Employee: John Smith
Resignation Date: Dec 10, 2025
Last Working Day: Dec 17, 2025
Assets Held:
  - AST-000150: Laptop (Dell XPS 13)
  - AST-000151: Monitor (LG 27UP550)
  - AST-000152: Monitor (Dell U2719D)

Return Due Date: Dec 17, 2025 (7 days later)

Actions:
  ✓ Update employee status to "resigned"
  ✓ Set return_due_date on all 3 assets
  ✓ Send email to john.smith@company.com
  ✓ CC manager@company.com
  ✓ Generate return notice with instructions
```

### Scenario 2: Resignation with No Assets

```
Employee: Jane Doe
Resignation Date: Dec 15, 2025
Assets Held: None

Actions:
  ✓ Update employee status to "resigned"
  ✓ Skip asset scheduling (no assets)
  ✓ Return success message
  ✓ No email sent (no assets to recover)
```

### Scenario 3: Manager Resignation

```
Employee: Robert Johnson (Manager)
Resignation Date: Dec 20, 2025
Assets Held:
  - AST-000160: Laptop (Apple MacBook Pro)
  - AST-000161: Monitor (ASUS VP28UQG)
  - AST-000162: Phone (iPhone 13)

Return Due Date: Dec 27, 2025

Actions:
  ✓ All assets scheduled for return
  ✓ Email sent to robert.johnson@company.com
  ✓ No manager CC (he's a manager)
  ✓ 3 assets worth ~$2500 to recover
```

## Response Codes

| Code | Scenario |
|------|----------|
| 200 | Resignation processed successfully |
| 400 | Missing required field (resignation_date) |
| 404 | Employee not found |
| 500 | Server error during processing |

## Features & Modes

### With Email Enabled
- Full email notifications sent
- HTML-formatted asset return notice
- CC to manager
- Professional communication trail

### Without Email (Demo Mode)
- All operations proceed normally
- Emails logged instead of sent
- Useful for testing/development
- Can be enabled by setting `EMAIL_ENABLED=false`

## Asset Status Flow

```
During Resignation:
  Initial Status: "assigned" → After Resign: "assigned" (with return_due_date)
  
Asset Return Process (Manual):
  1. Employee returns asset
  2. IT inspects and confirms
  3. Status updated to "returned" in API
  4. Employee checkout complete
```

## Troubleshooting

### Issue: Email not sending
**Solution:** 
- Verify `EMAIL_ENABLED=true`
- Check SMTP credentials
- For Gmail: ensure App Password is used, not regular password
- Check firewall/network access to SMTP server

### Issue: "Employee not found"
**Solution:** Verify employee_id is correct

### Issue: "Employee has no assets"
**Response:** This is normal - employee simply had no equipment

### Issue: Return dates not updating
**Solution:** 
- Verify agent is enabled: `AGENT_ENABLED=true`
- Check database permissions
- Verify resignation_date format (must be ISO: YYYY-MM-DD)

## Integration with Other Features

### Works with:
- **Asset Assignment Agent**: Handles new hires
- **Employee API**: Standard CRUD operations
- **Asset Management**: Tracks all asset movements

### Workflow Example:
```
1. New employee onboards
   → Asset Assignment Agent assigns equipment
   
2. Employee works for 2 years
   
3. Employee resigns
   → Asset Recovery Agent schedules returns
   → Email notifications sent
   
4. Employee returns assets
   → Update asset status manually via API
```

## Future Enhancements

- [ ] Automatic reminder emails before return due date
- [ ] Return receipt confirmation workflow
- [ ] Asset damage assessment upon return
- [ ] Automated deduction calculations
- [ ] Multi-language support
- [ ] Integration with exit interviews
- [ ] Asset donation workflow for damaged items
- [ ] Compliance reporting
