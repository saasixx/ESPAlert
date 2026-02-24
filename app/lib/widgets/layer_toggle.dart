import 'package:flutter/material.dart';
import '../config/theme.dart';

/// Vertical panel of toggleable map layers.
class LayerTogglePanel extends StatelessWidget {
  final Set<String> activeLayers;
  final Function(String) onToggle;

  const LayerTogglePanel({
    super.key,
    required this.activeLayers,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
      decoration: BoxDecoration(
        color: ESPAlertTheme.surface.withOpacity(0.92),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 12,
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _layerChip('meteo', '🌦️', 'Meteo', ESPAlertTheme.meteoColor),
          _layerChip('seismic', '📳', 'Sismos', ESPAlertTheme.seismicColor),
          _layerChip('traffic', '🚗', 'Tráfico', ESPAlertTheme.trafficColor),
          _layerChip('maritime', '🌊', 'Mar', ESPAlertTheme.maritimeColor),
        ],
      ),
    );
  }

  Widget _layerChip(String key, String emoji, String label, Color color) {
    final active = activeLayers.contains(key);

    return GestureDetector(
      onTap: () => onToggle(key),
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 3, horizontal: 4),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: active ? color.withOpacity(0.2) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          border: active
              ? Border.all(color: color.withOpacity(0.5))
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(emoji, style: const TextStyle(fontSize: 16)),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: active ? FontWeight.w700 : FontWeight.w400,
                color: active ? color : Colors.white54,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
