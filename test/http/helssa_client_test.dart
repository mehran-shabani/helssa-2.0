import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:helssa_app/core/http/helssa_client.dart';

void main() {
  test('adds X-Request-ID header', () async {
    String? seenReqId;
    final mock = MockClient((http.Request req) async {
      seenReqId = req.headers['X-Request-ID'];
      return http.Response('{}', 200);
    });
    final client = HelssaClient(baseUrl: 'http://example.com', client: mock);
    final res = await client.request('GET', '/ping');
    expect(res.ok, true);
    expect(seenReqId, isNotEmpty);
  });

  test('retries GET on 5xx', () async {
    int calls = 0;
    final mock = MockClient((http.Request req) async {
      calls++;
      if (calls < 3) return http.Response('err', 500);
      return http.Response('{}', 200);
    });
    final client = HelssaClient(baseUrl: 'http://example.com', client: mock);
    final res = await client.request('GET', '/unstable');
    expect(res.ok, true);
    expect(calls, 3);
  });

  test('does not retry POST without idempotency key', () async {
    int calls = 0;
    final mock = MockClient((http.Request req) async {
      calls++;
      return http.Response('oops', 500);
    });
    final client = HelssaClient(baseUrl: 'http://example.com', client: mock);
    final res = await client.request('POST', '/submit', body: {'a': 1});
    expect(res.statusCode, 500);
    expect(calls, 1);
  });

  test('timeout enforced per attempt', () async {
    final mock = MockClient((http.Request req) async {
      await Future<void>.delayed(const Duration(milliseconds: 200));
      return http.Response('{}', 200);
    });
    final client = HelssaClient(baseUrl: 'http://example.com', client: mock);
    final res = await client.request('POST', '/slow', timeout: const Duration(milliseconds: 100));
    expect(res.statusCode, 599); // timeout path
  });
}
