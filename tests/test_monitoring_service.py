"""
Unit tests for the MonitoringService class.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.services.monitoring_service import MonitoringService, MetricData


class TestMonitoringService:
    """Test cases for MonitoringService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = MonitoringService()
    
    def test_initialization_without_project_id(self):
        """Test service initialization without GCP project ID."""
        with patch.dict(os.environ, {}, clear=True):
            service = MonitoringService()
            assert service.project_id is None
            assert service.client is None
    
    def test_initialization_with_project_id(self):
        """Test service initialization with GCP project ID."""
        with patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'}):
            with patch('src.services.monitoring_service.monitoring_v3.MetricServiceClient') as mock_client:
                service = MonitoringService()
                assert service.project_id == 'test-project'
                assert service.client is not None
    
    def test_get_application_metrics(self):
        """Test getting application metrics."""
        metrics = self.service.get_application_metrics()
        
        assert 'uptime_seconds' in metrics
        assert 'environment' in metrics
        assert 'timestamp' in metrics
        assert isinstance(metrics['uptime_seconds'], (int, float))
        assert isinstance(metrics['timestamp'], str)
    
    def test_get_fallback_metrics_cloud_run(self):
        """Test fallback metrics for Cloud Run."""
        metrics = self.service._get_fallback_metrics("cloud_run")
        
        expected_keys = ['timestamp', 'status', 'request_count', 'avg_latency_ms', 'error_rate', 'active_instances']
        for key in expected_keys:
            assert key in metrics
        
        assert metrics['status'] == 'unavailable'
        assert metrics['request_count'] == 0
        assert metrics['avg_latency_ms'] == 0
        assert metrics['error_rate'] == 0
        assert metrics['active_instances'] == 1
    
    def test_get_fallback_metrics_cloud_sql(self):
        """Test fallback metrics for Cloud SQL."""
        metrics = self.service._get_fallback_metrics("cloud_sql")
        
        expected_keys = ['timestamp', 'status', 'active_connections', 'cpu_utilization']
        for key in expected_keys:
            assert key in metrics
        
        assert metrics['status'] == 'unavailable'
        assert metrics['active_connections'] == 0
        assert metrics['cpu_utilization'] == 0
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        metrics = self.service.get_all_metrics()
        
        assert 'cloud_run' in metrics
        assert 'cloud_sql' in metrics
        assert 'application' in metrics
        assert 'status' in metrics
        
        # Check that all sections have required keys
        assert 'timestamp' in metrics['cloud_run']
        assert 'timestamp' in metrics['cloud_sql']
        assert 'timestamp' in metrics['application']
    
    @patch('src.services.monitoring_service.monitoring_v3.MetricServiceClient')
    def test_get_cloud_run_metrics_with_client(self, mock_client_class):
        """Test getting Cloud Run metrics with monitoring client."""
        # Mock the client and its methods
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock the list_time_series method to return empty response
        mock_client.list_time_series.return_value = []
        
        # Set up service with mocked client
        self.service.client = mock_client
        self.service.project_id = 'test-project'
        
        metrics = self.service.get_cloud_run_metrics()
        
        assert 'request_count' in metrics
        assert 'avg_latency_ms' in metrics
        assert 'error_rate' in metrics
        assert 'active_instances' in metrics
        assert 'timestamp' in metrics
    
    @patch('src.services.monitoring_service.monitoring_v3.MetricServiceClient')
    def test_get_cloud_sql_metrics_with_client(self, mock_client_class):
        """Test getting Cloud SQL metrics with monitoring client."""
        # Mock the client and its methods
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock the list_time_series method to return empty response
        mock_client.list_time_series.return_value = []
        
        # Set up service with mocked client
        self.service.client = mock_client
        self.service.project_id = 'test-project'
        
        metrics = self.service.get_cloud_sql_metrics()
        
        assert 'active_connections' in metrics
        assert 'cpu_utilization' in metrics
        assert 'timestamp' in metrics
    
    def test_fetch_metric_without_client(self):
        """Test _fetch_metric without monitoring client."""
        result = self.service._fetch_metric("projects/test", "test.metric", 0, 1)
        assert result == 0.0
    
    @patch('src.services.monitoring_service.monitoring_v3.MetricServiceClient')
    def test_fetch_metric_with_client_error(self, mock_client_class):
        """Test _fetch_metric with client error."""
        # Mock the client to raise an exception
        mock_client = Mock()
        mock_client.list_time_series.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        
        self.service.client = mock_client
        self.service.project_id = 'test-project'
        
        result = self.service._fetch_metric("projects/test", "test.metric", 0, 1)
        assert result == 0.0
    
    @patch('src.services.monitoring_service.monitoring_v3.MetricServiceClient')
    def test_fetch_metric_with_data(self, mock_client_class):
        """Test _fetch_metric with actual data."""
        # Mock the client and response
        mock_client = Mock()
        mock_point = Mock()
        mock_point.value.double_value = 42.5
        
        mock_series = Mock()
        mock_series.points = [mock_point]
        
        mock_client.list_time_series.return_value = [mock_series]
        mock_client_class.return_value = mock_client
        
        self.service.client = mock_client
        self.service.project_id = 'test-project'
        
        result = self.service._fetch_metric("projects/test", "test.metric", 0, 1)
        assert result == 42.5
    
    def test_metric_data_dataclass(self):
        """Test MetricData dataclass."""
        now = datetime.utcnow()
        metric = MetricData(value=123.45, timestamp=now, label="test")
        
        assert metric.value == 123.45
        assert metric.timestamp == now
        assert metric.label == "test"
    
    def test_error_handling_in_get_cloud_run_metrics(self):
        """Test error handling in get_cloud_run_metrics."""
        # Mock client to raise exception
        self.service.client = Mock()
        self.service.client.list_time_series.side_effect = Exception("Test error")
        self.service.project_id = 'test-project'
        
        metrics = self.service.get_cloud_run_metrics()
        
        # Should return fallback metrics
        assert metrics['status'] == 'unavailable'
        assert 'request_count' in metrics
    
    def test_error_handling_in_get_cloud_sql_metrics(self):
        """Test error handling in get_cloud_sql_metrics."""
        # Mock client to raise exception
        self.service.client = Mock()
        self.service.client.list_time_series.side_effect = Exception("Test error")
        self.service.project_id = 'test-project'
        
        metrics = self.service.get_cloud_sql_metrics()
        
        # Should return fallback metrics
        assert metrics['status'] == 'unavailable'
        assert 'active_connections' in metrics



