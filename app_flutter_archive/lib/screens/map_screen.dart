import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../config/theme.dart';
import '../models/event.dart';
import '../providers/events_provider.dart';
import '../widgets/event_card.dart';
import '../widgets/layer_toggle.dart';
import '../widgets/severity_badge.dart';
import 'event_detail.dart';

/// Live map screen — the main view of ESPAlert.
class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final MapController _mapController = MapController();
  AlertEvent? _selectedEvent;

  // Spain center coordinates
  static const _spainCenter = LatLng(40.0, -3.7);

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<EventsProvider>();

    return Scaffold(
      body: Stack(
        children: [
          // ── Map ─────────────────────────────────────────
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _spainCenter,
              initialZoom: 6.0,
              minZoom: 4.0,
              maxZoom: 18.0,
              onTap: (_, __) => setState(() => _selectedEvent = null),
            ),
            children: [
              // Base tile layer (dark style)
              TileLayer(
                urlTemplate:
                    'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
                subdomains: const ['a', 'b', 'c', 'd'],
                userAgentPackageName: 'com.espalert.app',
              ),

              // Polygon layer for weather warning areas
              PolygonLayer(
                polygons: _buildWarningPolygons(provider.filteredEvents),
              ),

              // Circle markers for earthquakes
              CircleLayer(
                circles: _buildEarthquakeCircles(provider.filteredEvents),
              ),

              // Point markers for traffic incidents
              MarkerLayer(
                markers: _buildTrafficMarkers(provider.filteredEvents),
              ),
            ],
          ),

          // ── Top bar: app title + summary ────────────────
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: EdgeInsets.only(
                top: MediaQuery.of(context).padding.top + 8,
                left: 16,
                right: 16,
                bottom: 12,
              ),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    ESPAlertTheme.background.withOpacity(0.95),
                    ESPAlertTheme.background.withOpacity(0.0),
                  ],
                ),
              ),
              child: Row(
                children: [
                  const Text(
                    '🛡️ ESPAlert',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                  const Spacer(),
                  // Active alerts count badges
                  ..._buildSeverityCountBadges(provider),
                ],
              ),
            ),
          ).animate().fadeIn(duration: 500.ms),

          // ── Layer toggles ───────────────────────────────
          Positioned(
            top: MediaQuery.of(context).padding.top + 56,
            left: 12,
            child: LayerTogglePanel(
              activeLayers: provider.activeLayers,
              onToggle: provider.toggleLayer,
            ),
          ).animate().slideX(begin: -1, duration: 400.ms, curve: Curves.easeOut),

          // ── Zoom controls ───────────────────────────────
          Positioned(
            right: 12,
            bottom: 200,
            child: Column(
              children: [
                _mapButton(Icons.my_location, () => _centerOnSpain()),
                const SizedBox(height: 8),
                _mapButton(Icons.add, () => _zoom(1)),
                const SizedBox(height: 8),
                _mapButton(Icons.remove, () => _zoom(-1)),
              ],
            ),
          ),

          // ── Selected event card ─────────────────────────
          if (_selectedEvent != null)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: GestureDetector(
                onTap: () => _openDetail(_selectedEvent!),
                child: EventCard(
                  event: _selectedEvent!,
                  compact: false,
                ),
              ).animate().slideY(begin: 1, duration: 300.ms, curve: Curves.easeOut),
            ),

          // ── Loading indicator ───────────────────────────
          if (provider.loading)
            const Positioned(
              bottom: 120,
              left: 0,
              right: 0,
              child: Center(
                child: CircularProgressIndicator(
                  color: ESPAlertTheme.primary,
                ),
              ),
            ),
        ],
      ),
    );
  }

  List<Widget> _buildSeverityCountBadges(EventsProvider provider) {
    final counts = <String, int>{};
    for (final e in provider.activeEvents) {
      counts[e.severity] = (counts[e.severity] ?? 0) + 1;
    }

    return ['red', 'orange', 'yellow'].where((s) => counts.containsKey(s)).map((s) {
      return Padding(
        padding: const EdgeInsets.only(left: 6),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: ESPAlertTheme.severityColor(s).withOpacity(0.25),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: ESPAlertTheme.severityColor(s).withOpacity(0.6),
            ),
          ),
          child: Text(
            '${counts[s]}',
            style: TextStyle(
              color: ESPAlertTheme.severityColor(s),
              fontWeight: FontWeight.w700,
              fontSize: 14,
            ),
          ),
        ),
      );
    }).toList();
  }

  List<Polygon> _buildWarningPolygons(List<AlertEvent> events) {
    final polygons = <Polygon>[];
    for (final event in events) {
      if (event.areaGeojson == null) continue;
      if (event.isSeismic || event.isTraffic) continue;

      try {
        final coords = _extractPolygonCoords(event.areaGeojson!);
        if (coords != null && coords.length >= 3) {
          final color = ESPAlertTheme.severityColor(event.severity);
          polygons.add(Polygon(
            points: coords,
            color: color.withOpacity(0.15),
            borderColor: color.withOpacity(0.7),
            borderStrokeWidth: 2,
            isFilled: true,
          ));
        }
      } catch (_) {}
    }
    return polygons;
  }

  List<CircleMarker> _buildEarthquakeCircles(List<AlertEvent> events) {
    return events
        .where((e) => e.isSeismic && e.areaGeojson != null)
        .map((e) {
      final coords = _extractPointCoords(e.areaGeojson!);
      if (coords == null) return null;

      final mag = double.tryParse(e.magnitude ?? '0') ?? 0;
      final color = ESPAlertTheme.severityColor(e.severity);

      return CircleMarker(
        point: coords,
        radius: 6 + (mag * 3),
        color: color.withOpacity(0.4),
        borderColor: color,
        borderStrokeWidth: 2,
      );
    }).whereType<CircleMarker>().toList();
  }

  List<Marker> _buildTrafficMarkers(List<AlertEvent> events) {
    return events
        .where((e) => e.isTraffic && e.areaGeojson != null)
        .map((e) {
      final coords = _extractPointCoords(e.areaGeojson!);
      if (coords == null) return null;

      return Marker(
        point: coords,
        width: 36,
        height: 36,
        child: GestureDetector(
          onTap: () => setState(() => _selectedEvent = e),
          child: Container(
            decoration: BoxDecoration(
              color: ESPAlertTheme.trafficColor.withOpacity(0.9),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: ESPAlertTheme.trafficColor.withOpacity(0.4),
                  blurRadius: 8,
                ),
              ],
            ),
            child: Center(
              child: Text(
                ESPAlertTheme.eventTypeEmoji(e.eventType),
                style: const TextStyle(fontSize: 16),
              ),
            ),
          ),
        ),
      );
    }).whereType<Marker>().toList();
  }

  LatLng? _extractPointCoords(Map<String, dynamic> geojson) {
    try {
      final type = geojson['type'];
      if (type == 'Point') {
        final c = geojson['coordinates'] as List;
        return LatLng(c[1].toDouble(), c[0].toDouble());
      }
    } catch (_) {}
    return null;
  }

  List<LatLng>? _extractPolygonCoords(Map<String, dynamic> geojson) {
    try {
      final type = geojson['type'];
      List coords;
      if (type == 'Polygon') {
        coords = geojson['coordinates'][0];
      } else if (type == 'MultiPolygon') {
        coords = geojson['coordinates'][0][0];
      } else {
        return null;
      }
      return coords.map((c) => LatLng(c[1].toDouble(), c[0].toDouble())).toList();
    } catch (_) {}
    return null;
  }

  Widget _mapButton(IconData icon, VoidCallback onPressed) {
    return Container(
      decoration: BoxDecoration(
        color: ESPAlertTheme.surface.withOpacity(0.9),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 8,
          ),
        ],
      ),
      child: IconButton(
        icon: Icon(icon, color: Colors.white, size: 20),
        onPressed: onPressed,
      ),
    );
  }

  void _centerOnSpain() {
    _mapController.move(_spainCenter, 6.0);
  }

  void _zoom(double delta) {
    final currentZoom = _mapController.camera.zoom;
    _mapController.move(_mapController.camera.center, currentZoom + delta);
  }

  void _openDetail(AlertEvent event) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => EventDetailScreen(event: event),
      ),
    );
  }
}
