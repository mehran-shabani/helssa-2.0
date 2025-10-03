import 'package:flutter/material.dart';

Widget networkErrorBanner(String requestId, {String? details}) {
  return _banner(
    icon: Icons.wifi_off,
    title: 'Network issue',
    requestId: requestId,
    details: details ?? 'Please check your connection.',
    color: Colors.orange.shade100,
  );
}

Widget paymentErrorBanner(String requestId, {String? details}) {
  return _banner(
    icon: Icons.payment,
    title: 'Payment error',
    requestId: requestId,
    details: details ?? 'There was a problem with payment.',
    color: Colors.red.shade100,
  );
}

Widget insuranceErrorBanner(String requestId, {String? details}) {
  return _banner(
    icon: Icons.verified_user,
    title: 'Insurance issue',
    requestId: requestId,
    details: details ?? 'Insurance verification pending/failed.',
    color: Colors.blue.shade100,
  );
}

Widget _banner({
  required IconData icon,
  required String title,
  required String requestId,
  required String details,
  required Color color,
}) {
  return MaterialBanner(
    backgroundColor: color,
    content: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(details),
        const SizedBox(height: 4),
        Text('Request-ID: $requestId', style: const TextStyle(fontSize: 12)),
      ],
    ),
    leading: Icon(icon),
    actions: const [SizedBox.shrink()],
  );
}
