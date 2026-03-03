"""Conectores de salida — framework extensible para enviar alertas a diferentes canales."""

from app.services.output.base import OutputConnector, OutputMessage
from app.services.output.registry import OutputRegistry

__all__ = ["OutputConnector", "OutputMessage", "OutputRegistry"]
