import 'package:flutter/material.dart';
import '../models/contract_model.dart';

class RiskDetailsScreen extends StatelessWidget {
  final ContractAnalysisResult? result;

  const RiskDetailsScreen({Key? key, this.result}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (result == null) return const Center(child: Text('No contract loaded'));

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          automaticallyImplyLeading: false,
          title: const TabBar(
            indicatorColor: Color(0xFF00D2FF),
            tabs: [
              Tab(icon: Icon(Icons.warning_rounded), text: 'Risky Clauses'),
              Tab(icon: Icon(Icons.extension_off_rounded), text: 'Missing Clauses'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            // Risky Clauses List
            ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: result!.riskClauses.length,
              itemBuilder: (context, index) {
                final clause = result!.riskClauses[index];
                return Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A1A2E),
                    borderRadius: BorderRadius.circular(16),
                    border: Border(
                      left: BorderSide(
                        color: clause.riskLevel == 'HIGH' ? Colors.redAccent : Colors.orangeAccent,
                        width: 4,
                      ),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              clause.title,
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                          ),
                          Chip(
                            label: Text(clause.riskLevel, style: const TextStyle(fontSize: 10, color: Colors.white)),
                            backgroundColor: clause.riskLevel == 'HIGH' ? Colors.redAccent.withOpacity(0.3) : Colors.orange.withOpacity(0.3),
                          )
                        ],
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F0F1E),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '"${clause.text}"',
                          style: const TextStyle(fontStyle: FontStyle.italic, color: Colors.white70, fontSize: 13),
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text('Risk Rationale: ${clause.explanation}', style: const TextStyle(fontSize: 13, color: Colors.white70)),
                      const SizedBox(height: 6),
                      Text('Mitigation: ${clause.recommendation}', style: const TextStyle(fontSize: 13, color: Color(0xFF00E676))),
                    ],
                  ),
                );
              },
            ),

            // Missing Clauses List
            ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: result!.missingClauses.length,
              itemBuilder: (context, index) {
                final missing = result!.missingClauses[index];
                return Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF16213E),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.amber.withOpacity(0.4)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        missing.clauseName,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.amber),
                      ),
                      const SizedBox(height: 6),
                      Text(missing.reason, style: const TextStyle(color: Colors.white70, fontSize: 13)),
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(color: const Color(0xFF0F0F1E), borderRadius: BorderRadius.circular(8)),
                        child: Text('Suggested Template: ${missing.recommendedText}', style: const TextStyle(color: Color(0xFF00D2FF), fontSize: 12)),
                      )
                    ],
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
