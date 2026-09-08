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
