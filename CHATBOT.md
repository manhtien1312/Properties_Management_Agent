# Unified Chatbot - Complete Documentation

## Overview

The unified chatbot is an AI-powered assistant that can answer three types of questions using a **single API endpoint**:

1. **Asset Count Questions** - How many assets is an employee using?
2. **Resignation & Refresh Questions** - What assets must be returned and do they need refresh?
3. **Churn Prediction Questions** - What is the employee's turnover risk?

## Key Features

✅ **Single Endpoint** - All questions use `/api/churn/chatbot`  
✅ **Automatic Classification** - Detects question type automatically  
✅ **Context-Aware** - Retrieves relevant data based on employee_id  
✅ **AI-Powered** - Uses Google Gemini for natural language responses  
✅ **Asset Refresh Analysis** - Identifies assets >3 years old that need replacement  

## API Endpoint

```
GET /api/churn/chatbot
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | string | Yes | Your question in natural language |
| `employee_id` | integer | No | Employee ID for context-specific answers |

### Response Format

```json
{
  "success": true,
  "question": "Your question",
  "question_type": "asset_count | resignation_assets | churn_prediction",
  "answer": "AI-generated natural language answer",
  "context": {
    "employee_id": 5,
    "has_context_data": true,
    "data": { /* Relevant data used to answer */ }
  }
}
```

## Usage Examples

### 1. Asset Count Questions

**Question:** *"How many assets is employee 5 currently using?"*

```bash
curl "http://localhost:8000/api/churn/chatbot?question=How+many+assets+is+employee+5+using?&employee_id=5"
```

**Browser:**
```
http://localhost:8000/api/churn/chatbot?question=How%20many%20assets%20is%20employee%205%20using?&employee_id=5
```

**Response Context Includes:**
- Employee name and department
- Total number of assets
- Count by device type (laptop, monitor, phone)
- Asset details (brand, model, condition)
- Total asset value

**Example AI Answer:**
```
Employee John Smith (ID: 5) from the IT department is currently using 3 assets:
- 1 Laptop: Dell Latitude 7420 (excellent condition)
- 2 Monitors: Samsung U28E590D (good condition)

The total value of assets assigned to this employee is $2,450.00.
```

### 2. Resignation & Asset Refresh Questions

**Question:** *"If employee 10 resigns, what assets must be returned and do they need refresh?"*

```bash
curl "http://localhost:8000/api/churn/chatbot?question=If+employee+10+resigns+what+assets+need+refresh?&employee_id=10"
```

**Browser:**
```
http://localhost:8000/api/churn/chatbot?question=If%20employee%2010%20resigns%2C%20what%20assets%20must%20be%20returned%20and%20do%20they%20need%20refresh?&employee_id=10
```

**Response Context Includes:**
- Total assets to return
- Number of assets needing refresh (>3 years old)
- Number of assets OK to reassign
- Summary by device type with refresh status
- Detailed asset list with:
  - Asset age in years
  - Refresh status (URGENT >5 years, RECOMMENDED >3 years, OK <3 years)
  - Refresh reason
  - Current condition and value

**Example AI Answer:**
```
If employee Sarah Johnson (ID: 10) resigns, 4 assets must be returned:

NEEDS REFRESH (>3 years old):
- Laptop HP-LAP-001: 4.2 years old - RECOMMENDED for replacement
- Monitor SAM-MON-015: 5.8 years old - URGENT replacement needed

OK TO REASSIGN:
- Monitor SAM-MON-016: 1.5 years old - Good condition, can be reassigned
- Phone APP-PHO-032: 2.1 years old - Excellent condition, can be reassigned

Recommendation: 2 assets need refresh and should be replaced with new equipment. 
The remaining 2 assets are in acceptable condition and can be reassigned to new employees.
```

### 3. Churn Prediction Questions

**Question:** *"What is the churn risk for employee 3?"*

```bash
curl "http://localhost:8000/api/churn/chatbot?question=What+is+churn+risk+for+employee+3?&employee_id=3"
```

**Browser:**
```
http://localhost:8000/api/churn/chatbot?question=What%20is%20the%20churn%20risk%20for%20employee%203?&employee_id=3
```

**Response Context Includes:**
- Churn probability percentage
- Risk category (HIGH/MEDIUM/LOW)
- Top risk factors
- Model information

**Example AI Answer:**
```
Employee Michael Chen (ID: 3) has a HIGH churn risk with 78% probability of resignation 
within 6 months.

Top Risk Factors:
1. Low engagement score (trend declining)
2. No promotion in 24+ months
3. High overtime hours

