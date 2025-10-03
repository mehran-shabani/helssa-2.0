import 'dart:async';
import 'dart:convert';

import '../config/env.dart';
import '../core/http/helssa_client.dart';

class AnalyticsEvent {
  final String name;
  final DateTime ts;
  final Map<String, dynamic> props;
  final String? requestId;
  AnalyticsEvent(this.name, this.ts, this.props, {this.requestId});
  Map<String, dynamic> toJson() => {
        'name': name,
        'ts': ts.toIso8601String(),
        'props': props,
        if (requestId != null) 'requestId': requestId,
      };
}

class Analytics {
  final bool uploadEnabled;
  final HelssaClient _client;
  final int _cap;
  final List<AnalyticsEvent> _buf = <AnalyticsEvent>[];
  Timer? _timer;
  bool _uploadSupported = true; // set false if endpoint 404/403

  Analytics({bool? uploadEnabled, HelssaClient? client, int capacity = 200})
      : uploadEnabled = uploadEnabled ?? Env.analyticsUploadEnabled,
        _client = client ?? HelssaClient(),
        _cap = capacity {
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => flush());
  }

  void dispose() => _timer?.cancel();

  void emit(String name, {Map<String, Object?> props = const {}, String? requestId}) {
    final masked = _mask(Map<String, Object?>.from(props));
    final ev = AnalyticsEvent(name, DateTime.now(), masked, requestId: requestId);
    if (_buf.length >= _cap) {
      _buf.removeAt(0);
    }
    _buf.add(ev);
  }

  List<Map<String, dynamic>> dump() => _buf.map((e) => e.toJson()).toList(growable: false);

  Future<void> flush() async {
    if (!uploadEnabled || !_uploadSupported || _buf.isEmpty) return;
    final batch = _buf.map((e) => e.toJson()).toList(growable: false);
    final res = await _client.request('POST', '/api/v1/analytics/client-event',
        body: jsonEncode({'events': batch}));
    if (res.statusCode == 404 || res.statusCode == 403) {
      _uploadSupported = false; // silently stop trying
      return;
    }
    if (res.ok) {
      _buf.clear();
    }
  }

  static Map<String, Object?> _mask(Map<String, Object?> props) {
    const sens = {'password', 'token', 'otp', 'national_code'};
    Map<String, Object?> out = {};
    props.forEach((k, v) {
      if (sens.contains(k)) {
        out[k] = '***';
      } else if (v is Map<String, Object?>) {
        out[k] = _mask(v);
      } else {
        out[k] = v;
      }
    });
    return out;
  }
}

// Common event names (use as needed)
class HelssaEvents {
  static const viewLanding = 'view_landing';
  static const clickCta = 'click_cta';
  static const startOrder = 'start_order';
  static const submitOrder = 'submit_order';
  static const payInitiated = 'pay_initiated';
  static const paySuccessUi = 'pay_success_ui';
  static const rxIssuedUi = 'rx_issued_ui';
  static const rxDeliveredUi = 'rx_delivered_ui';
}

final analytics = Analytics();
