"""Output connectors — extensible framework for sending alerts to different channels."""

from app.services.output.base import OutputConnector, OutputMessage
from app.services.output.registry import OutputRegistry

__all__ = ["OutputConnector", "OutputMessage", "OutputRegistry"]
