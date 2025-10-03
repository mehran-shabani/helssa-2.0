import 'dart:convert';

import 'package:flutter/material.dart';

import '../../core/http/helssa_client.dart';

class SystemStatusPage extends StatefulWidget {
  final HelssaClient? client;
  const SystemStatusPage({super.key, this.client});

  @override
  State<SystemStatusPage> createState() => _SystemStatusPageState();
}

class _SystemStatusPageState extends State<SystemStatusPage> {
  late final HelssaClient _client = widget.client ?? HelssaClient();
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _ready;
  String? _healthReqId, _readyReqId;

  @override
  void initState() {
    super.initState();
    _loadHealth();
  }

  Future<void> _loadHealth() async {
    final r = await _client.request('GET', '/api/v1/system/health');
    _healthReqId = r.requestId;
    _health = _decode(r);
    if (mounted) setState(() {});
  }

  Future<void> _deepCheck() async {
    final r = await _client.request('GET', '/api/v1/system/ready');
    _readyReqId = r.requestId;
    _ready = _decode(r);
    if (mounted) setState(() {});
  }

  Map<String, dynamic>? _decode(HelssaResponse r) {
    if (r.json is Map<String, dynamic>) return r.json as Map<String, dynamic>;
    try {
      return json.decode(r.bodyText) as Map<String, dynamic>;
    } catch (_) {
      return {'status': 'unknown', 'raw': r.bodyText, 'code': r.statusCode};
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('System Status')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Health (${_healthReqId ?? '-'})',
                style: const TextStyle(fontWeight: FontWeight.bold)),
            Text('${_health ?? {}}'),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _deepCheck, child: const Text('Deep check (staff)')),
            const SizedBox(height: 12),
            if (_ready != null)
              (_ready!['code'] == 401 || _ready!['code'] == 403)
                  ? const Text('Restricted (staff-only). Login required.')
                  : Text('Ready (${_readyReqId ?? '-'}) → $_ready'),
          ],
        ),
      ),
    );
  }
}
