class User {
  final int id;
  final String email;
  final String phone;
  final String tier;
  final String kycStatus;
  final bool isActive;

  User({required this.id, required this.email, required this.phone,
        required this.tier, required this.kycStatus, required this.isActive});

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'], email: json['email'], phone: json['phone'],
    tier: json['tier'], kycStatus: json['kyc_status'], isActive: json['is_active'],
  );
}
