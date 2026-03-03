---
name: "\U0001F50C Solicitud de conector de salida"
about: Proponer un nuevo canal de salida para notificaciones de alertas
title: "[CONNECTOR] "
labels: ["enhancement", "output-connector"]
assignees: ""
---

## Canal de salida

**Plataforma:** <!-- e.g. Telegram, Slack, NTFY, Matrix, MQTT, SMS, etc. -->
**Documentación API:** <!-- Enlace a la API del servicio -->

## Descripción

<!-- ¿Cómo debería funcionar el conector? ¿Qué formato de mensaje? -->

## Formato del destino (target)

<!-- ¿Qué identifica al destinatario? e.g. chat_id, webhook_url, email, topic, etc. -->

## Prioridad

- [ ] Básico (solo texto plano)
- [ ] Con formato rico (HTML, embeds, etc.)
- [ ] Con imágenes (mapas, gráficos)
- [ ] Bidireccional (el usuario puede responder)

## Ejemplo de uso

```python
# ¿Cómo se usaría idealmente?
connector = MiConector(token="...")
await connector.send(message, target="@mi_canal")
```

## Checklist

- [ ] El servicio tiene API pública o SDK en Python
- [ ] Se puede crear una integración sin coste
- [ ] He revisado que no exista ya un issue similar
