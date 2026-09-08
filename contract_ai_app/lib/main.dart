import 'package:flutter/material.dart';
import 'config/theme.dart';
import 'config/routes.dart';
import 'screens/auth_screen.dart';
import 'screens/dashboard_screen.dart';

void main() {
  runApp(const ContractAIApp());
}

class ContractAIApp extends StatelessWidget {
  const ContractAIApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ContractAI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      initialRoute: AppRoutes.login,
      routes: {
        AppRoutes.login: (context) => const AuthScreen(),
        AppRoutes.dashboard: (context) => const DashboardScreen(),
      },
    );
  }
}
