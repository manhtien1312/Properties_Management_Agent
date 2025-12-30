# Properties Management API

FastAPI backend service for employee and asset management with SQLite database.

## Project Structure

```
src/
├── api/                           # API routes
│   ├── employees.py              # Employee CRUD endpoints
│   └── assets.py                 # Asset CRUD endpoints
├── database/
│   ├── database.py               # Database connection and session
│   ├── models.py                 # SQLAlchemy ORM models
│   └── init_db.py                # Database initialization script
├── service/
│   └── employee_asset_service.py # Business logic layer
├── schemas.py                     # Pydantic request/response schemas
└── main.py                        # FastAPI app initialization
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database (if not already done)

```bash
python src/database/init_db.py
```

This will create `properties_management.db` with 150 employees, 180 assets, and 1,800+ HR analytics records.

### 3. Run the Server

```bash
python -m uvicorn src.main:app --reload
```

The server will start at `http://localhost:8000`

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Employee Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/employees/` | Create new employee |
| GET | `/api/employees/` | Get all employees (with filters) |
| GET | `/api/employees/{employee_id}` | Get employee by ID |
| PUT | `/api/employees/{employee_id}` | Update employee |
| DELETE | `/api/employees/{employee_id}` | Delete employee |
| GET | `/api/employees/count/` | Get total employee count |

**Query Parameters for GET /api/employees/**:
- `skip`: Skip N records (default: 0)
- `limit`: Return N records (default: 100, max: 500)
- `department`: Filter by department (marketing, it)
- `manager_id`: Filter by manager ID
- `status`: Filter by status (active, resigned, notice_period)

### Asset Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/assets/` | Create new asset |
| GET | `/api/assets/` | Get all assets (with filters) |
| GET | `/api/assets/{asset_id}` | Get asset by ID |
| GET | `/api/assets/tag/{asset_tag}` | Get asset by tag |
| GET | `/api/assets/serial/{serial_number}` | Get asset by serial |
| PUT | `/api/assets/{asset_id}` | Update asset |
| DELETE | `/api/assets/{asset_id}` | Delete asset |
| GET | `/api/assets/count/` | Get total asset count |

**Query Parameters for GET /api/assets/**:
- `skip`: Skip N records (default: 0)
- `limit`: Return N records (default: 100, max: 500)
- `device_type`: Filter by type (laptop, monitor, phone)
- `status`: Filter by status (assigned, returned, lost, damaged, available)
- `employee_id`: Filter by assigned employee
- `condition`: Filter by condition (excellent, good, fair, poor, damaged)

## Example API Calls

### Create Employee
```bash
curl -X POST "http://localhost:8000/api/employees/" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john.doe@company.com",
    "department": "it",
    "role": "staff",
    "hire_date": "2023-01-15",
    "location": "New York",
    "work_mode": "hybrid"
  }'
```

### Get All Employees
```bash
curl "http://localhost:8000/api/employees/?limit=10&department=it"
```

### Update Employee
```bash
curl -X PUT "http://localhost:8000/api/employees/1" \
  -H "Content-Type: application/json" \
  -d '{
    "employment_status": "resigned",
    "resignation_date": "2024-12-30"
  }'
```

### Create Asset
```bash
curl -X POST "http://localhost:8000/api/assets/" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_tag": "AST-000001",
    "serial_number": "SN123456",
    "device_type": "laptop",
    "brand": "Dell",
    "model": "XPS 13",
    "purchase_date": "2023-06-15",
    "purchase_value": 1500.00,
    "current_value": 1200.00,
    "location": "New York",
    "warranty_expiry": "2025-06-15"
  }'
```

### Get Assets by Type
```bash
curl "http://localhost:8000/api/assets/?device_type=laptop"
```

## Architecture Layers

### 1. **API Layer** (`src/api/`)
- Handles HTTP requests/responses
- Input validation with Pydantic
- Error handling and status codes

### 2. **Service Layer** (`src/service/`)
- Contains business logic
- Database operations (CRUD)
- Data transformations
- Reusable across different endpoints

### 3. **ORM Layer** (`src/database/models.py`)
- SQLAlchemy models
- Database table definitions
- Relationships between tables

### 4. **Schema Layer** (`src/schemas.py`)
- Pydantic models for request/response validation
- Type hints and field constraints
- Automatic API documentation

## Database Models

### Employee
- Primary Key: `employee_id` (auto-increment)
- Fields: Full name, email, department, role, hire date, tenure, employment status, etc.
- Relationships: Manager (self-reference), Assets, HR Analytics

### Asset
- Primary Key: `asset_id` (auto-increment)
- Unique Fields: `asset_tag`, `serial_number`
- Fields: Device type, brand, model, purchase info, condition, status, etc.
- Relationships: Assigned Employee

### HR_Analytic
- Primary Key: `record_id` (auto-increment)
- Foreign Key: `employee_id`
- Fields: Performance rating, engagement score, promotions, training hours, etc.

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK`: Successful GET/PUT
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Database Location

The SQLite database file is located at: `src/database/properties_management.db`

To reset the database, simply delete the `.db` file and run `init_db.py` again.
