/// Environment configuration for ESPAlert app.
///
/// Change these values to match your deployment:
/// - Development: use Android emulator addresses (10.0.2.2)
/// - Production: use your actual backend domain
class Env {
  // Prevent instantiation
  Env._();

  /// Base URL for the REST API
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  /// WebSocket URL for real-time event stream
  static const String wsEventsUrl = String.fromEnvironment(
    'WS_EVENTS_URL',
    defaultValue: 'ws://10.0.2.2:8000/api/v1/ws/events',
  );

  /// Base URL for mesh network API
  static const String meshBaseUrl = String.fromEnvironment(
    'MESH_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1/mesh',
  );

  /// HTTP request timeout
  static const Duration httpTimeout = Duration(seconds: 15);

  /// WebSocket reconnect initial delay
  static const Duration wsReconnectInitial = Duration(seconds: 2);

  /// WebSocket reconnect max delay
  static const Duration wsReconnectMax = Duration(seconds: 60);
}
