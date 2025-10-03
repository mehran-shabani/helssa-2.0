import 'package:flutter/material.dart';

enum RxState { DRAFT, SUBMITTED, INS_PENDING, INS_CONFIRMED, DELIVERED }

class PrescriptionStages {
  final DateTime? draft, submitted, insPending, insConfirmed, delivered;
  const PrescriptionStages({
    this.draft,
    this.submitted,
    this.insPending,
    this.insConfirmed,
    this.delivered,
  });
}

class PrescriptionTimeline extends StatelessWidget {
  final PrescriptionStages stages;
  const PrescriptionTimeline({super.key, required this.stages});

  @override
  Widget build(BuildContext context) {
    final entries = <MapEntry<String, DateTime?>>[
      MapEntry('DRAFT', stages.draft),
      MapEntry('SUBMITTED', stages.submitted),
      MapEntry('INS_PENDING', stages.insPending),
      MapEntry('INS_CONFIRMED', stages.insConfirmed),
      MapEntry('DELIVERED', stages.delivered),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: entries.map((e) => _row(e.key, e.value)).toList(),
    );
  }

  Widget _row(String label, DateTime? ts) {
    final done = ts != null;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(done ? Icons.check_circle : Icons.radio_button_unchecked),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
              Text(done ? ts!.toLocal().toString() : 'pending'),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ],
    );
  }
}
