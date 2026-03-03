"""Utilidades comunes de validación para esquemas Pydantic."""

import re

# Contraseña: mín. 8 caracteres, al menos 1 mayúscula, 1 minúscula, 1 dígito
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$")


def sanitize_html(value: str) -> str:
    """Elimina etiquetas HTML de una cadena."""
    return re.sub(r"<[^>]+>", "", value).strip()
