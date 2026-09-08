import 'package:flutter/material.dart';
import '../models/contract_model.dart';
import '../services/api_service.dart';

class UploadScreen extends StatefulWidget {
  final Function(ContractAnalysisResult) onAnalysisComplete;

  const UploadScreen({Key? key, required this.onAnalysisComplete}) : super(key: key);

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  String _selectedContractType = 'Employment';
  String _selectedRole = 'Receiver';
  bool _isAnalyzing = false;
  String _selectedFileName = 'Employment_Agreement_2024.pdf';

  Future<void> _startAnalysis() async {
    setState(() => _isAnalyzing = true);
    final result = await ApiService.getAnalysisResult(_selectedContractType, _selectedRole);
    setState(() => _isAnalyzing = false);
    widget.onAnalysisComplete(result);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Upload & Analyze Contract',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            const Text(
              'Supported formats: PDF, DOCX, TXT, OCR Scanned Images',
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
            const SizedBox(height: 24),

            // Dropzone Mock Box
            GestureDetector(
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('File Selected: Employment_Agreement_2024.pdf')),
                );
              },
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
                decoration: BoxDecoration(
                  color: const Color(0xFF16213E).withOpacity(0.6),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFF00D2FF).withOpacity(0.4), width: 1.5),
                ),
                child: Column(
                  children: [
                    const Icon(Icons.cloud_upload_outlined, size: 54, color: Color(0xFF00D2FF)),
                    const SizedBox(height: 12),
                    const Text('Tap to select contract file', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(height: 4),
                    Text(_selectedFileName, style: const TextStyle(color: Color(0xFF00D2FF), fontSize: 13)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Dropdown controls
            const Text('Contract Type', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(color: const Color(0xFF1A1A2E), borderRadius: BorderRadius.circular(12)),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedContractType,
                  isExpanded: true,
                  dropdownColor: const Color(0xFF1A1A2E),
                  items: ['Employment', 'NDA', 'Service', 'Sales', 'Lease']
                      .map((type) => DropdownMenuItem(value: type, child: Text(type)))
                      .toList(),
                  onChanged: (val) => setState(() => _selectedContractType = val!),
                ),
              ),
            ),
            const SizedBox(height: 20),

            const Text('Perspective Role', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: ChoiceChip(
                    label: const Center(child: Text('Receiver (Employee/Client)')),
                    selected: _selectedRole == 'Receiver',
                    selectedColor: const Color(0xFF00D2FF),
                    onSelected: (val) => setState(() => _selectedRole = 'Receiver'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ChoiceChip(
                    label: const Center(child: Text('Sender (Employer/Vendor)')),
                    selected: _selectedRole == 'Sender',
                    selectedColor: const Color(0xFF00D2FF),
                    onSelected: (val) => setState(() => _selectedRole = 'Sender'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),

            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                icon: _isAnalyzing
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                    : const Icon(Icons.auto_awesome),
                label: Text(_isAnalyzing ? 'Analyzing with LegalBERT...' : 'Run Contract Risk Analysis'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00D2FF),
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                onPressed: _isAnalyzing ? null : _startAnalysis,
              ),
            )
          ],
        ),
      ),
    );
  }
}
