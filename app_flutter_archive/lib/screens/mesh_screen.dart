import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../config/theme.dart';
import '../services/mesh_service.dart';

/// Meshtastic mesh chat & communications screen.
///
/// Three tabs: Devices (BLE scan/connect), Chat, Nodes.
/// Supports BLE direct (offline) and HTTP gateway (online) modes.
class MeshScreen extends StatefulWidget {
  const MeshScreen({super.key});

  @override
  State<MeshScreen> createState() => _MeshScreenState();
}

class _MeshScreenState extends State<MeshScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _messageController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => MeshService(),
      child: Consumer<MeshService>(
        builder: (context, mesh, _) {
          return Scaffold(
            backgroundColor: ESPAlertTheme.background,
            appBar: AppBar(
              title: Row(
                children: [
                  const Text('📡 Mesh Radio'),
                  const SizedBox(width: 10),
                  _connectionBadge(mesh),
                ],
              ),
              bottom: TabBar(
                controller: _tabController,
                indicatorColor: ESPAlertTheme.primary,
                labelColor: ESPAlertTheme.primary,
                unselectedLabelColor: Colors.white54,
                tabs: [
                  const Tab(icon: Icon(Icons.bluetooth_searching, size: 20), text: 'Dispositivos'),
                  Tab(icon: const Icon(Icons.chat_bubble_outline, size: 20),
                      text: 'Chat (${mesh.messages.length})'),
                  Tab(icon: const Icon(Icons.cell_tower, size: 20),
                      text: 'Nodos (${mesh.nodes.length})'),
                ],
              ),
            ),
            body: TabBarView(
              controller: _tabController,
              children: [
                _buildDevicesTab(mesh),
                _buildChatTab(mesh),
                _buildNodesTab(mesh),
              ],
            ),
          );
        },
      ),
    );
  }

  // ── Devices Tab (BLE Scan & Connect) ──────────────────────────────────

  Widget _buildDevicesTab(MeshService mesh) {
    return Column(
      children: [
        // Mode selector banner
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          color: ESPAlertTheme.secondary.withOpacity(0.3),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    mesh.isBLE ? Icons.bluetooth_connected : Icons.wifi,
                    color: ESPAlertTheme.primary,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    mesh.isBLE
                        ? 'Conectado por Bluetooth (sin internet)'
                        : mesh.isHTTP
                            ? 'Conectado vía servidor (con internet)'
                            : 'Desconectado',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.8),
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'La conexión BLE permite comunicarte por LoRa '
                'sin necesidad de internet ni cobertura móvil.',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.white.withOpacity(0.5),
                ),
              ),
            ],
          ),
        ),

        // Action buttons
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // BLE Scan button
              Expanded(
                child: _actionButton(
                  icon: Icons.bluetooth_searching,
                  label: mesh.scanning ? 'Buscando...' : 'Buscar BLE',
                  color: ESPAlertTheme.primary,
                  loading: mesh.scanning,
                  onPressed: mesh.scanning ? null : () => mesh.startScan(),
                ),
              ),
              const SizedBox(width: 8),
              // HTTP Gateway button
              Expanded(
                child: _actionButton(
                  icon: Icons.cloud,
                  label: mesh.isHTTP ? 'Conectado' : 'Gateway HTTP',
                  color: ESPAlertTheme.meteoColor,
                  onPressed: mesh.isHTTP ? null : () {
                    mesh.connectGateway();
                    _tabController.animateTo(1); // Switch to chat
                  },
                ),
              ),
              if (mesh.connected) ...[
                const SizedBox(width: 8),
                // Disconnect button
                SizedBox(
                  width: 48,
                  child: _actionButton(
                    icon: Icons.link_off,
                    label: '',
                    color: ESPAlertTheme.accent,
                    onPressed: () {
                      if (mesh.isBLE) {
                        mesh.disconnectBLE();
                      }
                    },
                  ),
                ),
              ],
            ],
          ),
        ),

        // Error message
        if (mesh.error != null)
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: ESPAlertTheme.accent.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: ESPAlertTheme.accent.withOpacity(0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.error_outline, color: ESPAlertTheme.accent, size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(mesh.error!, style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 13))),
              ],
            ),
          ),

        // Device list
        Expanded(
          child: mesh.scannedDevices.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('📻', style: TextStyle(fontSize: 48)),
                      const SizedBox(height: 12),
                      Text(
                        'Pulsa "Buscar BLE" para encontrar\ndispositivos Meshtastic cercanos',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.4),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: mesh.scannedDevices.length,
                  itemBuilder: (ctx, i) {
                    final dev = mesh.scannedDevices[i];
                    return _buildDeviceCard(dev, mesh);
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildDeviceCard(MeshtasticDevice device, MeshService mesh) {
    final signalStrength = _rssiToPercent(device.rssi);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: ESPAlertTheme.surfaceVariant,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: ESPAlertTheme.primary.withOpacity(0.2)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: ESPAlertTheme.primary.withOpacity(0.15),
            shape: BoxShape.circle,
          ),
          child: const Center(
            child: Icon(Icons.router, color: ESPAlertTheme.primary, size: 24),
          ),
        ),
        title: Text(
          device.name,
          style: const TextStyle(fontWeight: FontWeight.w700, color: Colors.white),
        ),
        subtitle: Row(
          children: [
            Icon(Icons.signal_cellular_alt, size: 14, color: _signalColor(signalStrength)),
            const SizedBox(width: 4),
            Text(
              '$signalStrength% (${device.rssi} dBm)',
              style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5)),
            ),
          ],
        ),
        trailing: ElevatedButton(
          onPressed: () {
            mesh.connectBLE(device.id);
            _tabController.animateTo(1); // Switch to chat
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: ESPAlertTheme.primary,
            foregroundColor: ESPAlertTheme.background,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          ),
          child: const Text('Conectar', style: TextStyle(fontWeight: FontWeight.w700)),
        ),
      ),
    ).animate().fadeIn(duration: 200.ms);
  }

  Widget _actionButton({
    required IconData icon,
    required String label,
    required Color color,
    bool loading = false,
    VoidCallback? onPressed,
  }) {
    return SizedBox(
      height: 48,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: color.withOpacity(onPressed == null ? 0.3 : 0.15),
          foregroundColor: color,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: color.withOpacity(0.3)),
          ),
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 12),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (loading)
              SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: color))
            else
              Icon(icon, size: 18),
            if (label.isNotEmpty) ...[
              const SizedBox(width: 6),
              Flexible(child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700), overflow: TextOverflow.ellipsis)),
            ],
          ],
        ),
      ),
    );
  }

  // ── Chat Tab ──────────────────────────────────────────────────────────

  Widget _buildChatTab(MeshService mesh) {
    return Column(
      children: [
        // Mode indicator
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: ESPAlertTheme.secondary.withOpacity(0.2),
          child: Row(
            children: [
              Icon(
                mesh.isBLE ? Icons.bluetooth : mesh.isHTTP ? Icons.wifi : Icons.wifi_off,
                size: 14,
                color: mesh.connected ? ESPAlertTheme.severityGreen : ESPAlertTheme.severityRed,
              ),
              const SizedBox(width: 6),
              Text(
                mesh.isBLE
                    ? '📶 BLE Directo — sin internet'
                    : mesh.isHTTP
                        ? '🌐 Gateway HTTP'
                        : '❌ Desconectado — conecta un dispositivo',
                style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.6)),
              ),
            ],
          ),
        ),

        // Messages list
        Expanded(
          child: mesh.messages.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('📡', style: TextStyle(fontSize: 48)),
                      const SizedBox(height: 12),
                      Text(
                        mesh.connected
                            ? 'Sin mensajes — envía el primero'
                            : 'Conecta un dispositivo Meshtastic\nen la pestaña "Dispositivos"',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 14),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  reverse: true,
                  itemCount: mesh.messages.length,
                  itemBuilder: (ctx, i) => _buildMessageBubble(mesh.messages[i]),
                ),
        ),

        // Input
        _buildMessageInput(mesh),
      ],
    );
  }

  Widget _buildMessageBubble(MeshChatMessage msg) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: msg.isMine ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!msg.isMine) ...[
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(color: _nodeColor(msg.senderId), shape: BoxShape.circle),
              child: Center(child: Text(
                msg.senderName.isNotEmpty ? msg.senderName[0].toUpperCase() : '?',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14),
              )),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: msg.isMine
                    ? ESPAlertTheme.primary.withOpacity(0.2)
                    : ESPAlertTheme.surfaceVariant,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(msg.isMine ? 16 : 4),
                  bottomRight: Radius.circular(msg.isMine ? 4 : 16),
                ),
                border: msg.isMine ? Border.all(color: ESPAlertTheme.primary.withOpacity(0.3)) : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!msg.isMine)
                    Text(msg.senderName, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: _nodeColor(msg.senderId))),
                  Text(msg.text, style: const TextStyle(fontSize: 15, color: Colors.white, height: 1.3)),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_formatTime(msg.timestamp), style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4))),
                      if (msg.snr != null) ...[
                        const SizedBox(width: 8),
                        Text('${msg.snr!.toStringAsFixed(1)}dB', style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.3))),
                      ],
                      if (msg.hopCount != null && msg.hopCount! > 0) ...[
                        const SizedBox(width: 8),
                        Text('${msg.hopCount} saltos', style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.3))),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),
          if (msg.isMine) const SizedBox(width: 40),
        ],
      ),
    ).animate().fadeIn(duration: 200.ms);
  }

  Widget _buildMessageInput(MeshService mesh) {
    return Container(
      padding: EdgeInsets.only(left: 12, right: 8, top: 8, bottom: MediaQuery.of(context).padding.bottom + 8),
      decoration: BoxDecoration(
        color: ESPAlertTheme.surface,
        border: Border(top: BorderSide(color: Colors.white.withOpacity(0.1))),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
            decoration: BoxDecoration(
              color: ESPAlertTheme.secondary.withOpacity(0.5),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              mesh.isBLE ? 'BLE' : 'HTTP',
              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: mesh.isBLE ? ESPAlertTheme.primary : ESPAlertTheme.meteoColor),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: _messageController,
              maxLength: 228,
              maxLines: null,
              style: const TextStyle(fontSize: 15, color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Mensaje mesh...',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
                counterText: '',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                filled: true,
                fillColor: ESPAlertTheme.surfaceVariant,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _send(mesh),
              enabled: mesh.connected,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              color: mesh.connected ? ESPAlertTheme.primary : Colors.white24,
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: const Icon(Icons.send, size: 20),
              color: ESPAlertTheme.background,
              onPressed: mesh.connected ? () => _send(mesh) : null,
            ),
          ),
        ],
      ),
    );
  }

  void _send(MeshService mesh) {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;
    mesh.sendMessage(text);
    _messageController.clear();
  }

  // ── Nodes Tab ─────────────────────────────────────────────────────────

  Widget _buildNodesTab(MeshService mesh) {
    if (mesh.nodes.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('📡', style: TextStyle(fontSize: 48)),
            const SizedBox(height: 12),
            Text('No hay nodos detectados', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 16)),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: mesh.nodes.length,
      itemBuilder: (ctx, i) => _buildNodeCard(mesh.nodes[i]),
    );
  }

  Widget _buildNodeCard(MeshNodeInfo node) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: ESPAlertTheme.surfaceVariant,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _nodeColor(node.nodeId).withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              color: _nodeColor(node.nodeId).withOpacity(0.2),
              shape: BoxShape.circle,
              border: Border.all(color: _nodeColor(node.nodeId).withOpacity(0.5)),
            ),
            child: Center(child: Text(node.shortName, style: TextStyle(color: _nodeColor(node.nodeId), fontWeight: FontWeight.w800, fontSize: 14))),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(node.longName, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    if (node.batteryLevel != null) ...[
                      Icon(_batteryIcon(node.batteryLevel!), size: 14, color: _batteryColor(node.batteryLevel!)),
                      const SizedBox(width: 4),
                      Text('${node.batteryLevel}%', style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5))),
                      const SizedBox(width: 12),
                    ],
                    if (node.snr != null) ...[
                      Text('${node.snr!.toStringAsFixed(1)}dB', style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5))),
                      const SizedBox(width: 12),
                    ],
                    if (node.lat != null && node.lon != null)
                      Text('${node.lat!.toStringAsFixed(3)}°, ${node.lon!.toStringAsFixed(3)}°',
                          style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5))),
                  ],
                ),
              ],
            ),
          ),
          if (node.lastHeard != null)
            Text(timeago.format(node.lastHeard!, locale: 'es'),
                style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.4))),
        ],
      ),
    ).animate().fadeIn(duration: 200.ms);
  }

  // ── Helpers ───────────────────────────────────────────────────────────

  Widget _connectionBadge(MeshService mesh) {
    final Color color;
    final String label;
    final IconData icon;

    switch (mesh.mode) {
      case MeshConnectionMode.bleConnected:
        color = ESPAlertTheme.severityGreen;
        label = 'BLE';
        icon = Icons.bluetooth_connected;
        break;
      case MeshConnectionMode.httpGateway:
        color = ESPAlertTheme.meteoColor;
        label = 'HTTP';
        icon = Icons.cloud;
        break;
      case MeshConnectionMode.bleScanning:
        color = ESPAlertTheme.severityYellow;
        label = 'SCAN';
        icon = Icons.bluetooth_searching;
        break;
      default:
        color = ESPAlertTheme.severityRed;
        label = 'OFF';
        icon = Icons.bluetooth_disabled;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: color, letterSpacing: 0.5)),
        ],
      ),
    );
  }

  int _rssiToPercent(int rssi) => ((rssi + 100).clamp(0, 60) * 100 / 60).round();
  Color _signalColor(int percent) => percent > 60 ? ESPAlertTheme.severityGreen : percent > 30 ? ESPAlertTheme.severityYellow : ESPAlertTheme.severityRed;
  Color _nodeColor(String nodeId) {
    const colors = [Color(0xFF4ECDC4), Color(0xFFFF6B6B), Color(0xFF45B7D1), Color(0xFFFFA07A), Color(0xFF98D8C8), Color(0xFFF7DC6F), Color(0xFFBB8FCE), Color(0xFF82E0AA)];
    return colors[nodeId.hashCode.abs() % colors.length];
  }
  IconData _batteryIcon(int l) => l > 80 ? Icons.battery_full : l > 60 ? Icons.battery_5_bar : l > 40 ? Icons.battery_3_bar : l > 20 ? Icons.battery_2_bar : Icons.battery_alert;
  Color _batteryColor(int l) => l > 50 ? ESPAlertTheme.severityGreen : l > 20 ? ESPAlertTheme.severityYellow : ESPAlertTheme.severityRed;
  String _formatTime(DateTime dt) => '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
}
