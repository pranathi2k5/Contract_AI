import 'package:flutter/material.dart';
import '../models/contract_model.dart';

class LawsScreen extends StatelessWidget {
  final List<IndianLawMapping> laws;

  const LawsScreen({Key? key, required this.laws}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: laws.length,
        itemBuilder: (context, index) {
          final law = laws[index];
          return Container(
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1A2E),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.balance_rounded, color: Color(0xFF00D2FF)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        law.actName,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: Color(0xFF00D2FF)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.purple.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.purpleAccent),
                  ),
                  child: Text(
                    law.section,
                    style: const TextStyle(color: Colors.purpleAccent, fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  law.applicabilityReason,
                  style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
