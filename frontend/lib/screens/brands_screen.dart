import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/brands_api.dart';
import 'package:cardpulse/models/brand.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class BrandsScreen extends ConsumerStatefulWidget {
  const BrandsScreen({super.key});
  @override
  ConsumerState<BrandsScreen> createState() => _BrandsScreenState();
}

class _BrandsScreenState extends ConsumerState<BrandsScreen> {
  List<Brand> _brands = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    final client = ref.read(apiClientProvider);
    final api = BrandsApi(client);
    try {
      final brands = await api.getBrands();
      if (mounted) setState(() => _brands = brands);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Gift Card Brands')),
      body: RefreshIndicator(
        onRefresh: () async { _load(); },
        child: _brands.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : ListView.builder(
                itemCount: _brands.length,
                itemBuilder: (_, i) {
                  final brand = _brands[i];
                  return Card(child: ListTile(
                    leading: const Icon(Icons.card_giftcard, size: 32),
                    title: Text(brand.name, style: const TextStyle(fontSize: 18)),
                    subtitle: Text('${brand.denominations.length} denominations'),
                  ));
                },
              ),
      ),
    );
  }
}
