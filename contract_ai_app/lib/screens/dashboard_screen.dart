import 'package:flutter/material.dart';
import '../models/contract_model.dart';
import '../services/api_service.dart';
import 'upload_screen.dart';
import 'risk_details_screen.dart';
import 'laws_screen.dart';
import 'chatbot_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;
  ContractAnalysisResult? _result;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadInitialAnalysis();
  }

  Future<void> _loadInitialAnalysis() async {
    final result = await ApiService.getAnalysisResult('Employment', 'Receiver');
    setState(() {
      _result = result;
      _isLoading = false;
    });
  }

  void _onAnalysisUpdated(ContractAnalysisResult result) {
    setState(() {
      _result = result;
      _currentIndex = 0; // Switch back to dashboard view
    });
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> pages = [
      _buildDashboardHome(),
      UploadScreen(onAnalysisComplete: _onAnalysisUpdated),
      RiskDetailsScreen(result: _result),
      LawsScreen(laws: _result?.applicableLaws ?? []),
      const ChatbotScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: const [
            Icon(Icons.scale_rounded, color: Color(0xFF00D2FF)),
            SizedBox(width: 8),
            Text('ContractAI', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('ContractAI v2.0 Enterprise Connected to Spring Boot & FastAPI')),
              );
            },
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00D2FF)))
          : IndexedStack(index: _currentIndex, children: pages),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        selectedItemColor: const Color(0xFF00D2FF),
        unselectedItemColor: Colors.white54,
        backgroundColor: const Color(0xFF16213E),
        type: BottomNavigationBarType.fixed,
        onTap: (index) => setState(() => _currentIndex = index),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard_rounded), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.cloud_upload_rounded), label: 'Upload'),
          BottomNavigationBarItem(icon: Icon(Icons.warning_amber_rounded), label: 'Risks'),
          BottomNavigationBarItem(icon: Icon(Icons.gavel_rounded), label: 'Laws'),
          BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), label: 'Chatbot'),
        ],
      ),
    );
  }

  Widget _buildDashboardHome() {
    if (_result == null) return const SizedBox();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Score Card
          Container(
            padding: const EdgeInsets.all(24.0),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1A2E),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white10),
            ),
            child: Column(
              children: [
                const Text('Overall Risk Score', style: TextStyle(color: Colors.white70, fontSize: 16)),
                const SizedBox(height: 12),
                Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 140,
                      height: 140,
                      child: CircularProgressIndicator(
                        value: _result!.overallRiskScore / 100,
                        strokeWidth: 14,
                        backgroundColor: Colors.white10,
                        color: _result!.overallRiskScore > 70 ? Colors.redAccent : Colors.orangeAccent,
                      ),
                    ),
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${_result!.overallRiskScore}',
                          style: const TextStyle(fontSize: 38, fontWeight: FontWeight.bold, color: Colors.white),
                        ),
                        Text(
                          '/ 100',
                          style: const TextStyle(color: Colors.white54, fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Chip(
                  label: Text(
                    '${_result!.riskLevel} RISK',
                    style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  backgroundColor: _result!.riskLevel == 'HIGH' ? Colors.redAccent.withOpacity(0.3) : Colors.orange.withOpacity(0.3),
                  side: BorderSide(color: _result!.riskLevel == 'HIGH' ? Colors.redAccent : Colors.orange),
                ),
                const SizedBox(height: 12),
                Text(
                  _result!.summary,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Quick Metric Row
          Row(
            children: [
              Expanded(
                child: _buildMetricTile(
                  icon: Icons.list_alt,
                  color: Colors.cyan,
                  title: 'Risky Clauses',
                  value: '${_result!.riskClauses.length}',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildMetricTile(
                  icon: Icons.warning_rounded,
                  color: Colors.amber,
                  title: 'Missing Clauses',
                  value: '${_result!.missingClauses.length}',
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Executive Summary Box
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF16213E),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    Icon(Icons.shield_outlined, color: Color(0xFF00D2FF)),
                    SizedBox(width: 8),
                    Text('Legal Assessment Summary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  ],
                ),
                const SizedBox(height: 10),
                const Text(
                  'Post-employment non-compete restrains trade under Section 27 of the Indian Contract Act 1872. Uncapped indemnity clause poses extreme financial risk to Receiver.',
                  style: TextStyle(color: Colors.white70, height: 1.4),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildMetricTile({required IconData icon, required Color color, required String title, required String value}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A2E),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: color.withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              Text(title, style: const TextStyle(fontSize: 12, color: Colors.white54)),
            ],
          )
        ],
      ),
    );
  }
}
