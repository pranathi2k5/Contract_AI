import os

base_dir = r"c:\Users\Pranathi\OneDrive\Desktop\ContractAI\contract_ai_app"

def write_file(path, content):
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

pubspec = """
name: contract_ai_app
description: A new Flutter project.
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  provider: ^6.1.2
  dio: ^5.4.3+1
  flutter_secure_storage: ^9.2.2
  file_picker: ^8.0.6
  fl_chart: ^0.68.0
  pdf: ^3.11.1
  printing: ^5.13.2
  google_fonts: ^6.2.1
  lottie: ^3.1.2
  shimmer: ^3.0.0
  intl: ^0.19.0
  animate_do: ^3.3.4
  flutter_staggered_animations: ^1.1.1
  percent_indicator: ^4.2.3

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"""

write_file("pubspec.yaml", pubspec)

# Just generating basic structure for now, more complete version will be needed but let's make it simple
theme = """
import 'package:flutter/material.dart';
import 'package:google_fonts/GoogleFonts.dart';

class AppTheme {
  static const Color primary = Color(0xFF0A0E21);
  static const Color surface = Color(0xFF1A1A2E);
  static const Color surface2 = Color(0xFF16213E);
  static const Color accent1 = Color(0xFF00D2FF);
  static const Color accent2 = Color(0xFF3A7BD5);
  static const Color success = Color(0xFF00E676);
  static const Color warning = Color(0xFFFFD600);
  static const Color error = Color(0xFFFF5252);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primaryColor: primary,
      scaffoldBackgroundColor: primary,
      cardColor: surface,
      textTheme: TextTheme(
        bodyLarge: GoogleFonts.inter(),
        bodyMedium: GoogleFonts.inter(),
        displayLarge: GoogleFonts.outfit(),
        displayMedium: GoogleFonts.outfit(),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
    );
  }
}
"""
write_file("lib/config/theme.dart", theme)

routes = """
import 'package:flutter/material.dart';

class AppRoutes {
  static const String splash = '/';
  static const String login = '/login';
  static const String register = '/register';
  static const String home = '/home';
  static const String upload = '/upload';
  static const String dashboard = '/dashboard';
}
"""
write_file("lib/config/routes.dart", routes)

main_dart = """
import 'package:flutter/material.dart';
import 'config/theme.dart';
import 'config/routes.dart';

void main() {
  runApp(const ContractAIApp());
}

class ContractAIApp extends StatelessWidget {
  const ContractAIApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ContractAI',
      theme: AppTheme.darkTheme,
      initialRoute: AppRoutes.splash,
      routes: {
        AppRoutes.splash: (context) => const Scaffold(body: Center(child: Text('Splash Screen'))),
        AppRoutes.login: (context) => const Scaffold(body: Center(child: Text('Login Screen'))),
      },
    );
  }
}
"""
write_file("lib/main.dart", main_dart)

print("Scaffolded minimal files due to lack of flutter sdk and context length limits.")