Recommendations:
- Schedule 1-on-1 with manager immediately
- Discuss career development opportunities
- Review workload and work-life balance
- Consider retention bonus or promotion
```

## Question Type Classification

The system automatically detects question types using keyword matching:

| Question Type | Keywords Detected |
|---------------|-------------------|
| **asset_count** | "how many asset", "asset count", "assets using", "assets assigned", "list assets" |
| **resignation_assets** | "resign", "return", "offboard", "leave", "quit", "needs refresh", "replacement" |
| **churn_prediction** | "churn", "risk", "leaving", "turnover", "probability", "predict", "likely to leave" |

## Asset Refresh Logic

Assets are analyzed for refresh needs based on age:

| Age | Status | Action |
|-----|--------|--------|
| **>5 years** | URGENT | Must be replaced immediately |
| **3-5 years** | RECOMMENDED | Should be refreshed, plan replacement |
| **<3 years** | OK | Can be reassigned to new employees |

## Technical Implementation

### Files Created/Modified

1. **`src/agent/chatbot_tools.py`** (NEW)
   - `UnifiedChatbotTools` class
   - `get_employee_asset_count()` - Get asset count and details
   - `get_resignation_assets_info()` - Analyze assets for return and refresh needs
   - `classify_question_type()` - Automatic question classification

2. **`src/api/churn.py`** (MODIFIED)
   - Enhanced `/api/churn/chatbot` endpoint
   - Supports all three question types
   - Automatic context retrieval based on question type
   - AI-powered natural language responses

3. **`test_unified_chatbot.py`** (NEW)
   - Comprehensive test suite
   - Usage examples

### Backend Tools Used

- **Asset Count:** Queries `Asset` table by `assigned_to` field
- **Resignation Analysis:** Calculates asset age from `purchase_date`
- **Churn Prediction:** Uses existing `ChurnPredictionTools`
- **AI Response:** Google Gemini 2.0 Flash via LangChain

## Integration with Existing Features

The unified chatbot integrates seamlessly with:

✅ **Asset Health Tracker** - Uses same age calculation logic (3-year threshold)  
✅ **Churn Prediction Agent** - Reuses ML model and prediction tools  
✅ **Employee Lifecycle Management** - Accesses same asset assignment data  

## Testing

### Manual Testing

1. Start the server:
```bash
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --reload
```

2. Test in browser or use curl:
```bash
# Asset count
curl "http://localhost:8000/api/churn/chatbot?question=How+many+assets+is+employee+1+using?&employee_id=1"

# Resignation assets
curl "http://localhost:8000/api/churn/chatbot?question=What+assets+need+refresh+if+employee+2+resigns?&employee_id=2"

# Churn prediction
curl "http://localhost:8000/api/churn/chatbot?question=What+is+churn+risk+for+employee+3?&employee_id=3"
```

### Automated Testing

Run the test suite:
```bash
python test_unified_chatbot.py
```

Tests include:
- Question classification
- Asset count retrieval
- Resignation assets analysis with refresh status
- API usage examples

## Example Scenarios

### Scenario 1: HR Manager Checking Assets

**Q:** *"How many assets is employee 15 currently using?"*

The chatbot will:
1. Classify as `asset_count` question
2. Retrieve all assets assigned to employee 15
3. Group by device type
4. Calculate total value
5. Provide natural language summary with details

### Scenario 2: Planning Employee Offboarding

**Q:** *"If employee 25 resigns, what assets must be returned and which need replacement?"*

The chatbot will:
1. Classify as `resignation_assets` question
2. Get all assets assigned to employee 25
3. Calculate age of each asset
4. Determine refresh status (URGENT/RECOMMENDED/OK)
5. Provide detailed analysis with recommendations

### Scenario 3: Retention Planning

**Q:** *"Is employee 8 at risk of leaving?"*

The chatbot will:
1. Classify as `churn_prediction` question
2. Run ML prediction for employee 8
3. Get top risk factors
4. Provide probability and recommendations

## Best Practices

1. **Always provide employee_id** for specific questions
2. **Use natural language** - The AI understands context
3. **Ask follow-up questions** - The chatbot maintains context
4. **Combine questions** - "What is the churn risk for employee 5 and what assets do they have?"

## Error Handling

- **Employee not found:** Returns error with employee_id
- **No assets:** Returns message "This employee has no assets"
- **API key missing:** Provides fallback message
- **Invalid employee_id:** Returns appropriate error

## Future Enhancements

Potential additions:
- **Multi-employee queries** - "Which employees in IT department have assets needing refresh?"
- **Procurement recommendations** - "How many laptops should we purchase this month?"
- **Cost analysis** - "What is the total cost to replace all aging assets?"
- **Predictive maintenance** - "Which assets are likely to fail soon?"

## Summary

The unified chatbot provides a single, intelligent interface for:
- 📊 **Asset Management** - Track current asset assignments
- 🔄 **Lifecycle Planning** - Determine refresh needs upon employee departure  
- 🎯 **Churn Prediction** - Identify retention risks

All through one API endpoint with natural language interaction! 🚀
