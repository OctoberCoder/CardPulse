class Brand {
  final int id;
  final String name;
  final String slug;
  final String icon;
  final bool active;
  final List<Denomination> denominations;

  Brand({required this.id, required this.name, required this.slug,
         this.icon = '', this.active = true, this.denominations = const []});

  factory Brand.fromJson(Map<String, dynamic> json) => Brand(
    id: json['id'], name: json['name'], slug: json['slug'],
    icon: json['icon'] ?? '', active: json['active'] ?? true,
    denominations: (json['denominations'] as List?)?.map((d) => Denomination.fromJson(d)).toList() ?? [],
  );
}

class Denomination {
  final int id;
  final double value;
  final String currency;

  Denomination({required this.id, required this.value, this.currency = 'USD'});

  factory Denomination.fromJson(Map<String, dynamic> json) => Denomination(
    id: json['id'], value: (json['value'] as num).toDouble(), currency: json['currency'] ?? 'USD',
  );
}
