import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('CardPulse'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              ref.read(authProvider.notifier).logout();
              context.go('/login');
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Welcome, ${authState.user?.email ?? ''}', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 24),
            Card(child: ListTile(
              leading: const Icon(Icons.sell, size: 32),
              title: const Text('Sell a Card', style: TextStyle(fontSize: 18)),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/sell'),
            )),
            Card(child: ListTile(
              leading: const Icon(Icons.store, size: 32),
              title: const Text('Browse Brands', style: TextStyle(fontSize: 18)),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/brands'),
            )),
            Card(child: ListTile(
              leading: const Icon(Icons.account_balance_wallet, size: 32),
              title: const Text('Wallet', style: TextStyle(fontSize: 18)),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/wallet'),
            )),
          ],
        ),
      ),
    );
  }
}
