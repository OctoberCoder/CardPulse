import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/brands_api.dart';
import 'package:cardpulse/api/submissions_api.dart';
import 'package:cardpulse/models/brand.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class SellCardScreen extends ConsumerStatefulWidget {
  const SellCardScreen({super.key});
  @override
  ConsumerState<SellCardScreen> createState() => _SellCardScreenState();
}

class _SellCardScreenState extends ConsumerState<SellCardScreen> {
  final _codeController = TextEditingController();
  Brand? _selectedBrand;
  Denomination? _selectedDenomination;
  Map<String, dynamic>? _quote;
  bool _loading = false;
  List<Brand> _brands = [];

  @override
  void initState() {
    super.initState();
    _loadBrands();
  }

  void _loadBrands() async {
    final client = ref.read(apiClientProvider);
    final api = BrandsApi(client);
    try {
      final brands = await api.getBrands();
      if (mounted) setState(() => _brands = brands);
    } catch (_) {}
  }

  void _getQuote() async {
    if (_selectedBrand == null || _selectedDenomination == null) return;
    setState(() => _loading = true);
    try {
      final client = ref.read(apiClientProvider);
      final api = SubmissionsApi(client);
      final quote = await api.quoteCard(
        _selectedBrand!.id, _selectedDenomination!.id, _codeController.text,
      );
      if (mounted) setState(() => _quote = quote);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _submitCard() async {
    if (_quote == null) return;
    setState(() => _loading = true);
    try {
      final client = ref.read(apiClientProvider);
      final api = SubmissionsApi(client);
      await api.submitCard(
        _selectedBrand!.id, _selectedDenomination!.id, _codeController.text,
        (_quote!['quoted_amount'] as num).toDouble(),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Card submitted for review!')));
        setState(() { _quote = null; _codeController.clear(); });
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sell a Card')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            DropdownButtonFormField<Brand>(
              initialValue: _selectedBrand,
              decoration: const InputDecoration(labelText: 'Brand'),
              items: _brands.map((b) => DropdownMenuItem(value: b, child: Text(b.name))).toList(),
              onChanged: (b) => setState(() { _selectedBrand = b; _selectedDenomination = null; _quote = null; }),
            ),
            if (_selectedBrand != null) ...[
              const SizedBox(height: 16),
              DropdownButtonFormField<Denomination>(
                key: ValueKey(_selectedBrand?.id),
                initialValue: _selectedDenomination,
                decoration: const InputDecoration(labelText: 'Denomination'),
                items: _selectedBrand!.denominations
                    .map((d) => DropdownMenuItem(value: d, child: Text('\$${d.value.toStringAsFixed(0)}')))
                    .toList(),
                onChanged: (d) => setState(() => _selectedDenomination = d),
              ),
            ],
            const SizedBox(height: 16),
            TextField(controller: _codeController, decoration: const InputDecoration(labelText: 'Gift Card Code'), maxLines: 2),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _loading ? null : _getQuote, child: const Text('Get Quote')),
            if (_quote != null) ...[
              const SizedBox(height: 16),
              Card(child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(children: [
                  Text('Rate: ${(_quote!['buy_rate'] as num).toStringAsFixed(2)}'),
                  Text('You receive: \$${(_quote!['quoted_amount'] as num).toStringAsFixed(2)}', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  ElevatedButton(onPressed: _loading ? null : _submitCard, child: const Text('Accept & Submit')),
                ]),
              )),
            ],
            if (_loading) const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator())),
          ],
        ),
      ),
    );
  }
}
