import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  static const _baseUrl = 'http://10.0.2.2:8000/api';

  final Dio _dio;
  final FlutterSecureStorage _storage;

  ApiClient()
      : _dio = Dio(BaseOptions(baseUrl: _baseUrl, connectTimeout: const Duration(seconds: 10))),
        _storage = const FlutterSecureStorage();

  Future<String?> getToken() => _storage.read(key: 'auth_token');
  Future<void> saveToken(String token) => _storage.write(key: 'auth_token', value: token);
  Future<void> clearToken() => _storage.delete(key: 'auth_token');

  Future<dynamic> get(String path, {Map<String, dynamic>? params}) async {
    final token = await getToken();
    final response = await _dio.get(path,
        queryParameters: params,
        options: Options(headers: _authHeader(token)));
    return response.data;
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    final token = await getToken();
    final response = await _dio.post(path,
        data: body,
        options: Options(headers: _authHeader(token)));
    return response.data;
  }

  Future<dynamic> patch(String path, {Map<String, dynamic>? body}) async {
    final token = await getToken();
    final response = await _dio.patch(path,
        data: body,
        options: Options(headers: _authHeader(token)));
    return response.data;
  }

  void setWebBaseUrl() {
    _dio.options.baseUrl = 'http://localhost:8000/api';
  }

  Map<String, String>? _authHeader(String? token) =>
      token != null ? {'Authorization': 'Bearer $token'} : null;
}
