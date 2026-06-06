import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/wallet_api.dart';
import 'package:cardpulse/models/wallet.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class WalletScreen extends ConsumerStatefulWidget {
  const WalletScreen({super.key});
  @override
  ConsumerState<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends ConsumerState<WalletScreen> {
  Wallet? _wallet;
  List<WalletTransaction> _transactions = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    final client = ref.read(apiClientProvider);
    final api = WalletApi(client);
    try {
      final wallet = await api.getWallet();
      final txs = await api.getTransactions();
      if (mounted) setState(() { _wallet = wallet; _transactions = txs; });
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Wallet')),
      body: RefreshIndicator(
        onRefresh: () async => _load(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(children: [
                const Text('Balance', style: TextStyle(color: Colors.grey)),
                Text('\$${_wallet?.balance.toStringAsFixed(2) ?? '0.00'}', style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold)),
              ]),
            )),
            const SizedBox(height: 16),
            const Text('Recent Transactions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            ..._transactions.map((t) => ListTile(
              leading: Icon(t.type == 'credit' ? Icons.arrow_downward : Icons.arrow_upward, color: t.type == 'credit' ? Colors.green : Colors.red),
              title: Text(t.description),
              trailing: Text('\$${t.amount.toStringAsFixed(2)}'),
              subtitle: Text(t.createdAt.substring(0, 10)),
            )),
          ],
        ),
      ),
    );
  }
}
