import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/brand.dart';

class BrandsApi {
  final ApiClient _client;
  BrandsApi(this._client);

  Future<List<Brand>> getBrands() async {
    final data = await _client.get('/brands');
    return (data as List).map((j) => Brand.fromJson(j as Map<String, dynamic>)).toList();
  }
}
