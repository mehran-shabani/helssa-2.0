import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:helssa_app/core/http/helssa_client.dart';
import 'package:helssa_app/features/kpi/kpi_panel.dart';

Widget _mkApp(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  testWidgets('shows restricted placeholder on 403', (tester) async {
    final mock = MockClient((http.Request req) async => http.Response('no', 403));
    final client = HelssaClient(baseUrl: 'http://example.com', client: mock);
    await tester.pumpWidget(_mkApp(KpiPanel(client: client)));
    await tester.pumpAndSettle();
    expect(find.text('Restricted (staff-only)'), findsOneWidget);
  });

  testWidgets('renders metrics on 200', (tester) async {
    final payload = jsonEncode({
      'today_delivered': 12,
      'median_tat': 45,
      'p95_tat': 120,
      'pay_success_count': 30
    });
    final mock = MockClient((http.Request req) async => http.Response(payload, 200));
    final client = HelssaClient(baseUrl: 'http://example.com', client: mock);
    await tester.pumpWidget(_mkApp(SizedBox(height: 400, child: KpiPanel(client: client))));
    await tester.pumpAndSettle();
    expect(find.text('12'), findsWidgets);
    expect(find.text('45'), findsWidgets);
    expect(find.text('120'), findsWidgets);
    expect(find.text('30'), findsWidgets);
  });
}
