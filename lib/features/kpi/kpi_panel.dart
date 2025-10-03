import 'dart:convert';

import 'package:flutter/material.dart';

import '../../config/env.dart';
import '../../core/http/helssa_client.dart';

class KpiPanel extends StatefulWidget {
  final HelssaClient? client;
  const KpiPanel({super.key, this.client});

  @override
  State<KpiPanel> createState() => _KpiPanelState();
}

class _KpiPanelState extends State<KpiPanel> {
  late final HelssaClient _client = widget.client ?? HelssaClient();
  Future<Map<String, dynamic>>? _future;

  @override
  void initState() {
    super.initState();
    if (!(Env.kpiPanelEnabled && Env.showDevMenu)) return;
    final now = DateTime.now();
    final from = now.subtract(const Duration(days: 7));
    String d(DateTime x) => x.toIso8601String().substring(0, 10);
    _future = _fetch('/api/v1/analytics/daily?from=${d(from)}&to=${d(now)}');
  }

  Future<Map<String, dynamic>> _fetch(String path) async {
    final r = await _client.request('GET', path);
    if (r.statusCode == 401 || r.statusCode == 403) {
      return {'restricted': true, 'requestId': r.requestId};
    }
    if (!r.ok) {
      return {'error': 'HTTP ${r.statusCode}', 'requestId': r.requestId};
    }
    if (r.json is Map<String, dynamic>) return r.json as Map<String, dynamic>;
    try {
      return json.decode(r.bodyText) as Map<String, dynamic>;
    } catch (_) {
      return {'error': 'Invalid JSON', 'requestId': r.requestId};
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!(Env.kpiPanelEnabled && Env.showDevMenu)) {
      return const SizedBox.shrink();
    }
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        final data = snap.data ?? {};
        if (data['restricted'] == true) {
          return const Center(child: Text('Restricted (staff-only)'));
        }
        if (data.containsKey('error')) {
          return Center(child: Text('Error: ${data['error']}'));
        }
        final todayDelivered = data['today_delivered'] ?? data['todayDelivered'] ?? '—';
        final medianTat = data['median_tat'] ?? '—';
        final p95Tat = data['p95_tat'] ?? '—';
        final paySuccess = data['pay_success_count'] ?? '—';
        return GridView.count(
          crossAxisCount: 2,
          childAspectRatio: 1.6,
          padding: const EdgeInsets.all(12),
          children: [
            _card('Today Delivered', '$todayDelivered'),
            _card('Median TAT (m)', '$medianTat'),
            _card('p95 TAT (m)', '$p95Tat'),
            _card('Pay Success', '$paySuccess'),
          ],
        );
      },
    );
  }

  Widget _card(String title, String value) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 20)),
          ],
        ),
      ),
    );
  }
}
