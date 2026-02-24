/// Unified event model — mirrors the backend Event schema.
class AlertEvent {
  final String id;
  final String source;
  final String sourceId;
  final String eventType;
  final String severity;
  final String title;
  final String? description;
  final String? instructions;
  final String? areaName;
  final Map<String, dynamic>? areaGeojson;
  final DateTime? effective;
  final DateTime? expires;
  final String? sourceUrl;
  final String? magnitude;
  final String? depthKm;
  final DateTime createdAt;

  AlertEvent({
    required this.id,
    required this.source,
    required this.sourceId,
    required this.eventType,
    required this.severity,
    required this.title,
    this.description,
    this.instructions,
    this.areaName,
    this.areaGeojson,
    this.effective,
    this.expires,
    this.sourceUrl,
    this.magnitude,
    this.depthKm,
    required this.createdAt,
  });

  factory AlertEvent.fromJson(Map<String, dynamic> json) {
    return AlertEvent(
      id: json['id'] ?? '',
      source: json['source'] ?? '',
      sourceId: json['source_id'] ?? '',
      eventType: json['event_type'] ?? 'other',
      severity: json['severity'] ?? 'green',
      title: json['title'] ?? '',
      description: json['description'],
      instructions: json['instructions'],
      areaName: json['area_name'],
      areaGeojson: json['area_geojson'],
      effective: json['effective'] != null
          ? DateTime.tryParse(json['effective'])
          : null,
      expires: json['expires'] != null
          ? DateTime.tryParse(json['expires'])
          : null,
      sourceUrl: json['source_url'],
      magnitude: json['magnitude'],
      depthKm: json['depth_km'],
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }

  bool get isActive {
    final now = DateTime.now().toUtc();
    if (effective != null && effective!.isAfter(now)) return false;
    if (expires != null && expires!.isBefore(now)) return false;
    return true;
  }

  /// Minutes until this event starts (null if already active)
  int? get minutesUntilStart {
    if (effective == null) return null;
    final delta = effective!.difference(DateTime.now().toUtc());
    if (delta.isNegative) return null;
    return delta.inMinutes;
  }

  bool get isMeteo => [
        'wind', 'rain', 'storm', 'snow', 'ice', 'fog',
        'heat', 'cold', 'uv', 'fire_risk'
      ].contains(eventType);

  bool get isMaritime => ['coastal', 'wave', 'tide'].contains(eventType);

  bool get isSeismic => ['earthquake', 'tsunami'].contains(eventType);

  bool get isTraffic => eventType.startsWith('traffic');
}
