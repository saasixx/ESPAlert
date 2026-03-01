import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:permission_handler/permission_handler.dart';
import '../config/env.dart';

/// Meshtastic BLE service UUIDs
class MeshtasticBLE {
  static const serviceUuid = '6ba1b218-15a8-461f-9fa8-5dcae273eafd';
  static const toRadioUuid = 'f75c76d2-129e-4dad-a1dd-7866124401e7';
  static const fromRadioUuid = '2c55e69e-4993-11ed-b878-0242ac120002';
  static const fromNumUuid = 'ed9da18c-a800-4f66-a670-aa7547e34453';
}

/// Connection mode for mesh communication.
enum MeshConnectionMode {
  disconnected,
  bleScanning,
  bleConnected,
  httpGateway,
}

/// A Meshtastic device found during BLE scan.
class MeshtasticDevice {
  final String id;
  final String name;
  final int rssi;

  MeshtasticDevice({required this.id, required this.name, required this.rssi});
}

/// A message in the mesh chat.
class MeshChatMessage {
  final String senderId;
  final String senderName;
  final String text;
  final int channel;
  final DateTime timestamp;
  final double? lat;
  final double? lon;
  final double? snr;
  final int? rssi;
  final int? hopCount;
  final bool isMine;

  MeshChatMessage({
    required this.senderId,
    required this.senderName,
    required this.text,
    this.channel = 0,
    required this.timestamp,
    this.lat,
    this.lon,
    this.snr,
    this.rssi,
    this.hopCount,
    this.isMine = false,
  });

  factory MeshChatMessage.fromJson(Map<String, dynamic> json) {
    return MeshChatMessage(
      senderId: json['sender_id'] ?? '',
      senderName: json['sender_name'] ?? 'Desconocido',
      text: json['text'] ?? '',
      channel: json['channel'] ?? 0,
      timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
      lat: json['lat']?.toDouble(),
      lon: json['lon']?.toDouble(),
      snr: json['snr']?.toDouble(),
      rssi: json['rssi'],
      hopCount: json['hop_count'],
    );
  }
}

/// A Meshtastic node on the mesh network.
class MeshNodeInfo {
  final String nodeId;
  final String longName;
  final String shortName;
  final double? lat;
  final double? lon;
  final int? altitude;
  final int? batteryLevel;
  final double? snr;
  final DateTime? lastHeard;

  MeshNodeInfo({
    required this.nodeId,
    required this.longName,
    required this.shortName,
    this.lat,
    this.lon,
    this.altitude,
    this.batteryLevel,
    this.snr,
    this.lastHeard,
  });

  factory MeshNodeInfo.fromJson(Map<String, dynamic> json) {
    return MeshNodeInfo(
      nodeId: json['node_id'] ?? '',
      longName: json['long_name'] ?? '',
      shortName: json['short_name'] ?? '??',
      lat: json['lat']?.toDouble(),
      lon: json['lon']?.toDouble(),
      altitude: json['altitude'],
      batteryLevel: json['battery_level'],
      snr: json['snr']?.toDouble(),
      lastHeard: json['last_heard'] != null
          ? DateTime.tryParse(json['last_heard'])
          : null,
    );
  }
}

/// Service for Meshtastic mesh network communication.
///
/// Dual-mode:
/// - **BLE Direct**: connects directly to a Meshtastic device via Bluetooth
///   (works offline, no internet required — emergency mode)
/// - **HTTP Gateway**: relay messages through the backend when internet is available
class MeshService extends ChangeNotifier {
  static String baseUrl = Env.meshBaseUrl;

  // BLE
  final FlutterReactiveBle _ble = FlutterReactiveBle();
  StreamSubscription<DiscoveredDevice>? _scanSubscription;
  StreamSubscription<ConnectionStateUpdate>? _connectionSubscription;
  StreamSubscription<List<int>>? _fromRadioSubscription;
  StreamSubscription<List<int>>? _notifySubscription;
  String? _connectedDeviceId;

