import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/env.dart';
import '../models/event.dart';

/// REST API client for the ESPAlert backend.
class ApiService {
  static String baseUrl = Env.apiBaseUrl;

  String? _token;

  void setToken(String token) => _token = token;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  // ── Events ────────────────────────────────────────────

  Future<List<AlertEvent>> getEvents({
    String? eventType,
    String? severity,
    String? source,
    bool activeOnly = true,
    double? lat,
    double? lon,
    double radiusKm = 50,
    int limit = 50,
  }) async {
    final params = <String, String>{
      'active_only': activeOnly.toString(),
      'limit': limit.toString(),
      'radius_km': radiusKm.toString(),
    };
    if (eventType != null) params['event_type'] = eventType;
    if (severity != null) params['severity'] = severity;
    if (source != null) params['source'] = source;
    if (lat != null) params['lat'] = lat.toString();
    if (lon != null) params['lon'] = lon.toString();

    final uri = Uri.parse('$baseUrl/events/').replace(queryParameters: params);
    final resp = await http.get(uri, headers: _headers)
        .timeout(Env.httpTimeout);

    if (resp.statusCode == 200) {
      final list = jsonDecode(resp.body) as List;
      return list.map((j) => AlertEvent.fromJson(j)).toList();
    }
    throw Exception('Failed to load events: ${resp.statusCode}');
  }

  Future<AlertEvent> getEvent(String id) async {
    final resp = await http.get(
      Uri.parse('$baseUrl/events/$id'),
      headers: _headers,
    );
    if (resp.statusCode == 200) {
      return AlertEvent.fromJson(jsonDecode(resp.body));
    }
    throw Exception('Event not found');
  }

  Future<Map<String, dynamic>> getActiveSummary() async {
    final resp = await http.get(
      Uri.parse('$baseUrl/events/active/summary'),
      headers: _headers,
    );
    if (resp.statusCode == 200) {
      return jsonDecode(resp.body);
    }
    throw Exception('Failed to load summary');
  }

  // ── Auth ──────────────────────────────────────────────

  Future<String> register(String email, String password, {String? name}) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: _headers,
      body: jsonEncode({
        'email': email,
        'password': password,
        if (name != null) 'display_name': name,
      }),
    );
    if (resp.statusCode == 201) {
      final data = jsonDecode(resp.body);
      _token = data['access_token'];
      return _token!;
    }
    throw Exception('Registration failed: ${resp.body}');
  }

  Future<String> login(String email, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: _headers,
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      _token = data['access_token'];
      return _token!;
    }
    throw Exception('Login failed');
  }

  // ── Zones ─────────────────────────────────────────────

  Future<List<dynamic>> getZones() async {
    final resp = await http.get(
      Uri.parse('$baseUrl/subscriptions/zones'),
      headers: _headers,
    );
    if (resp.statusCode == 200) return jsonDecode(resp.body);
    throw Exception('Failed to load zones');
  }

  Future<void> createZone(String label, Map<String, dynamic> geojson) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/subscriptions/zones'),
      headers: _headers,
      body: jsonEncode({'label': label, 'geojson': geojson}),
    );
    if (resp.statusCode != 201) throw Exception('Failed to create zone');
  }

  Future<void> deleteZone(String id) async {
    final resp = await http.delete(
      Uri.parse('$baseUrl/subscriptions/zones/$id'),
      headers: _headers,
    );
    if (resp.statusCode != 204) throw Exception('Failed to delete zone');
  }

  // ── Settings ──────────────────────────────────────────

  Future<void> updateSettings({
    String? fcmToken,
    String? quietStart,
    String? quietEnd,
    bool? predictiveAlerts,
  }) async {
    final body = <String, dynamic>{};
    if (fcmToken != null) body['fcm_token'] = fcmToken;
    if (quietStart != null) body['quiet_start'] = quietStart;
    if (quietEnd != null) body['quiet_end'] = quietEnd;
    if (predictiveAlerts != null) body['predictive_alerts'] = predictiveAlerts;

    final resp = await http.patch(
      Uri.parse('$baseUrl/subscriptions/settings'),
      headers: _headers,
      body: jsonEncode(body),
    );
    if (resp.statusCode != 200) throw Exception('Failed to update settings');
  }
}
