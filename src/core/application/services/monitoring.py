from enum import Enum

class AlertType(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class AlertSeverity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertConfig:
    def __init__(self, alert_type: AlertType, severity: AlertSeverity, message: str):
        self.alert_type = alert_type
        self.severity = severity
        self.message = message

class MonitoringService:
    def __init__(self):
        pass

    def send_alert(self, alert_config: AlertConfig):
        print(f"Alert: {alert_config.alert_type.value} - {alert_config.severity.value} - {alert_config.message}") 