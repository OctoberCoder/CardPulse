import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/api/auth_api.dart';
import 'package:cardpulse/models/user.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final authApiProvider = Provider<AuthApi>((ref) => AuthApi(ref.read(apiClientProvider)));

class AuthState {
  final User? user;
  final bool isLoading;
  final String? error;

  const AuthState({this.user, this.isLoading = false, this.error});

  bool get isAuthenticated => user != null;
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthApi _api;
  final ApiClient _client;

  AuthNotifier(this._api, this._client) : super(const AuthState());

  Future<void> tryAutoLogin() async {
    final token = await _client.getToken();
    if (token != null) {
      try {
        final user = await _api.getMe();
        state = AuthState(user: user);
      } catch (_) {
        await _client.clearToken();
      }
    }
  }

  Future<void> login(String email, String password) async {
    state = const AuthState(isLoading: true);
    try {
      await _api.login(email, password);
      final user = await _api.getMe();
      state = AuthState(user: user);
    } catch (e) {
      state = AuthState(error: e.toString());
    }
  }

  Future<void> register(String email, String password, String phone) async {
    state = const AuthState(isLoading: true);
    try {
      final user = await _api.register(email, password, phone);
      state = AuthState(user: user);
    } catch (e) {
      state = AuthState(error: e.toString());
    }
  }

  Future<void> logout() async {
    await _client.clearToken();
    state = const AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(authApiProvider), ref.read(apiClientProvider));
});
