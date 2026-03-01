import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/settings_provider.dart';

/// Settings screen — zone management, notification preferences.
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsProvider>();

    return Scaffold(
      backgroundColor: ESPAlertTheme.background,
      appBar: AppBar(title: const Text('⚙️ Ajustes')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Notification Preferences ────────────────────
          _sectionTitle('Notificaciones'),

          _card([
            SwitchListTile(
              title: const Text('Alertas predictivas'),
              subtitle: const Text(
                'Te avisamos si mañana puede haber avisos en tu zona',
              ),
              value: settings.predictiveAlerts,
              onChanged: settings.setPredictiveAlerts,
              activeColor: ESPAlertTheme.primary,
            ),
          ]),

          const SizedBox(height: 12),

          // ── Minimum Severity ────────────────────────────
          _sectionTitle('Severidad mínima para notificar'),

          _card([
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: ['green', 'yellow', 'orange', 'red'].map((s) {
                  final isSelected = settings.minSeverity == s;
                  final color = ESPAlertTheme.severityColor(s);
                  return GestureDetector(
                    onTap: () => settings.setMinSeverity(s),
                    child: Column(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: isSelected ? color : color.withOpacity(0.2),
                            shape: BoxShape.circle,
                            border: isSelected
                                ? Border.all(color: Colors.white, width: 2)
                                : null,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          _severityName(s),
                          style: TextStyle(
                            fontSize: 11,
                            color: isSelected ? Colors.white : Colors.white54,
                            fontWeight:
                                isSelected ? FontWeight.w700 : FontWeight.w400,
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
          ]),

          const SizedBox(height: 12),

          // ── Quiet Hours ─────────────────────────────────
          _sectionTitle('Horario de silencio'),

          _card([
            ListTile(
              leading: const Icon(Icons.bedtime, color: ESPAlertTheme.primary),
              title: const Text('Inicio'),
              trailing: Text(
                settings.quietStart != null
                    ? '${settings.quietStart!.hour.toString().padLeft(2, '0')}:${settings.quietStart!.minute.toString().padLeft(2, '0')}'
                    : 'No configurado',
                style: const TextStyle(color: ESPAlertTheme.primary),
              ),
              onTap: () => _pickTime(context, settings, isStart: true),
            ),
            const Divider(height: 1, color: Colors.white12),
            ListTile(
              leading:
                  const Icon(Icons.wb_sunny, color: ESPAlertTheme.primary),
              title: const Text('Fin'),
              trailing: Text(
                settings.quietEnd != null
                    ? '${settings.quietEnd!.hour.toString().padLeft(2, '0')}:${settings.quietEnd!.minute.toString().padLeft(2, '0')}'
                    : 'No configurado',
                style: const TextStyle(color: ESPAlertTheme.primary),
              ),
              onTap: () => _pickTime(context, settings, isStart: false),
            ),
            if (settings.quietStart != null || settings.quietEnd != null)
              ListTile(
                leading: const Icon(Icons.clear, color: Colors.white54),
                title: const Text('Quitar horario de silencio'),
                onTap: () => settings.setQuietHours(null, null),
              ),
          ]),

          const SizedBox(height: 12),

          // ── About ───────────────────────────────────────
          _sectionTitle('Información'),

          _card([
            const ListTile(
              leading: Icon(Icons.info_outline, color: ESPAlertTheme.primary),
              title: Text('ESPAlert v1.0.0'),
              subtitle: Text(
                'Sistema multi-riesgo para España\n'
                'Datos: AEMET, IGN, DGT, MeteoAlarm',
              ),
            ),
            const Divider(height: 1, color: Colors.white12),
            const ListTile(
              leading: Icon(Icons.phone, color: ESPAlertTheme.accent),
              title: Text('Emergencias: 112'),
              subtitle: Text('Teléfono único europeo de emergencias'),
            ),
          ]),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _sectionTitle(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, left: 4),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w700,
          color: ESPAlertTheme.primary,
          letterSpacing: 1,
        ),
      ),
    );
  }

  Widget _card(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: ESPAlertTheme.surfaceVariant,
        borderRadius: BorderRadius.circular(16),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(children: children),
    );
  }

  String _severityName(String s) {
    switch (s) {
      case 'green':
        return 'Todos';
      case 'yellow':
        return 'Amarillo+';
      case 'orange':
        return 'Naranja+';
      case 'red':
        return 'Solo rojo';
      default:
        return s;
    }
  }

  void _pickTime(BuildContext context, SettingsProvider settings,
      {required bool isStart}) async {
    final initial = isStart
        ? (settings.quietStart ?? const TimeOfDay(hour: 23, minute: 0))
        : (settings.quietEnd ?? const TimeOfDay(hour: 7, minute: 0));

    final picked = await showTimePicker(
      context: context,
      initialTime: initial,
    );
    if (picked != null) {
      if (isStart) {
        settings.setQuietHours(picked, settings.quietEnd);
      } else {
        settings.setQuietHours(settings.quietStart, picked);
      }
    }
  }
}
