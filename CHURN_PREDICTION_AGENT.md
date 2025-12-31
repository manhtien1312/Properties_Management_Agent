# Employee Churn Prediction Agent

## Overview

The **Employee Churn Prediction Agent** uses machine learning to predict which employees are at risk of resigning within the next 6 months. It provides:

- **Probability scores** (0.0 to 1.0)
- **Risk categories** (High/Medium/Low)
- **Feature importance** (top contributing factors)
- **Conversational chatbot** for Q&A about predictions

## Features

### 1. **Individual Churn Prediction**
Predict resignation risk for any employee using 16 behavioral and performance features.

### 2. **High-Risk Employee Detection**
Identify all employees with high churn probability for proactive retention.

### 3. **Batch Predictions**
Process multiple employees at once for team-wide risk assessment.

### 4. **AI Chatbot**
Ask natural language questions about churn predictions and get intelligent answers.

### 5. **Feature Importance Analysis**
Understand which factors contribute most to churn risk.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New ML dependencies:
- pandas==2.1.4
- numpy==1.26.2  
- scikit-learn==1.3.2
- xgboost==2.0.3

### 2. Generate Training Dataset

```bash
python src/ml/generate_churn_dataset.py
```

This creates `src/ml/churn_training_data.csv` with 1000 synthetic employee records.

### 3. Train the Model

```bash
python src/ml/train_churn_model.py
```

This trains an XGBoost classifier and saves:
- `src/ml/churn_model.pkl` - Trained model
- `src/ml/churn_model_metadata.json` - Model metadata and metrics

Expected output:
```
Accuracy:  0.85+
Precision: 0.80+
Recall:    0.75+
F1 Score:  0.77+
ROC AUC:   0.90+
```

### 4. Start the Server

```bash
python -m uvicorn src.main:app --reload
```

## API Endpoints

### 1. Predict Individual Employee

**Endpoint:** `GET /api/churn/predict/{employee_id}`

**Example:**
```bash
curl "http://localhost:8000/api/churn/predict/5"
```

**Response:**
```json
{
  "success": true,
  "employee_id": 5,
  "employee_name": "John Smith",
  "prediction": 1,
  "probability": 0.823,
  "risk_category": "High",
  "risk_level": 3,
  "top_factors": [
    {
      "feature": "engagement_score_latest",
      "value": 2.3,
      "importance": 0.145,
      "is_risk_factor": true
    },
    {
      "feature": "months_since_last_promotion",
      "value": 36,
      "importance": 0.132,
      "is_risk_factor": true
    }
  ],
  "model_info": {
    "model_type": "XGBoost",
    "model_version": "1.0",
    "accuracy": 0.87
  }
}
```

### 2. Get High-Risk Employees

**Endpoint:** `GET /api/churn/high-risk?min_probability=0.7`

**Example:**
```bash
curl "http://localhost:8000/api/churn/high-risk?min_probability=0.7"
```

**Response:**
```json
{
  "success": true,
  "total_employees": 150,
  "high_risk_count": 12,
  "threshold": 0.7,
  "high_risk_employees": [
    {
      "employee_id": 5,
      "employee_name": "John Smith",
      "probability": 0.823,
      "risk_category": "High",
      "top_factor": {
        "feature": "engagement_score_latest",
        "value": 2.3
      }
    }
  ]
}
```

### 3. Get Model Information

**Endpoint:** `GET /api/churn/model/info`

**Example:**
```bash
curl "http://localhost:8000/api/churn/model/info"
```

**Response:**
```json
{
  "success": true,
  "model_type": "XGBoost",
  "model_version": "1.0",
  "trained_date": "2025-12-31T10:30:00",
  "n_features": 16,
  "feature_names": [...],
  "metrics": {
    "accuracy": 0.87,
    "precision": 0.82,
    "recall": 0.78,
    "f1_score": 0.80,
    "roc_auc": 0.92
  },
  "top_features": [...]
}
```

### 4. Batch Predictions

**Endpoint:** `POST /api/churn/batch-predict`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/churn/batch-predict" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3, 4, 5]'
```

### 5. AI Chatbot

**Endpoint:** `GET /api/churn/chatbot?question=...&employee_id=...`

**Examples:**

```bash
# General question
curl "http://localhost:8000/api/churn/chatbot?question=What%20is%20employee%20churn?"

# Employee-specific question
curl "http://localhost:8000/api/churn/chatbot?question=Why%20might%20this%20employee%20leave?&employee_id=5"

