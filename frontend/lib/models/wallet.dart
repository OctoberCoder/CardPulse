class Wallet {
  final double balance;
  final String currency;
  final double lockedAmount;

  Wallet({required this.balance, this.currency = 'USD', this.lockedAmount = 0.0});

  factory Wallet.fromJson(Map<String, dynamic> json) => Wallet(
    balance: (json['balance'] as num).toDouble(),
    currency: json['currency'] ?? 'USD',
    lockedAmount: (json['locked_amount'] as num?)?.toDouble() ?? 0.0,
  );
}

class WalletTransaction {
  final int id;
  final String type;
  final double amount;
  final String reference;
  final String description;
  final String createdAt;

  WalletTransaction({required this.id, required this.type, required this.amount,
                     required this.reference, required this.description, required this.createdAt});

  factory WalletTransaction.fromJson(Map<String, dynamic> json) => WalletTransaction(
    id: json['id'], type: json['type'], amount: (json['amount'] as num).toDouble(),
    reference: json['reference'], description: json['description'],
    createdAt: json['created_at'],
  );
}
