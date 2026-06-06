import 'package:cardpulse/api/client.dart';

class AdminApi {
  final ApiClient _client;
  AdminApi(this._client);

  Future<List<Map<String, dynamic>>> getSubmissions({String? statusFilter}) async {
    final params = statusFilter != null ? {'status_filter': statusFilter} : null;
    final data = await _client.get('/admin/cards/submissions', params: params);
    return (data as List).cast<Map<String, dynamic>>();
  }

  Future<void> reviewSubmission(int id, String status, {String notes = '', double? finalAmount}) async {
    await _client.patch('/admin/cards/submissions/$id/review', body: {
      'status': status, 'admin_notes': notes,
      'final_amount': ?finalAmount,
    });
  }
}
