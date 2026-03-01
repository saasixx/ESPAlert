import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../config/theme.dart';
import '../models/event.dart';
import '../providers/events_provider.dart';
import '../widgets/event_card.dart';
import 'event_detail.dart';

/// Timeline screen — events sorted chronologically with time slider.
class TimelineScreen extends StatefulWidget {
  const TimelineScreen({super.key});

  @override
  State<TimelineScreen> createState() => _TimelineScreenState();
}

class _TimelineScreenState extends State<TimelineScreen> {
  double _hoursBack = 0; // 0 = now, can go back 48h

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<EventsProvider>();
    final cutoff = DateTime.now().toUtc().subtract(
          Duration(hours: _hoursBack.toInt()),
        );

    // Filter events visible at the selected time
    final visible = provider.events.where((e) {
      if (e.effective != null && e.effective!.isAfter(cutoff)) return false;
      if (e.expires != null && e.expires!.isBefore(cutoff)) return false;
      return true;
    }).toList();

    return Scaffold(
      backgroundColor: ESPAlertTheme.background,
      appBar: AppBar(
        title: const Text('📅 Timeline'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => provider.loadEvents(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Time slider
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: ESPAlertTheme.surface,
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _hoursBack == 0
                          ? 'Ahora'
                          : 'Hace ${_hoursBack.toInt()}h',
                      style: const TextStyle(
                        color: ESPAlertTheme.primary,
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      '${visible.length} eventos',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.6),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
                Slider(
                  value: _hoursBack,
                  min: 0,
                  max: 48,
                  divisions: 48,
                  activeColor: ESPAlertTheme.primary,
                  inactiveColor: ESPAlertTheme.surfaceVariant,
                  label: _hoursBack == 0
                      ? 'Ahora'
                      : '${_hoursBack.toInt()}h atrás',
                  onChanged: (v) => setState(() => _hoursBack = v),
                ),
              ],
            ),
          ),

          // Events list
          Expanded(
            child: visible.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text('🎉', style: TextStyle(fontSize: 48)),
                        const SizedBox(height: 12),
                        Text(
                          'Sin alertas en este momento',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: visible.length,
                    itemBuilder: (ctx, i) {
                      return GestureDetector(
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                EventDetailScreen(event: visible[i]),
                          ),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: EventCard(event: visible[i]),
                        ).animate().fadeIn(delay: (50 * i).ms),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
