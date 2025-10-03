import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';

import '../../config/env.dart';

class HelssaResponse {
  final String requestId;
  final int statusCode;
  final dynamic json; // may be null
  final String bodyText;
  HelssaResponse(this.requestId, this.statusCode, this.json, this.bodyText);
  bool get ok => statusCode >= 200 && statusCode < 300;
}

class HelssaClient {
  final String baseUrl;
  final http.Client _client;
  final _uuid = const Uuid();
  HelssaClient({String? baseUrl, http.Client? client})
      : baseUrl = (baseUrl ?? Env.apiBaseUrl).endsWith('/')
            ? (baseUrl ?? Env.apiBaseUrl)
            : '${baseUrl ?? Env.apiBaseUrl}/',
        _client = client ?? http.Client();

  Uri _resolve(String path) {
    final clean = path.startsWith('/') ? path.substring(1) : path;
    return Uri.parse(baseUrl).resolve(clean);
  }

  Future<HelssaResponse> request(
    String method,
    String path, {
    Map<String, String>? headers,
    Object? body,
    String? idempotencyKey,
    Duration timeout = const Duration(seconds: 10),
  }) async {
    final reqId = _uuid.v4();
    final hdrs = <String, String>{
      'Accept': 'application/json',
      'X-Request-ID': reqId,
      ...?headers,
    };
    String? payload;
    if (body != null) {
      if (body is String) {
        payload = body;
      } else {
        payload = jsonEncode(body);
      }
      hdrs.putIfAbsent('Content-Type', () => 'application/json; charset=utf-8');
    }
    if (idempotencyKey != null && idempotencyKey.isNotEmpty) {
      hdrs['X-Idempotency-Key'] = idempotencyKey;
    }
    final uri = _resolve(path);
    final methodUp = method.toUpperCase();
    final isIdem = methodUp == 'GET' || methodUp == 'HEAD' || (methodUp == 'POST' && idempotencyKey != null);
    int attempts = 0;
    int maxAttempts = 3;
    final rnd = Random();
    int sleptMs = 0;
    while (true) {
      attempts += 1;
      try {
        final http.Response r = await _send(methodUp, uri, hdrs, payload)
            .timeout(timeout);
        final txt = r.body;
        dynamic j;
        try {
          j = txt.isNotEmpty ? jsonDecode(txt) : null;
        } catch (_) {
          j = null;
        }
        if (r.statusCode >= 500 && r.statusCode < 600 && isIdem && attempts < maxAttempts) {
          // retryable 5xx
        } else {
          return HelssaResponse(reqId, r.statusCode, j, txt);
        }
      } on TimeoutException catch (_) {
        if (!(isIdem && attempts < maxAttempts)) {
          return HelssaResponse(reqId, 599, null, 'timeout');
        }
      } on SocketException catch (_) {
        if (!(isIdem && attempts < maxAttempts)) {
          return HelssaResponse(reqId, 0, null, 'network_error');
        }
      } on http.ClientException catch (_) {
        if (!(isIdem && attempts < maxAttempts)) {
          return HelssaResponse(reqId, 0, null, 'client_error');
        }
      }
      // backoff with jitter, cap total ~6s
      final base = 200 * (1 << (attempts - 1)); // 200ms, 400ms
      final jitter = 100 + rnd.nextInt(200); // 100-300ms
      int wait = base + jitter;
      if (sleptMs + wait > 6000) break;
      await Future.delayed(Duration(milliseconds: wait));
      sleptMs += wait;
      if (attempts >= maxAttempts) break;
    }
    return HelssaResponse(reqId, 599, null, 'retry_exhausted');
  }

  Future<http.Response> _send(
      String method, Uri uri, Map<String, String> headers, String? payload) {
    switch (method) {
      case 'GET':
        return _client.get(uri, headers: headers);
      case 'HEAD':
        return _client.head(uri, headers: headers);
      case 'POST':
        return _client.post(uri, headers: headers, body: payload);
      case 'PUT':
        return _client.put(uri, headers: headers, body: payload);
      case 'DELETE':
        return _client.delete(uri, headers: headers, body: payload);
      default:
        return _client.send(http.Request(method, uri)..headers.addAll(headers)..bodyBytes = (payload ?? '').codeUnits)
            .then(http.Response.fromStream);
    }
  }
}
