class CardSubmission {
  final int id;
  final int brandId;
  final int denominationId;
  final double quotedAmount;
  final double? finalAmount;
  final String status;
  final String submittedAt;

  CardSubmission({required this.id, required this.brandId, required this.denominationId,
                  required this.quotedAmount, this.finalAmount, required this.status,
                  required this.submittedAt});

  factory CardSubmission.fromJson(Map<String, dynamic> json) => CardSubmission(
    id: json['id'], brandId: json['brand_id'], denominationId: json['denomination_id'],
    quotedAmount: (json['quoted_amount'] as num).toDouble(),
    finalAmount: (json['final_amount'] as num?)?.toDouble(),
    status: json['status'], submittedAt: json['submitted_at'],
  );
}
