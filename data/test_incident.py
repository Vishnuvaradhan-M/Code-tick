# data/test_incident.py

MOCK_METRICS = {
    "service":            "checkout-service",
    "timestamp":          "2026-03-07T02:17:00Z",
    "cpu_percent":        94,
    "memory_percent":     91,
    "error_rate_percent": 22.0,
    "response_time_ms":   3200,
    "normal_cpu":         20,
    "normal_memory":      40,
    "normal_error_rate":  1.0,
    "normal_response_ms": 120,
    "spike_start_time":   "2026-03-07T02:14:00Z"
}

MOCK_COMMITS = [
    {
        "sha":           "a1b2c3d",
        "message":       "Initial checkout service setup - DB pool size: 10",
        "author":        "dev-team",
        "timestamp":     "2026-03-07T01:00:00Z",
        "files_changed": ["app.py", "requirements.txt"]
    },
    {
        "sha":           "e4f5g6h",
        "message":       "Add connection retry logic and circuit breaker",
        "author":        "dev-team",
        "timestamp":     "2026-03-07T01:30:00Z",
        "files_changed": ["app.py", "config.py"]
    },
    {
        "sha":           "i7j8k9l",
        "message":       "Performance tuning - Redis cache layer added",
        "author":        "dev-team",
        "timestamp":     "2026-03-07T01:45:00Z",
        "files_changed": ["config.py", "cache.py"]
    },
    {
        "sha":           "abc123x",
        "message":       "Increase DB connection pool from 10 to 100 for peak load",
        "author":        "dev-team",
        "timestamp":     "2026-03-07T02:11:00Z",
        "files_changed": ["config.py", "database.py"],
        "risk_flag":     "config_change"
    }
]

MOCK_PAST_INCIDENTS = [
    {
        "date":       "2026-02-15",
        "cause":      "Memory leak in connection pool",
        "resolution": "Rollback config, restart service",
        "duration":   "38 minutes"
    }
]

INCIDENT_META = {
    "service_name": "checkout-service",
    "alert_time":   "2026-03-07T02:17:00Z",
    "alert_type":   "P1 - Service Degraded",
    "environment":  "production"
}