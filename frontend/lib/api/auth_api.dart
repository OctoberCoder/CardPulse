import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/user.dart';

class AuthApi {
  final ApiClient _client;
  AuthApi(this._client);

  Future<User> register(String email, String password, String phone) async {
    final data = await _client.post('/auth/register', body: {
      'email': email, 'password': password, 'phone': phone,
    });
    return User.fromJson(data as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final data = await _client.post('/auth/login', body: {
      'email': email, 'password': password,
    });
    await _client.saveToken(data['access_token']);
    return data as Map<String, dynamic>;
  }

  Future<User> getMe() async {
    final data = await _client.get('/auth/me');
    return User.fromJson(data as Map<String, dynamic>);
  }
}
