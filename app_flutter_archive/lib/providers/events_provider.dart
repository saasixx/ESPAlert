import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../config/env.dart';
import '../models/event.dart';
import '../services/api_service.dart';

/// Provider for alert events — loads from API + real-time WebSocket.
class EventsProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  WebSocketChannel? _wsChannel;

  List<AlertEvent> _events = [];
  bool _loading = false;
  String? _error;
  int _wsReconnectAttempts = 0;

  // Active layer filters
  Set<String> _activeLayers = {'meteo', 'seismic', 'traffic', 'maritime'};

  List<AlertEvent> get events => _events;
  bool get loading => _loading;
  String? get error => _error;
  Set<String> get activeLayers => _activeLayers;

  /// Filtered events based on active layers
  List<AlertEvent> get filteredEvents {
    return _events.where((e) {
      if (e.isMeteo && _activeLayers.contains('meteo')) return true;
      if (e.isSeismic && _activeLayers.contains('seismic')) return true;
      if (e.isTraffic && _activeLayers.contains('traffic')) return true;
      if (e.isMaritime && _activeLayers.contains('maritime')) return true;
      return false;
    }).toList();
  }

  List<AlertEvent> get activeEvents =>
      filteredEvents.where((e) => e.isActive).toList();

  /// Events grouped by severity (for summary cards)
  Map<String, List<AlertEvent>> get eventsBySeverity {
    final map = <String, List<AlertEvent>>{};
    for (final e in activeEvents) {
      map.putIfAbsent(e.severity, () => []).add(e);
    }
    return map;
  }

  void toggleLayer(String layer) {
    if (_activeLayers.contains(layer)) {
      _activeLayers.remove(layer);
    } else {
      _activeLayers.add(layer);
    }
    notifyListeners();
  }

  /// Load events from REST API
  Future<void> loadEvents({
    double? lat,
    double? lon,
    double radiusKm = 200,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _events = await _api.getEvents(
        activeOnly: false, // Show all recent for timeline
        lat: lat,
        lon: lon,
        radiusKm: radiusKm,
        limit: 200,
      );
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Connect to WebSocket for real-time updates
  void connectWebSocket() {
    _wsReconnectAttempts = 0;
    _connectWS();
  }

  void _connectWS() {
    try {
      _wsChannel = WebSocketChannel.connect(
        Uri.parse(Env.wsEventsUrl),
      );

      _wsChannel!.stream.listen(
        (message) {
          _wsReconnectAttempts = 0; // Reset on successful message
          try {
            final data = jsonDecode(message);
            final newEvent = AlertEvent.fromJson(data);

            // Add to the top of the list if not a duplicate
            if (!_events.any((e) => e.id == newEvent.id)) {
              _events.insert(0, newEvent);
              notifyListeners();
            }
          } catch (e) {
            debugPrint('WebSocket parse error: $e');
          }
        },
        onError: (error) {
          debugPrint('WebSocket error: $error');
          _scheduleReconnect();
        },
        onDone: () {
          debugPrint('WebSocket closed, reconnecting...');
          _scheduleReconnect();
        },
      );
    } catch (e) {
      debugPrint('WebSocket connection failed: $e');
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    _wsReconnectAttempts++;
    // Exponential backoff: 2s, 4s, 8s, 16s, 32s, max 60s
    final delayMs = min(
      Env.wsReconnectInitial.inMilliseconds * pow(2, _wsReconnectAttempts - 1),
      Env.wsReconnectMax.inMilliseconds,
    ).toInt();
    debugPrint('WebSocket reconnecting in ${delayMs}ms (attempt $_wsReconnectAttempts)');
    Future.delayed(Duration(milliseconds: delayMs), _connectWS);
  }

  @override
  void dispose() {
    _wsChannel?.sink.close();
    super.dispose();
  }
}
