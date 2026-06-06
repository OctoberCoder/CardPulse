import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/screens/login_screen.dart';
import 'package:cardpulse/screens/register_screen.dart';
import 'package:cardpulse/screens/dashboard_screen.dart';
import 'package:cardpulse/screens/sell_card_screen.dart';
import 'package:cardpulse/screens/wallet_screen.dart';
import 'package:cardpulse/screens/brands_screen.dart';
import 'package:cardpulse/screens/admin_submissions_screen.dart';

final _router = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
    GoRoute(path: '/register', builder: (_, _) => const RegisterScreen()),
    GoRoute(path: '/dashboard', builder: (_, _) => const DashboardScreen()),
    GoRoute(path: '/sell', builder: (_, _) => const SellCardScreen()),
    GoRoute(path: '/wallet', builder: (_, _) => const WalletScreen()),
    GoRoute(path: '/brands', builder: (_, _) => const BrandsScreen()),
    GoRoute(path: '/admin/submissions', builder: (_, _) => const AdminSubmissionsScreen()),
  ],
);

void main() {
  if (kIsWeb) {
    ApiClient().setWebBaseUrl();
  }
  runApp(const ProviderScope(child: CardPulseApp()));
}

class CardPulseApp extends StatelessWidget {
  const CardPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'CardPulse',
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
        brightness: Brightness.dark,
      ),
      routerConfig: _router,
    );
  }
}