  // HTTP fallback
  WebSocketChannel? _wsChannel;

  // State
  MeshConnectionMode _mode = MeshConnectionMode.disconnected;
  final List<MeshtasticDevice> _scannedDevices = [];
  final List<MeshChatMessage> _messages = [];
  final List<MeshNodeInfo> _nodes = [];
  bool _scanning = false;
  String? _error;

  // Getters
  MeshConnectionMode get mode => _mode;
  bool get connected => _mode == MeshConnectionMode.bleConnected ||
      _mode == MeshConnectionMode.httpGateway;
  bool get isBLE => _mode == MeshConnectionMode.bleConnected;
  bool get isHTTP => _mode == MeshConnectionMode.httpGateway;
  bool get scanning => _scanning;
  String? get error => _error;
  List<MeshtasticDevice> get scannedDevices => List.unmodifiable(_scannedDevices);
  List<MeshChatMessage> get messages => List.unmodifiable(_messages);
  List<MeshNodeInfo> get nodes => List.unmodifiable(_nodes);

  // ── BLE Permissions ───────────────────────────────────────────────────

  /// Request Bluetooth permissions (Android 12+ requires explicit)
  Future<bool> requestBLEPermissions() async {
    if (await Permission.bluetoothScan.isGranted &&
        await Permission.bluetoothConnect.isGranted &&
        await Permission.locationWhenInUse.isGranted) {
      return true;
    }

    final statuses = await [
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.locationWhenInUse,
    ].request();

    return statuses.values.every((s) => s.isGranted);
  }

  // ── BLE Scan ──────────────────────────────────────────────────────────

  /// Scan for Meshtastic devices via BLE.
  Future<void> startScan({Duration timeout = const Duration(seconds: 10)}) async {
    final hasPermission = await requestBLEPermissions();
    if (!hasPermission) {
      _error = 'Permisos Bluetooth denegados';
      notifyListeners();
      return;
    }

    _scanning = true;
    _scannedDevices.clear();
    _error = null;
    _mode = MeshConnectionMode.bleScanning;
    notifyListeners();

    _scanSubscription = _ble.scanForDevices(
      withServices: [Uuid.parse(MeshtasticBLE.serviceUuid)],
      scanMode: ScanMode.lowLatency,
    ).listen(
      (device) {
        // Deduplicate by ID
        if (!_scannedDevices.any((d) => d.id == device.id)) {
          _scannedDevices.add(MeshtasticDevice(
            id: device.id,
            name: device.name.isNotEmpty ? device.name : 'Meshtastic-${device.id.substring(device.id.length - 4)}',
            rssi: device.rssi,
          ));
          notifyListeners();
        }
      },
      onError: (e) {
        _error = 'Error de escaneo: $e';
        _scanning = false;
        notifyListeners();
      },
    );

    // Auto-stop after timeout
    Future.delayed(timeout, stopScan);
  }

  void stopScan() {
    _scanSubscription?.cancel();
    _scanSubscription = null;
    _scanning = false;
    if (_mode == MeshConnectionMode.bleScanning) {
      _mode = MeshConnectionMode.disconnected;
    }
    notifyListeners();
  }

  // ── BLE Connect ───────────────────────────────────────────────────────

  /// Connect to a specific Meshtastic device via BLE.
  Future<void> connectBLE(String deviceId) async {
    stopScan();
    _error = null;
    notifyListeners();

    _connectionSubscription = _ble.connectToDevice(
      id: deviceId,
      connectionTimeout: const Duration(seconds: 15),
    ).listen(
      (update) async {
        switch (update.connectionState) {
          case DeviceConnectionState.connected:
            _connectedDeviceId = deviceId;
            _mode = MeshConnectionMode.bleConnected;
            _error = null;
            notifyListeners();

            // Subscribe to incoming data
            await _subscribeToMeshDevice(deviceId);
            // Request initial config (node list)
            await _requestConfig(deviceId);
            break;

          case DeviceConnectionState.disconnected:
            _connectedDeviceId = null;
            _mode = MeshConnectionMode.disconnected;
            notifyListeners();
            break;

          case DeviceConnectionState.connecting:
            debugPrint('BLE: connecting to $deviceId...');
            break;

          case DeviceConnectionState.disconnecting:
            debugPrint('BLE: disconnecting from $deviceId...');
            break;
        }
      },
      onError: (e) {
        _error = 'Error de conexión BLE: $e';
        _mode = MeshConnectionMode.disconnected;
        notifyListeners();
      },
    );
  }

