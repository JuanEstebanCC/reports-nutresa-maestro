# Nutresa Maestro Reports API

A FastAPI application that generates reports from the Nutresa Maestro database system, supporting multiple subdomains and Excel export functionality.

## Features

- **Multi-subdomain support**: Connects to multiple database subdomains
- **Report generation**: Aggregates data from all subdomains
- **Excel export**: Generates Excel reports with proper formatting
- **RESTful API**: Clean and documented API endpoints
- **Database connection pooling**: Efficient database connections

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── reports.py      # Report endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   └── database.py        # Database connection management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── report_service.py  # Report generation logic
│       └── excel_service.py   # Excel export functionality
├── static/
│   ├── __init__.py
│   └── subdomains.json        # Subdomain configuration
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. Configure subdomains:
   ```bash
   # Edit static/subdomains.json with your subdomain mappings
   ```

## Configuration

### Environment Variables

- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 3306)
- `DB_USER`: Database username (default: root)
- `DB_PASSWORD`: Database password
- `SUBDOMAINS_FILE`: Path to subdomains configuration file (default: static/subdomains.json)
- `DEBUG`: Enable debug mode
- `ALLOWED_ORIGINS`: CORS allowed origins

### Subdomains Configuration

Edit `static/subdomains.json` to map subdomain names to their corresponding database names:

```json
{
  "subdomain1": "nutresa-subdomain1",
  "subdomain2": "nutresa-subdomain2",
  "subdomain3": "nutresa-subdomain3"
}
```

## Usage

### Start the application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Generate Report (JSON) - First 5 subdomains only
```
GET /api/v1/reports
```

#### Generate Excel Report - First 5 subdomains only
```
GET /api/v1/reports/excel
```

#### Get Available Subdomains
```
GET /api/v1/subdomains
```

#### Test All Subdomains Connection
```
GET /api/v1/test-subdomains
```

#### Health Check
```
GET /health
```

## Report Structure

The generated report includes the following columns:

- **Código de Agente**: Agent code (from authenticated user)
- **Nombre del Agente**: Agent's full name
- **Período de Tiempo**: Time period (formatted as "Month Year", e.g., "Agosto 2025")
- **Variable**: Variable name
- **Meta Asignada**: Assigned goal (max_goal from liquidations)
- **Meta Distribuida**: Distributed goal (actual results achieved)
- **% Meta**: Percentage of goal achieved (Meta Distribuida / Meta Asignada * 100)
- **Incentivo Asignado**: Assigned incentive amount (calculated as points × pointValue)
- **Incentivo Distribuido**: Distributed incentive amount
- **% Variables Completadas**: Percentage of variables completed for the agent in the period

## Database

The application uses **MySQL** as the database system with the following features:

- **Async MySQL driver**: Uses `aiomysql` for asynchronous database operations
- **Connection pooling**: Efficient database connection management
- **Multi-subdomain support**: Connects to different MySQL databases based on subdomain configuration

### Database Queries

The application performs the following main queries:

1. **Main Report Query**: Retrieves user data, liquidations, and role information
2. **Incentive Calculation**: Gets assigned points and point values for incentive calculation
3. **Period Information**: Extracts month information from period data
4. **Variable Information**: Gets variable names by ID

## Error Handling

The application includes comprehensive error handling:
- Database connection errors
- Subdomain processing errors
- Excel generation errors
- API validation errors

## Development

### Code Style

- Uses functions instead of classes where possible
- Follows FastAPI best practices
- Implements proper error handling and logging
- Uses type hints throughout the codebase

### Testing

To test the API endpoints:

```bash
# Test all subdomain connections
curl "http://localhost:8000/api/v1/test-subdomains"

# Generate report (JSON) - first 5 subdomains only
curl "http://localhost:8000/api/v1/reports"

# Generate Excel report - first 5 subdomains only
curl "http://localhost:8000/api/v1/reports/excel" -o nutresa_report_test.xlsx

# Get available subdomains
curl "http://localhost:8000/api/v1/subdomains"

# Health check
curl "http://localhost:8000/health"
```

## License

This project is proprietary software for Nutresa Maestro system.
