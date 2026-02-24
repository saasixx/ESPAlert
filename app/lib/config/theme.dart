import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// ESPAlert design system — dark, premium, emergency-focused.
class ESPAlertTheme {
  // ── Brand Colors ──────────────────────────────────────
  static const Color background = Color(0xFF0A0E21);
  static const Color surface = Color(0xFF1A1A2E);
  static const Color surfaceVariant = Color(0xFF16213E);
  static const Color primary = Color(0xFF4ECDC4);
  static const Color secondary = Color(0xFF0F3460);
  static const Color accent = Color(0xFFE94560);

  // ── Severity Colors ───────────────────────────────────
  static const Color severityGreen = Color(0xFF4CAF50);
  static const Color severityYellow = Color(0xFFFFC107);
  static const Color severityOrange = Color(0xFFFF9800);
  static const Color severityRed = Color(0xFFF44336);

  // ── Event Type Colors ─────────────────────────────────
  static const Color meteoColor = Color(0xFF42A5F5);
  static const Color seismicColor = Color(0xFFAB47BC);
  static const Color trafficColor = Color(0xFFFF7043);
  static const Color maritimeColor = Color(0xFF26C6DA);

  static Color severityColor(String severity) {
    switch (severity) {
      case 'red':
        return severityRed;
      case 'orange':
        return severityOrange;
      case 'yellow':
        return severityYellow;
      default:
        return severityGreen;
    }
  }

  static Color eventTypeColor(String type) {
    if (type.startsWith('traffic')) return trafficColor;
    if (type == 'earthquake' || type == 'tsunami') return seismicColor;
    if (type == 'coastal' || type == 'wave' || type == 'tide') return maritimeColor;
    return meteoColor;
  }

  static String severityLabel(String severity) {
    switch (severity) {
      case 'red':
        return 'RIESGO EXTREMO';
      case 'orange':
        return 'RIESGO IMPORTANTE';
      case 'yellow':
        return 'RIESGO';
      default:
        return 'SIN RIESGO';
    }
  }

  static String eventTypeEmoji(String type) {
    const map = {
      'wind': '💨',
      'rain': '🌧️',
      'storm': '⛈️',
      'snow': '❄️',
      'ice': '🧊',
      'fog': '🌫️',
      'heat': '🌡️',
      'cold': '🥶',
      'uv': '☀️',
      'fire_risk': '🔥',
      'coastal': '🌊',
      'wave': '🌊',
      'tide': '🌊',
      'earthquake': '📳',
      'tsunami': '🌊',
      'traffic_accident': '🚗',
      'traffic_closure': '🚧',
      'traffic_works': '🔧',
      'traffic_jam': '🐌',
      'civil_protection': '🚨',
    };
    return map[type] ?? '⚠️';
  }

  // ── Dark Theme ────────────────────────────────────────
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: surface,
        error: accent,
      ),
      textTheme: GoogleFonts.interTextTheme(
        ThemeData.dark().textTheme,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: surface,
        foregroundColor: Colors.white,
        elevation: 0,
        titleTextStyle: GoogleFonts.inter(
          fontSize: 20,
          fontWeight: FontWeight.w700,
          color: Colors.white,
        ),
      ),
      cardTheme: CardTheme(
        color: surfaceVariant,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: surface,
        indicatorColor: secondary.withOpacity(0.8),
        labelTextStyle: WidgetStatePropertyAll(
          GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w500),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: surfaceVariant,
        selectedColor: primary.withOpacity(0.3),
        labelStyle: GoogleFonts.inter(fontSize: 13),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: primary,
        foregroundColor: background,
      ),
    );
  }
}
