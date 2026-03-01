import 'package:flutter/material.dart';
import '../config/theme.dart';

/// Animated countdown showing time until an event starts.
class CountdownTimer extends StatelessWidget {
  final int minutesLeft;

  const CountdownTimer({super.key, required this.minutesLeft});

  @override
  Widget build(BuildContext context) {
    final hours = minutesLeft ~/ 60;
    final mins = minutesLeft % 60;

    final timeStr = hours > 0
        ? '${hours}h ${mins}m'
        : '${mins}m';

    final urgency = minutesLeft <= 15
        ? ESPAlertTheme.severityRed
        : minutesLeft <= 60
            ? ESPAlertTheme.severityOrange
            : ESPAlertTheme.severityYellow;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: urgency.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: urgency.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.timer, size: 16, color: urgency),
          const SizedBox(width: 6),
          Text(
            'En $timeStr',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: urgency,
            ),
          ),
        ],
      ),
    );
  }
}
