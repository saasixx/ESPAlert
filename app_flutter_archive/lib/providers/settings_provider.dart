import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Provider for user settings — zones, filters, quiet hours.
class SettingsProvider extends ChangeNotifier {
  bool _predictiveAlerts = true;
  TimeOfDay? _quietStart;
  TimeOfDay? _quietEnd;
  String _minSeverity = 'yellow';
  Set<String> _enabledTypes = {};

  bool get predictiveAlerts => _predictiveAlerts;
  TimeOfDay? get quietStart => _quietStart;
  TimeOfDay? get quietEnd => _quietEnd;
  String get minSeverity => _minSeverity;
  Set<String> get enabledTypes => _enabledTypes;

  SettingsProvider() {
    _loadFromPrefs();
  }

  Future<void> _loadFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    _predictiveAlerts = prefs.getBool('predictive_alerts') ?? true;
    _minSeverity = prefs.getString('min_severity') ?? 'yellow';

    final types = prefs.getStringList('enabled_types');
    if (types != null && types.isNotEmpty) {
      _enabledTypes = types.toSet();
    }

    final qs = prefs.getString('quiet_start');
    if (qs != null) {
      final parts = qs.split(':');
      _quietStart = TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
    }
    final qe = prefs.getString('quiet_end');
    if (qe != null) {
      final parts = qe.split(':');
      _quietEnd = TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
    }

    notifyListeners();
  }

  Future<void> setPredictiveAlerts(bool value) async {
    _predictiveAlerts = value;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('predictive_alerts', value);
  }

  Future<void> setMinSeverity(String value) async {
    _minSeverity = value;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('min_severity', value);
  }

  Future<void> setQuietHours(TimeOfDay? start, TimeOfDay? end) async {
    _quietStart = start;
    _quietEnd = end;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    if (start != null) {
      await prefs.setString('quiet_start', '${start.hour}:${start.minute}');
    } else {
      await prefs.remove('quiet_start');
    }
    if (end != null) {
      await prefs.setString('quiet_end', '${end.hour}:${end.minute}');
    } else {
      await prefs.remove('quiet_end');
    }
  }

  Future<void> toggleType(String type) async {
    if (_enabledTypes.contains(type)) {
      _enabledTypes.remove(type);
    } else {
      _enabledTypes.add(type);
    }
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('enabled_types', _enabledTypes.toList());
  }
}
