import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../config/theme.dart';
import '../models/event.dart';
import '../widgets/severity_badge.dart';
import '../widgets/countdown_timer.dart';

/// Full-detail screen for a single alert event.
class EventDetailScreen extends StatelessWidget {
  final AlertEvent event;

  const EventDetailScreen({super.key, required this.event});

  @override
  Widget build(BuildContext context) {
    final color = ESPAlertTheme.severityColor(event.severity);
    final emoji = ESPAlertTheme.eventTypeEmoji(event.eventType);

    return Scaffold(
      backgroundColor: ESPAlertTheme.background,
      body: CustomScrollView(
        slivers: [
          // ── Hero header ─────────────────────────────────
          SliverAppBar(
            expandedHeight: 200,
            pinned: true,
            backgroundColor: color.withOpacity(0.3),
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                event.title,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      color.withOpacity(0.4),
                      ESPAlertTheme.background,
                    ],
                  ),
                ),
                child: Center(
                  child: Text(
                    emoji,
                    style: const TextStyle(fontSize: 72),
                  ).animate(
                    onPlay: (c) => c.repeat(reverse: true),
                  ).scale(
                    begin: const Offset(1, 1),
                    end: const Offset(1.1, 1.1),
                    duration: 1500.ms,
                  ),
                ),
              ),
            ),
          ),

          // ── Content ─────────────────────────────────────
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Severity + Countdown row
                  Row(
                    children: [
                      SeverityBadge(severity: event.severity, large: true),
                      const SizedBox(width: 12),
                      if (event.minutesUntilStart != null)
                        CountdownTimer(
                          minutesLeft: event.minutesUntilStart!,
                        ),
                      const Spacer(),
                      Chip(
                        avatar: const Icon(Icons.source, size: 16),
                        label: Text(event.source.toUpperCase()),
                        backgroundColor: ESPAlertTheme.surfaceVariant,
                      ),
                    ],
                  ).animate().fadeIn(delay: 100.ms),

                  const SizedBox(height: 16),

                  // Area
                  if (event.areaName != null && event.areaName!.isNotEmpty)
                    _infoRow(Icons.location_on, 'Zona', event.areaName!),

                  // Earthquake specifics
                  if (event.magnitude != null)
                    _infoRow(Icons.show_chart, 'Magnitud', 'M${event.magnitude}'),
                  if (event.depthKm != null)
                    _infoRow(Icons.height, 'Profundidad', '${event.depthKm} km'),

                  // Time info
                  if (event.effective != null)
                    _infoRow(Icons.play_arrow, 'Inicio',
                        _formatDateTime(event.effective!)),
                  if (event.expires != null)
                    _infoRow(Icons.stop, 'Fin',
                        _formatDateTime(event.expires!)),

                  const Divider(height: 32, color: Colors.white24),

                  // Description
                  if (event.description != null &&
                      event.description!.isNotEmpty) ...[
                    const Text(
                      'Descripción',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      event.description!,
                      style: TextStyle(
                        fontSize: 15,
                        color: Colors.white.withOpacity(0.8),
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // Instructions / Safety
                  if (event.instructions != null &&
                      event.instructions!.isNotEmpty) ...[
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: color.withOpacity(0.3)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.shield, color: color, size: 22),
                              const SizedBox(width: 8),
                              Text(
                                'Recomendaciones',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: color,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(
                            event.instructions!,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.white.withOpacity(0.85),
                              height: 1.6,
                            ),
                          ),
                        ],
                      ),
                    ).animate().fadeIn(delay: 300.ms),
                    const SizedBox(height: 20),
                  ],

                  // Official source link
                  if (event.sourceUrl != null)
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () => _openUrl(event.sourceUrl!),
                        icon: const Icon(Icons.open_in_new),
                        label: const Text('Ver fuente oficial'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: ESPAlertTheme.primary,
                          side: BorderSide(
                              color: ESPAlertTheme.primary.withOpacity(0.5)),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),

                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.white54),
          const SizedBox(width: 10),
          Text(
            '$label: ',
            style: const TextStyle(
              color: Colors.white54,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDateTime(DateTime dt) {
    return '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  void _openUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
