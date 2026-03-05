---
name: "🔌 Output Connector Request"
about: Propose a new output channel for alert notifications
title: "[CONNECTOR] "
labels: ["enhancement", "output-connector"]
assignees: ""
---

## Output channel

**Platform:** <!-- e.g. Telegram, Slack, NTFY, Matrix, MQTT, SMS, etc. -->
**API documentation:** <!-- Link to the service's API -->

## Description

<!-- How should the connector work? What message format? -->

## Target format

<!-- What identifies the recipient? e.g. chat_id, webhook_url, email, topic, etc. -->

## Priority

- [ ] Basic (plain text only)
- [ ] Rich formatting (HTML, embeds, etc.)
- [ ] With images (maps, charts)
- [ ] Bidirectional (user can reply)

## Usage example

```python
# How would it ideally be used?
connector = MyConnector(token="...")
await connector.send(message, target="@my_channel")
```

## Checklist

- [ ] The service has a public API or Python SDK
- [ ] An integration can be created at no cost
- [ ] I have checked that no similar issue already exists
