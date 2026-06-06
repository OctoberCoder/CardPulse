import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/wallet.dart';

class WalletApi {
  final ApiClient _client;
  WalletApi(this._client);

  Future<Wallet> getWallet() async {
    final data = await _client.get('/wallet');
    return Wallet.fromJson(data as Map<String, dynamic>);
  }

  Future<List<WalletTransaction>> getTransactions() async {
    final data = await _client.get('/wallet/transactions');
    return (data as List).map((j) => WalletTransaction.fromJson(j as Map<String, dynamic>)).toList();
  }
}