# Actionable question
curl "http://localhost:8000/api/churn/chatbot?question=What%20can%20we%20do%20to%20reduce%20churn?"
```

**Response:**
```json
{
  "success": true,
  "question": "Why might employee 5 leave?",
  "answer": "Based on the prediction data, Employee 5 (John Smith) has an 82.3% probability of leaving within 6 months. The top risk factors are:\n\n1. **Low Engagement Score** (2.3/5.0) - The employee shows significantly lower engagement than healthy levels (3.5+).\n\n2. **Long Time Since Promotion** (36 months) - No career advancement in 3 years can lead to frustration.\n\n3. **Declining Performance Trend** - Performance ratings have decreased over time.\n\nRecommended Actions:\n- Schedule 1-on-1 to understand concerns\n- Discuss career development opportunities\n- Consider promotion or lateral move\n- Review compensation and benefits",
  "context": {
    "employee_id": 5,
    "has_prediction_data": true
  }
}
```

## Features Used for Prediction

| Feature | Description | Risk Indicator |
|---------|-------------|----------------|
| tenure_months | Employee tenure | Very low or very high |
| months_since_last_promotion | Time since last promotion | > 24 months |
| salary_change_percent_1y | Salary change in past year | < 5% |
| performance_rating_avg | Average performance (2 years) | < 3.5 |
| performance_rating_trend | Performance trend | Negative |
| sick_days_ytd | Sick days this year | > 10 |
| unplanned_leaves_ytd | Unplanned absences | > 5 |
| engagement_score_latest | Latest engagement score | < 3.5 |
| engagement_score_trend | Engagement trend | Negative |
| manager_changes | Manager changes (2 years) | > 1 |
| department_changes | Department transfers | > 1 |
| training_hours_ytd | Training hours | < 30 |
| overtime_hours_avg | Average monthly overtime | > 25 hours |
| remote_work_percent | Remote work percentage | < 40% |
| project_count | Active projects | < 2 |
| reports_count | Direct reports | Varies |

## Risk Categories

| Category | Probability | Action |
|----------|-------------|--------|
| **High** | 70%+ | Immediate intervention needed |
| **Medium** | 40-70% | Monitor closely, retention actions |
| **Low** | <40% | No immediate concern |

## Use Cases

### 1. Proactive Retention
Identify at-risk employees before they resign:
```bash
curl "http://localhost:8000/api/churn/high-risk"
```

### 2. Exit Interview Preparation
Check churn risk before exit interview:
```bash
curl "http://localhost:8000/api/churn/predict/42"
```

### 3. Team Health Assessment
Batch predict for entire team:
```bash
curl -X POST "http://localhost:8000/api/churn/batch-predict" \
  -H "Content-Type: application/json" \
  -d '[10, 11, 12, 13, 14]'
```

### 4. Strategic Insights
Ask chatbot for recommendations:
```bash
curl "http://localhost:8000/api/churn/chatbot?question=What%20are%20the%20top%20reasons%20employees%20leave?"
```

## Chatbot Q&A Examples

**General Questions:**
- "What factors predict employee churn?"
- "How accurate is the churn model?"
- "What can managers do to reduce turnover?"

**Employee-Specific:**
- "Why might employee 5 be at risk?" (with employee_id=5)
- "What retention strategies would work for this employee?" (with employee_id)
- "Should we be concerned about this person leaving?" (with employee_id)

**Actionable Insights:**
- "What are early warning signs of churn?"
- "How can we improve engagement scores?"
- "What's the ROI of retention programs?"

## Model Retraining

To retrain with updated data:

1. Update `src/ml/churn_training_data.csv` with real employee data
2. Run training script:
```bash
python src/ml/train_churn_model.py
```
3. Restart server to load new model

## Integration Examples

### With Employee Dashboard
```python
# In employee profile view
employee_id = 5
churn_result = requests.get(f"http://localhost:8000/api/churn/predict/{employee_id}").json()

if churn_result['risk_category'] == 'High':
    display_warning("⚠️ High Churn Risk - Retention Action Needed")
```

### With HR Workflows
```python
# Weekly high-risk report
high_risk = requests.get("http://localhost:8000/api/churn/high-risk?min_probability=0.7").json()

for employee in high_risk['high_risk_employees']:
    send_notification_to_manager(employee['employee_id'], employee['probability'])
```

### With Chatbot UI
```javascript
// User asks question
const response = await fetch(
  `http://localhost:8000/api/churn/chatbot?question=${encodeURIComponent(question)}&employee_id=${empId}`
);
const data = await response.json();
displayChatMessage(data.answer);
```

## Troubleshooting

### Model Not Found
```
Error: Model not available
```
**Solution:** Run `python src/ml/train_churn_model.py` to generate the model

### No HR Analytics Data
```
Error: No HR analytics data found for employee
```
**Solution:** Employee needs HR analytics records in the database

### Low Accuracy
**Solution:** 
- Add more training data
- Retrain with real employee data
- Adjust model hyperparameters in `train_churn_model.py`

## Performance

- **Prediction Time:** <50ms per employee
- **Batch Processing:** ~100 employees in <2 seconds
- **Model Size:** ~500KB
- **Memory Usage:** ~50MB when loaded

## Future Enhancements

- [ ] Real-time predictions via webhooks
- [ ] Automated retention campaign triggers
- [ ] Integration with performance review system
- [ ] Manager dashboard with team churn risks
- [ ] Historical trend analysis
- [ ] Cost-benefit analysis of retention
- [ ] Personalized retention recommendations
- [ ] Multi-model ensemble predictions
