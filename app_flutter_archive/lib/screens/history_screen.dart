import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/events_provider.dart';
import '../widgets/event_card.dart';
import 'event_detail.dart';

/// Personal history — past alerts that affected the user's zones.
class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final events = context.watch<EventsProvider>().events;

    // Show all events sorted by date (most recent first)
    final past = events.where((e) => !e.isActive).toList()
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));

    return Scaffold(
      backgroundColor: ESPAlertTheme.background,
      appBar: AppBar(
        title: const Text('📋 Historial'),
      ),
      body: past.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('📭', style: TextStyle(fontSize: 48)),
                  const SizedBox(height: 12),
                  Text(
                    'No hay alertas pasadas',
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
              itemCount: past.length,
              itemBuilder: (ctx, i) {
                return GestureDetector(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => EventDetailScreen(event: past[i]),
                    ),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: EventCard(event: past[i]),
                  ),
                );
              },
            ),
    );
  }
}
