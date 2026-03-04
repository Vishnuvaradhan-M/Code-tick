# data/test_incident.py

MOCK_METRICS = {
    "service": "checkout-service",
    "timestamp": "2025-03-07T02:14:00Z",
    "cpu_percent": 94.2,
    "memory_percent": 91.7,
    "error_rate_percent": 22.4,
    "response_time_ms": 4200,
    "normal_response_time_ms": 120,
    "requests_per_second": 847,
    "failed_requests": 189
}

MOCK_COMMITS = [
    {
        "sha": "abc123",
        "message": "Increase database connection pool size from 10 to 100",
        "author": "john.dev@shopeasy.com",
        "timestamp": "2025-03-07T02:11:00Z",
        "files_changed": ["config/database.yml", "config/pool.conf"]
    },
    {
        "sha": "def456",
        "message": "Update structured logging format",
        "author": "sara.dev@shopeasy.com",
        "timestamp": "2025-03-06T23:30:00Z",
        "files_changed": ["src/logger.py"]
    },
    {
        "sha": "ghi789",
        "message": "Fix CSS on landing page",
        "author": "mike.dev@shopeasy.com",
        "timestamp": "2025-03-06T18:00:00Z",
        "files_changed": ["frontend/styles.css"]
    }
]

MOCK_PAST_INCIDENTS = [
    {
        "date": "2024-12-15",
        "cause": "Database connection pool exhaustion",
        "symptoms": "High memory, slow response times",
        "fix": "Rolled back connection pool config change",
        "recovery_minutes": 6
    }
]

INCIDENT_META = {
    "alert_time": "2025-03-07T02:17:00Z",
    "alert_message": "p99 latency exceeded 4000ms on checkout-service",
    "service": "checkout-service",
    "environment": "production"
}