  /// Subscribe to the FromRadio characteristic for incoming data.
  Future<void> _subscribeToMeshDevice(String deviceId) async {
    final fromNumChar = QualifiedCharacteristic(
      serviceId: Uuid.parse(MeshtasticBLE.serviceUuid),
      characteristicId: Uuid.parse(MeshtasticBLE.fromNumUuid),
      deviceId: deviceId,
    );

    final fromRadioChar = QualifiedCharacteristic(
      serviceId: Uuid.parse(MeshtasticBLE.serviceUuid),
      characteristicId: Uuid.parse(MeshtasticBLE.fromRadioUuid),
      deviceId: deviceId,
    );

    // Subscribe to notifications on fromNum
    _notifySubscription = _ble.subscribeToCharacteristic(fromNumChar).listen(
      (_) async {
        // When notified, read all available data from fromRadio
        try {
          while (true) {
            final data = await _ble.readCharacteristic(fromRadioChar);
            if (data.isEmpty) break;
            _handleFromRadio(Uint8List.fromList(data));
          }
        } catch (_) {
          // No more data available
        }
      },
      onError: (e) => debugPrint('BLE notify error: $e'),
    );
  }

  /// Parse incoming protobuf from the Meshtastic radio.
  void _handleFromRadio(Uint8List data) {
    // Simplified parsing — in production use generated protobuf classes
    // For now, we handle raw bytes and extract text messages
    try {
      // Try to extract text message from the payload
      // Meshtastic FromRadio protobuf: field 11 = MeshPacket
      // MeshPacket.decoded.payload contains the text

      final text = _tryExtractText(data);
      if (text != null && text.isNotEmpty) {
        final msg = MeshChatMessage(
          senderId: 'ble-${data.hashCode}',
          senderName: 'Mesh',
          text: text,
          timestamp: DateTime.now(),
        );
        _messages.insert(0, msg);
        notifyListeners();
      }

      // Try to extract node info
      final node = _tryExtractNodeInfo(data);
      if (node != null) {
        _nodes.removeWhere((n) => n.nodeId == node.nodeId);
        _nodes.insert(0, node);
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Error parsing FromRadio: $e');
    }
  }

  /// Attempt to extract a text message from raw protobuf bytes.
  String? _tryExtractText(Uint8List data) {
    // Look for UTF-8 text content in the protobuf payload
    // Field tag for text in Data protobuf is typically tag 1 (string)
    // This is a simplified parser — production should use protobuf codegen
    try {
      final str = utf8.decode(data, allowMalformed: true);
      // Look for readable text sequences
      final match = RegExp(r'[\x20-\x7E\u00C0-\u024F]{4,}').firstMatch(str);
      if (match != null) {
        final extracted = match.group(0)!.trim();
        // Filter out obvious protobuf artifacts
        if (extracted.length > 3 && !extracted.startsWith('\x00')) {
          return extracted;
        }
      }
    } catch (_) {}
    return null;
  }

  /// Attempt to extract node info from raw protobuf bytes.
  MeshNodeInfo? _tryExtractNodeInfo(Uint8List data) {
    // Simplified — production should use protobuf codegen
    // Look for NodeInfo packets (field 7 in FromRadio)
    try {
      if (data.length > 20) {
        // Check if this looks like a NodeInfo packet
        // For now return null — full implementation needs protobuf gen
        return null;
      }
    } catch (_) {}
    return null;
  }

  /// Request initial configuration from the connected device.
  Future<void> _requestConfig(String deviceId) async {
    final toRadioChar = QualifiedCharacteristic(
      serviceId: Uuid.parse(MeshtasticBLE.serviceUuid),
      characteristicId: Uuid.parse(MeshtasticBLE.toRadioUuid),
      deviceId: deviceId,
    );

    // Send a "want_config_id" request to get initial node list
    // Protobuf: ToRadio { want_config_id = 1 }
    // Field 3 (want_config_id), varint encoding
    final configRequest = Uint8List.fromList([0x18, 0x01]); // tag 3, value 1

    try {
      await _ble.writeCharacteristicWithResponse(
        toRadioChar,
        value: configRequest,
      );
    } catch (e) {
      debugPrint('Error requesting config: $e');
    }
  }

  // ── BLE Send ──────────────────────────────────────────────────────────

  /// Send a text message via BLE to the connected Meshtastic device.
  Future<void> sendMessageBLE(String text, {int channel = 0}) async {
    if (_connectedDeviceId == null) return;

    final toRadioChar = QualifiedCharacteristic(
      serviceId: Uuid.parse(MeshtasticBLE.serviceUuid),
      characteristicId: Uuid.parse(MeshtasticBLE.toRadioUuid),
      deviceId: _connectedDeviceId!,
    );

    // Encode text message as Meshtastic protobuf
    // ToRadio { packet { decoded { portnum: TEXT_MESSAGE_APP, payload: text } } }
    final textBytes = utf8.encode(text);
    final payload = _buildTextMessageProto(textBytes, channel);

    try {
      // Meshtastic BLE requires chunked writes with 4-byte length prefix
      final framedData = _frameForBLE(payload);
      for (final chunk in framedData) {
        await _ble.writeCharacteristicWithResponse(
          toRadioChar,
          value: chunk,
        );
      }

      // Optimistic local insert
      _messages.insert(0, MeshChatMessage(
        senderId: 'me',
        senderName: 'Yo',
        text: text,
        channel: channel,
        timestamp: DateTime.now(),
        isMine: true,
      ));
      notifyListeners();
    } catch (e) {
      _error = 'Error al enviar: $e';
      notifyListeners();
    }
  }

  /// Build a ToRadio protobuf with a text message payload.
  Uint8List _buildTextMessageProto(List<int> textBytes, int channel) {
    // Simplified protobuf encoding:
    // ToRadio {
    //   packet (field 2) {
    //     decoded (field 3) {
    //       portnum (field 1): 1 (TEXT_MESSAGE_APP)
    //       payload (field 2): textBytes
    //     }
    //     channel (field 8): channel
    //   }
    // }

    // Inner: Data { portnum=1, payload=text }
    final portnum = [0x08, 0x01]; // field 1, varint 1
    final payloadTag = [0x12, textBytes.length]; // field 2, length-delimited
    final innerData = [...portnum, ...payloadTag, ...textBytes];

    // MeshPacket { decoded=innerData, channel=channel }
    final decodedTag = [0x1A, innerData.length]; // field 3, length-delimited
    final channelField = channel > 0 ? [0x40, channel] : <int>[]; // field 8, varint
    final meshPacket = [...decodedTag, ...innerData, ...channelField];

    // ToRadio { packet=meshPacket }
    final packetTag = [0x12, meshPacket.length]; // field 2, length-delimited
    final toRadio = [...packetTag, ...meshPacket];

    return Uint8List.fromList(toRadio);
  }

  /// Frame protobuf data for BLE transport (4-byte header + chunks of max 512 bytes).
  List<Uint8List> _frameForBLE(Uint8List data) {
    const maxChunk = 508; // 512 - 4 byte header
    final frames = <Uint8List>[];

    // First frame: 4-byte little-endian length + data
    final header = ByteData(4);
    header.setUint32(0, data.length, Endian.little);
    final headerBytes = header.buffer.asUint8List();

    final firstChunkSize = data.length > maxChunk ? maxChunk : data.length;
    frames.add(Uint8List.fromList([
      ...headerBytes,
      ...data.sublist(0, firstChunkSize),
    ]));

    // Remaining frames (if data > 508 bytes)
    for (var offset = firstChunkSize; offset < data.length; offset += 512) {
      final end = (offset + 512 > data.length) ? data.length : offset + 512;
      frames.add(Uint8List.fromList(data.sublist(offset, end)));
    }

    return frames;
  }

  // ── BLE Disconnect ────────────────────────────────────────────────────

  void disconnectBLE() {
    _notifySubscription?.cancel();
    _fromRadioSubscription?.cancel();
    _connectionSubscription?.cancel();
    _connectedDeviceId = null;
    _mode = MeshConnectionMode.disconnected;
    notifyListeners();
  }

  // ── HTTP Gateway Fallback ─────────────────────────────────────────────

  /// Connect via backend HTTP gateway (when internet is available).
  void connectGateway() {
    try {
      _wsChannel = WebSocketChannel.connect(
        Uri.parse('ws://10.0.2.2:8000/api/v1/mesh/ws'),
      );

      _wsChannel!.stream.listen(
        (message) {
          final data = jsonDecode(message);
          final type = data['type'];

          if (type == 'message') {
            final msg = MeshChatMessage.fromJson(data['data']);
            _messages.insert(0, msg);
            notifyListeners();
          } else if (type == 'node_update') {
            final node = MeshNodeInfo.fromJson(data['data']);
            _nodes.removeWhere((n) => n.nodeId == node.nodeId);
            _nodes.insert(0, node);
            notifyListeners();
          }
        },
        onError: (e) {
          debugPrint('Mesh WS error: $e');
          _mode = MeshConnectionMode.disconnected;
          notifyListeners();
        },
        onDone: () {
          _mode = MeshConnectionMode.disconnected;
          notifyListeners();
        },
      );

      _mode = MeshConnectionMode.httpGateway;
      notifyListeners();
      loadHistory();
      loadNodes();
    } catch (e) {
      debugPrint('Mesh WS connect failed: $e');
    }
  }

  /// Send message via HTTP gateway.
  Future<void> sendMessageHTTP(String text, {int channel = 0}) async {
    if (_wsChannel != null) {
      _wsChannel!.sink.add(jsonEncode({
        'action': 'send',
        'text': text,
        'channel': channel,
        'destination': '^all',
      }));

      _messages.insert(0, MeshChatMessage(
        senderId: 'me',
        senderName: 'Yo',
        text: text,
        channel: channel,
        timestamp: DateTime.now(),
        isMine: true,
      ));
      notifyListeners();
    }
  }

  // ── Unified Send ──────────────────────────────────────────────────────

  /// Send a message using the active connection mode.
  Future<void> sendMessage(String text, {int channel = 0}) async {
    if (text.length > 228) text = text.substring(0, 228);

    if (_mode == MeshConnectionMode.bleConnected) {
      await sendMessageBLE(text, channel: channel);
    } else if (_mode == MeshConnectionMode.httpGateway) {
      await sendMessageHTTP(text, channel: channel);
    }
  }

  // ── REST API helpers ──────────────────────────────────────────────────

  Future<void> loadHistory() async {
    try {
      final resp = await http.get(Uri.parse('$baseUrl/messages?limit=100'));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        final list = data['messages'] as List;
        _messages.clear();
        _messages.addAll(list.map((j) => MeshChatMessage.fromJson(j)));
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Failed to load mesh history: $e');
    }
  }

  Future<void> loadNodes() async {
    try {
      final resp = await http.get(Uri.parse('$baseUrl/nodes'));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        final list = data['nodes'] as List;
        _nodes.clear();
        _nodes.addAll(list.map((j) => MeshNodeInfo.fromJson(j)));
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Failed to load mesh nodes: $e');
    }
  }

  @override
  void dispose() {
    _scanSubscription?.cancel();
    _connectionSubscription?.cancel();
    _fromRadioSubscription?.cancel();
    _notifySubscription?.cancel();
    _wsChannel?.sink.close();
    super.dispose();
  }
}
