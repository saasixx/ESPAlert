import 'package:flutter/material.dart';
import '../config/theme.dart';

/// Colored badge showing alert severity level.
class SeverityBadge extends StatelessWidget {
  final String severity;
  final bool large;

  const SeverityBadge({
    super.key,
    required this.severity,
    this.large = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = ESPAlertTheme.severityColor(severity);
    final label = ESPAlertTheme.severityLabel(severity);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: large ? 14 : 10,
        vertical: large ? 6 : 4,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(large ? 12 : 8),
        border: Border.all(color: color.withOpacity(0.6)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: large ? 13 : 10,
          fontWeight: FontWeight.w800,
          color: color,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
