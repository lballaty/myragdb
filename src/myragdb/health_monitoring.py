# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/health_monitoring.py
# Description: Health monitoring and metrics collection for production
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import logging
import psutil
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str
    last_check: datetime = field(default_factory=datetime.now)
    details: Dict = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-level metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_available_mb: float = 0.0
    disk_percent: float = 0.0
    disk_available_mb: float = 0.0
    process_count: int = 0
    thread_count: int = 0


@dataclass
class OperationMetrics:
    """Metrics for operations/requests."""
    operation_name: str
    count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    error_count: int = 0
    last_execution: Optional[datetime] = None

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration."""
        return self.total_duration_ms / self.count if self.count > 0 else 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.count + self.error_count
        return (self.count / total * 100) if total > 0 else 0.0


class HealthMonitor:
    """
    Monitors system and application health.

    Business Purpose: Provides real-time health status and metrics for
    monitoring system performance, detecting issues, and alerting on problems.

    Features:
    - System-level metrics (CPU, memory, disk)
    - Component health tracking
    - Operation performance metrics
    - Health check thresholds
    - Metrics history

    Usage Example:
        monitor = HealthMonitor()
        monitor.register_component_checker('database', check_database_health)

        # In request handler
        monitor.record_operation_duration('search', duration_ms)

        # Get health status
        health = monitor.get_health_status()
    """

    # Default thresholds
    DEFAULT_CPU_THRESHOLD = 80.0
    DEFAULT_MEMORY_THRESHOLD = 85.0
    DEFAULT_DISK_THRESHOLD = 90.0
    DEFAULT_ERROR_RATE_THRESHOLD = 5.0

    def __init__(
        self,
        cpu_threshold: float = DEFAULT_CPU_THRESHOLD,
        memory_threshold: float = DEFAULT_MEMORY_THRESHOLD,
        disk_threshold: float = DEFAULT_DISK_THRESHOLD,
        error_rate_threshold: float = DEFAULT_ERROR_RATE_THRESHOLD,
    ):
        """
        Initialize health monitor.

        Args:
            cpu_threshold: CPU usage alert threshold (percent)
            memory_threshold: Memory usage alert threshold (percent)
            disk_threshold: Disk usage alert threshold (percent)
            error_rate_threshold: Error rate alert threshold (percent)
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.error_rate_threshold = error_rate_threshold

        self.components: Dict[str, ComponentHealth] = {}
        self.component_checkers: Dict[str, callable] = {}
        self.operation_metrics: Dict[str, OperationMetrics] = {}
        self.system_metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000

    def register_component_checker(
        self,
        component_name: str,
        checker: callable,
    ) -> None:
        """
        Register a health check function for a component.

        Args:
            component_name: Name of component
            checker: Callable that returns (status, message, details)
        """
        self.component_checkers[component_name] = checker

    def check_component_health(self, component_name: str) -> ComponentHealth:
        """
        Check health of a specific component.

        Args:
            component_name: Name of component

        Returns:
            ComponentHealth instance
        """
        if component_name not in self.component_checkers:
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.UNKNOWN,
                message=f"No checker registered for {component_name}",
            )

        try:
            checker = self.component_checkers[component_name]
            result = checker()

            if isinstance(result, tuple):
                status, message, details = result
            else:
                status = result.get('status', HealthStatus.UNKNOWN)
                message = result.get('message', '')
                details = result.get('details', {})

            health = ComponentHealth(
                name=component_name,
                status=status,
                message=message,
                details=details,
            )

            self.components[component_name] = health
            return health

        except Exception as e:
            logger.error(f"Error checking health of {component_name}: {e}")
            health = ComponentHealth(
                name=component_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
            )
            self.components[component_name] = health
            return health

    def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system metrics.

        Returns:
            SystemMetrics instance
        """
        try:
            metrics = SystemMetrics(
                cpu_percent=psutil.cpu_percent(interval=0.1),
                memory_percent=psutil.virtual_memory().percent,
                memory_available_mb=psutil.virtual_memory().available / (1024 * 1024),
                disk_percent=psutil.disk_usage('/').percent,
                disk_available_mb=psutil.disk_usage('/').free / (1024 * 1024),
                process_count=len(psutil.pids()),
                thread_count=psutil.Process().num_threads(),
            )

            # Keep history
            self.system_metrics_history.append(metrics)
            if len(self.system_metrics_history) > self.max_history_size:
                self.system_metrics_history.pop(0)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics()

    def record_operation_duration(
        self,
        operation_name: str,
        duration_ms: float,
        error: bool = False,
    ) -> None:
        """
        Record operation execution duration and result.

        Args:
            operation_name: Name of operation
            duration_ms: Duration in milliseconds
            error: Whether operation resulted in error
        """
        if operation_name not in self.operation_metrics:
            self.operation_metrics[operation_name] = OperationMetrics(
                operation_name=operation_name
            )

        metrics = self.operation_metrics[operation_name]

        if error:
            metrics.error_count += 1
        else:
            metrics.count += 1
            metrics.total_duration_ms += duration_ms
            metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
            metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)

        metrics.last_execution = datetime.now()

    def get_operation_metrics(self, operation_name: Optional[str] = None) -> Dict:
        """
        Get operation metrics.

        Args:
            operation_name: Specific operation to get metrics for.
                          If None, returns all metrics.

        Returns:
            Dictionary of metrics
        """
        if operation_name:
            if operation_name in self.operation_metrics:
                metrics = self.operation_metrics[operation_name]
                return {
                    'operation': operation_name,
                    'count': metrics.count,
                    'errors': metrics.error_count,
                    'success_rate': metrics.success_rate,
                    'avg_duration_ms': metrics.avg_duration_ms,
                    'min_duration_ms': metrics.min_duration_ms,
                    'max_duration_ms': metrics.max_duration_ms,
                    'last_execution': metrics.last_execution.isoformat() if metrics.last_execution else None,
                }
            return None

        result = {}
        for op_name, metrics in self.operation_metrics.items():
            result[op_name] = {
                'count': metrics.count,
                'errors': metrics.error_count,
                'success_rate': metrics.success_rate,
                'avg_duration_ms': metrics.avg_duration_ms,
                'min_duration_ms': metrics.min_duration_ms,
                'max_duration_ms': metrics.max_duration_ms,
            }
        return result

    def get_health_status(self) -> Dict:
        """
        Get overall health status.

        Returns:
            Dictionary with health status and metrics
        """
        system_metrics = self.get_system_metrics()
        overall_status = HealthStatus.HEALTHY

        # Check system metrics
        alerts = []
        if system_metrics.cpu_percent > self.cpu_threshold:
            alerts.append(f"High CPU usage: {system_metrics.cpu_percent}%")
            overall_status = HealthStatus.DEGRADED

        if system_metrics.memory_percent > self.memory_threshold:
            alerts.append(f"High memory usage: {system_metrics.memory_percent}%")
            overall_status = HealthStatus.DEGRADED

        if system_metrics.disk_percent > self.disk_threshold:
            alerts.append(f"High disk usage: {system_metrics.disk_percent}%")
            overall_status = HealthStatus.DEGRADED

        # Check component health
        component_statuses = []
        for component_name, health in self.components.items():
            component_statuses.append({
                'name': component_name,
                'status': health.status.value,
                'message': health.message,
                'details': health.details,
                'last_check': health.last_check.isoformat(),
            })

            if health.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY

        # Check operation error rates
        operation_statuses = []
        for op_name, metrics in self.operation_metrics.items():
            if metrics.success_rate < (100 - self.error_rate_threshold):
                alerts.append(f"High error rate for {op_name}: {100 - metrics.success_rate:.1f}%")
                overall_status = HealthStatus.DEGRADED

            operation_statuses.append({
                'operation': op_name,
                'success_rate': metrics.success_rate,
                'avg_duration_ms': metrics.avg_duration_ms,
            })

        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                'cpu_percent': system_metrics.cpu_percent,
                'memory_percent': system_metrics.memory_percent,
                'memory_available_mb': system_metrics.memory_available_mb,
                'disk_percent': system_metrics.disk_percent,
                'disk_available_mb': system_metrics.disk_available_mb,
            },
            'components': component_statuses,
            'operations': operation_statuses,
            'alerts': alerts,
        }
