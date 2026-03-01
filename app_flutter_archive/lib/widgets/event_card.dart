import 'package:flutter/material.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../config/theme.dart';
import '../models/event.dart';
import 'severity_badge.dart';

/// Card widget displaying a single alert event.
class EventCard extends StatelessWidget {
  final AlertEvent event;
  final bool compact;

  const EventCard({super.key, required this.event, this.compact = true});

  @override
  Widget build(BuildContext context) {
    final color = ESPAlertTheme.severityColor(event.severity);
    final emoji = ESPAlertTheme.eventTypeEmoji(event.eventType);

    return Container(
      decoration: BoxDecoration(
        color: ESPAlertTheme.surfaceVariant,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.1),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Emoji + type
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(emoji, style: const TextStyle(fontSize: 22)),
                ),
                const SizedBox(width: 12),

                // Title + area
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        event.title,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (event.areaName != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          event.areaName!,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.white.withOpacity(0.5),
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ],
                  ),
                ),

                // Severity badge
                SeverityBadge(severity: event.severity),
              ],
            ),

            if (!compact && event.description != null) ...[
              const SizedBox(height: 10),
              Text(
                event.description!,
                style: TextStyle(
                  fontSize: 13,
                  color: Colors.white.withOpacity(0.7),
                  height: 1.4,
                ),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],

            const SizedBox(height: 8),

            // Bottom row: source + time
            Row(
              children: [
                // Source chip
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: ESPAlertTheme.surface,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    event.source.toUpperCase(),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: Colors.white.withOpacity(0.5),
                      letterSpacing: 0.5,
                    ),
                  ),
                ),

                // Earthquake magnitude
                if (event.magnitude != null) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: ESPAlertTheme.seismicColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      'M${event.magnitude}',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: ESPAlertTheme.seismicColor,
                      ),
                    ),
                  ),
                ],

                const Spacer(),

                // Countdown or time ago
                if (event.minutesUntilStart != null)
                  Text(
                    '⏱️ en ${event.minutesUntilStart} min',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: color,
                    ),
                  )
                else
                  Text(
                    timeago.format(event.createdAt, locale: 'es'),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.white.withOpacity(0.4),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
