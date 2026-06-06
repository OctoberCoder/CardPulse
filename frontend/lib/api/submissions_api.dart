import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/submission.dart';

class SubmissionsApi {
  final ApiClient _client;
  SubmissionsApi(this._client);

  Future<Map<String, dynamic>> quoteCard(int brandId, int denominationId, String cardCode) async {
    final data = await _client.post('/cards/quote', body: {
      'brand_id': brandId, 'denomination_id': denominationId, 'card_code': cardCode,
    });
    return data as Map<String, dynamic>;
  }

  Future<CardSubmission> submitCard(int brandId, int denominationId, String cardCode, double quotedAmount) async {
    final data = await _client.post('/cards/submit', body: {
      'brand_id': brandId, 'denomination_id': denominationId,
      'card_code': cardCode, 'quoted_amount': quotedAmount,
    });
    return CardSubmission.fromJson(data as Map<String, dynamic>);
  }
}
