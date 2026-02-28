"""
Monitoring service for fetching GCP Cloud Monitoring metrics.
Provides system metrics for the monitoring dashboard.
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Cloud Monitoring imports
try:
    from google.cloud import monitoring_v3
    from google.cloud.monitoring_v3 import query
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """Container for metric data points."""
    value: float
    timestamp: datetime
    label: str = ""

class MonitoringService:
    """Service for fetching GCP Cloud Monitoring metrics."""
    
    def __init__(self):
        """Initialize the monitoring service."""
        self.client = None
        self.project_id = os.getenv('GCP_PROJECT_ID')
        
        if MONITORING_AVAILABLE and self.project_id:
            try:
                self.client = monitoring_v3.MetricServiceClient()
                logger.info("Cloud Monitoring client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Cloud Monitoring client: {e}")
        else:
            logger.info("Cloud Monitoring not available (missing dependencies or project ID)")
    
    def get_cloud_run_metrics(self) -> Dict[str, Any]:
        """Fetch Cloud Run metrics."""
        if not self.client or not self.project_id:
            return self._get_fallback_metrics("cloud_run")
        
        try:
            # Get metrics for the last hour
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            # Convert to protobuf timestamps
            start_seconds = int(start_time.timestamp())
            end_seconds = int(end_time.timestamp())
            
            project_name = f"projects/{self.project_id}"
            
            # Request count metric
            request_count = self._fetch_metric(
                project_name,
                'run.googleapis.com/request_count',
                start_seconds,
                end_seconds
            )
            
            # Response latency metric
            response_latency = self._fetch_metric(
                project_name,
                'run.googleapis.com/request_latencies',
                start_seconds,
                end_seconds
            )
            
            # Error rate metric
            error_count = self._fetch_metric(
                project_name,
                'run.googleapis.com/request_count',
                start_seconds,
                end_seconds,
                filter_str='metric.response_code_class != "2xx"'
            )
            
            return {
                "request_count": request_count,
                "avg_latency_ms": response_latency,
                "error_rate": error_count / max(request_count, 1) * 100,
                "active_instances": 1,  # Simplified for demo
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching Cloud Run metrics: {e}")
            return self._get_fallback_metrics("cloud_run")
    
    def get_cloud_sql_metrics(self) -> Dict[str, Any]:
        """Fetch Cloud SQL metrics."""
        if not self.client or not self.project_id:
            return self._get_fallback_metrics("cloud_sql")
        
        try:
            # Get metrics for the last hour
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            start_seconds = int(start_time.timestamp())
            end_seconds = int(end_time.timestamp())
            
            project_name = f"projects/{self.project_id}"
            
            # Database connections
            connections = self._fetch_metric(
                project_name,
                'cloudsql.googleapis.com/database/num_backends',
                start_seconds,
                end_seconds
            )
            
            # CPU utilization
            cpu_util = self._fetch_metric(
                project_name,
                'cloudsql.googleapis.com/database/cpu/utilization',
                start_seconds,
                end_seconds
            )
            
            return {
                "active_connections": connections,
                "cpu_utilization": cpu_util,
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching Cloud SQL metrics: {e}")
            return self._get_fallback_metrics("cloud_sql")
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics."""
        return {
            "uptime_seconds": int(time.time() - os.path.getctime(__file__)),
            "environment": os.getenv('APP_ENVIRONMENT', 'development'),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all available metrics."""
        return {
            "cloud_run": self.get_cloud_run_metrics(),
            "cloud_sql": self.get_cloud_sql_metrics(),
            "application": self.get_application_metrics(),
            "status": "healthy" if self.client else "limited"
        }
    
    def _fetch_metric(self, project_name: str, metric_type: str, 
                     start_seconds: int, end_seconds: int, 
                     filter_str: str = "") -> float:
        """Fetch a specific metric from Cloud Monitoring."""
        try:
            # Create time interval
            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": end_seconds},
                "start_time": {"seconds": start_seconds}
            })
            
            # Create filter
            filter_string = f'metric.type = "{metric_type}"'
            if filter_str:
                filter_string += f' AND {filter_str}'
            
            # List time series
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": project_name,
                "filter": filter_string,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
            })
            
            response = self.client.list_time_series(request=request)
            
            # Extract the latest value
            latest_value = 0.0
            for series in response:
                if series.points:
                    latest_point = series.points[-1]
                    if latest_point.value.double_value:
                        latest_value = latest_point.value.double_value
                    elif latest_point.value.int64_value:
                        latest_value = float(latest_point.value.int64_value)
            
            return latest_value
            
        except Exception as e:
            logger.error(f"Error fetching metric {metric_type}: {e}")
            return 0.0
    
    def _get_fallback_metrics(self, service_type: str) -> Dict[str, Any]:
        """Return fallback metrics when Cloud Monitoring is unavailable."""
        base_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unavailable"
        }
        
        if service_type == "cloud_run":
            return {
                **base_metrics,
                "request_count": 0,
                "avg_latency_ms": 0,
                "error_rate": 0,
                "active_instances": 1
            }
        elif service_type == "cloud_sql":
            return {
                **base_metrics,
                "active_connections": 0,
                "cpu_utilization": 0
            }
        else:
            return base_metrics



