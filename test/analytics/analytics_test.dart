import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:helssa_app/analytics/analytics.dart';
import 'package:helssa_app/core/http/helssa_client.dart';

void main() {
  test('masks sensitive props and enforces ring buffer', () async {
    final a = Analytics(uploadEnabled: false);
    a.emit('start_order', props: {'password': 'x', 'otp': '1234', 'ok': 1});
    final dump = a.dump();
    expect(dump.first['props']['password'], '***');
    expect(dump.first['props']['otp'], '***');
    // ring buffer
    for (var i = 0; i < 250; i++) {
      a.emit('e$i');
    }
    expect(a.dump().length, 200);
  });

  test('safe failure on 404 when upload enabled', () async {
    final mock = MockClient((http.Request req) async {
      return http.Response('nope', 404);
    });
    final client = HelssaClient(baseUrl: 'http://example.com', client: mock);
    final a = Analytics(uploadEnabled: true, client: client);
    a.emit('view_landing');
    await a.flush(); // should not throw
  });
}
