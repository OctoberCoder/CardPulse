# CardPulse Phase 4: Flutter Frontend

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Flutter SPA frontend that connects to the CardPulse FastAPI backend, with auth, card browsing, selling, and wallet features.

**Architecture:** Riverpod for state management, Dio for HTTP client with auth interceptor, GoRouter for navigation. Screens: Auth (login/register), Dashboard, Sell Card, Browse Cards, Wallet.

**Tech Stack:** Flutter 3.44+, Dart 3.x, Riverpod, Dio, GoRouter, flutter_secure_storage

---

### Task 1: Project Setup + Dependencies + API Client

**Files:**
- Modify: `frontend/pubspec.yaml`
- Create: `frontend/lib/api/client.dart`
- Create: `frontend/lib/api/auth_api.dart`
- Create: `frontend/lib/api/brands_api.dart`
- Create: `frontend/lib/api/submissions_api.dart`
- Create: `frontend/lib/api/wallet_api.dart`
- Create: `frontend/lib/models/user.dart`
- Create: `frontend/lib/models/brand.dart`
- Create: `frontend/lib/models/submission.dart`
- Create: `frontend/lib/models/wallet.dart`

**Steps:**

- [ ] **Modify `frontend/pubspec.yaml`** — add dependencies under `dependencies:`:
```yaml
  dio: ^5.4.0
  flutter_riverpod: ^2.5.0
  riverpod_annotation: ^2.3.0
  go_router: ^14.0.0
  flutter_secure_storage: ^9.2.0
  json_annotation: ^4.9.0
```

Run `cd /Users/igeorge/CardPulse/frontend && flutter pub get`

- [ ] **Create `frontend/lib/models/user.dart`**:
```dart
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
```

- [ ] **Create `frontend/lib/models/brand.dart`**:
```dart
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
```

- [ ] **Create `frontend/lib/models/submission.dart`**:
```dart
class CardSubmission {
  final int id;
  final int brandId;
  final int denominationId;
  final double quotedAmount;
  final double? finalAmount;
  final String status;
  final String submittedAt;

  CardSubmission({required this.id, required this.brandId, required this.denominationId,
                  required this.quotedAmount, this.finalAmount, required this.status,
                  required this.submittedAt});

  factory CardSubmission.fromJson(Map<String, dynamic> json) => CardSubmission(
    id: json['id'], brandId: json['brand_id'], denominationId: json['denomination_id'],
    quotedAmount: (json['quoted_amount'] as num).toDouble(),
    finalAmount: (json['final_amount'] as num?)?.toDouble(),
    status: json['status'], submittedAt: json['submitted_at'],
  );
}
```

- [ ] **Create `frontend/lib/models/wallet.dart`**:
```dart
class Wallet {
  final double balance;
  final String currency;
  final double lockedAmount;

  Wallet({required this.balance, this.currency = 'USD', this.lockedAmount = 0.0});

  factory Wallet.fromJson(Map<String, dynamic> json) => Wallet(
    balance: (json['balance'] as num).toDouble(),
    currency: json['currency'] ?? 'USD',
    lockedAmount: (json['locked_amount'] as num?)?.toDouble() ?? 0.0,
  );
}

class WalletTransaction {
  final int id;
  final String type;
  final double amount;
  final String reference;
  final String description;
  final String createdAt;

  WalletTransaction({required this.id, required this.type, required this.amount,
                     required this.reference, required this.description, required this.createdAt});

  factory WalletTransaction.fromJson(Map<String, dynamic> json) => WalletTransaction(
    id: json['id'], type: json['type'], amount: (json['amount'] as num).toDouble(),
    reference: json['reference'], description: json['description'],
    createdAt: json['created_at'],
  );
}
```

- [ ] **Create `frontend/lib/api/client.dart`**:
```dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  static const _baseUrl = 'http://10.0.2.2:8000/api';  // Android emulator -> host
  static const _tokenKey = 'auth_token';

  final Dio _dio;
  final FlutterSecureStorage _storage;

  ApiClient()
      : _dio = Dio(BaseOptions(baseUrl: _baseUrl, connectTimeout: const Duration(seconds: 10))),
        _storage = const FlutterSecureStorage();

  Future<String?> getToken() => _storage.read(key: _tokenKey);
  Future<void> saveToken(String token) => _storage.write(key: _tokenKey, token);
  Future<void> clearToken() => _storage.delete(key: _tokenKey);

  Future<Map<String, dynamic>> get(String path, {Map<String, dynamic>? params}) async {
    final token = await getToken();
    final response = await _dio.get(path,
        queryParameters: params,
        options: Options(headers: _authHeader(token)));
    return response.data;
  }

  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body}) async {
    final token = await getToken();
    final response = await _dio.post(path,
        data: body,
        options: Options(headers: _authHeader(token)));
    return response.data;
  }

  Future<Map<String, dynamic>> patch(String path, {Map<String, dynamic>? body}) async {
    final token = await getToken();
    final response = await _dio.patch(path,
        data: body,
        options: Options(headers: _authHeader(token)));
    return response.data;
  }

  Map<String, String>? _authHeader(String? token) =>
      token != null ? {'Authorization': 'Bearer $token'} : null;

  // Web fallback: use localhost instead of 10.0.2.2
  void setWebBaseUrl() {
    _dio.options.baseUrl = 'http://localhost:8000/api';
  }
}
```

- [ ] **Create `frontend/lib/api/auth_api.dart`**:
```dart
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/user.dart';

class AuthApi {
  final ApiClient _client;

  AuthApi(this._client);

  Future<User> register(String email, String password, String phone) async {
    final data = await _client.post('/auth/register', body: {
      'email': email, 'password': password, 'phone': phone,
    });
    return User.fromJson(data);
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final data = await _client.post('/auth/login', body: {
      'email': email, 'password': password,
    });
    await _client.saveToken(data['access_token']);
    return data;
  }

  Future<User> getMe() async {
    final data = await _client.get('/auth/me');
    return User.fromJson(data);
  }
}
```

- [ ] **Create `frontend/lib/api/brands_api.dart`**:
```dart
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/brand.dart';

class BrandsApi {
  final ApiClient _client;
  BrandsApi(this._client);

  Future<List<Brand>> getBrands() async {
    final data = await _client.get('/brands');
    return (data as List).map((j) => Brand.fromJson(j)).toList();
  }

  Future<List<Denomination>> getDenominations(String slug) async {
    final data = await _client.get('/brands/$slug/denominations');
    return (data as List).map((j) => Denomination.fromJson(j)).toList();
  }
}
```

- [ ] **Create `frontend/lib/api/submissions_api.dart`**:
```dart
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/submission.dart';

class SubmissionsApi {
  final ApiClient _client;
  SubmissionsApi(this._client);

  Future<Map<String, dynamic>> quoteCard(int brandId, int denominationId, String cardCode) async {
    return await _client.post('/cards/quote', body: {
      'brand_id': brandId, 'denomination_id': denominationId, 'card_code': cardCode,
    });
  }

  Future<CardSubmission> submitCard(int brandId, int denominationId, String cardCode, double quotedAmount) async {
    final data = await _client.post('/cards/submit', body: {
      'brand_id': brandId, 'denomination_id': denominationId,
      'card_code': cardCode, 'quoted_amount': quotedAmount,
    });
    return CardSubmission.fromJson(data);
  }
}
```

- [ ] **Create `frontend/lib/api/wallet_api.dart`**:
```dart
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/models/wallet.dart';

class WalletApi {
  final ApiClient _client;
  WalletApi(this._client);

  Future<Wallet> getWallet() async {
    final data = await _client.get('/wallet');
    return Wallet.fromJson(data);
  }

  Future<List<WalletTransaction>> getTransactions() async {
    final data = await _client.get('/wallet/transactions');
    return (data as List).map((j) => WalletTransaction.fromJson(j)).toList();
  }
}
```

- [ ] **Commit**:
```bash
git add frontend/ && git commit -m "feat(flutter): project setup, API client, models"
```

---

### Task 2: Auth Provider + Screens (Login, Register)

**Files:**
- Create: `frontend/lib/providers/auth_provider.dart`
- Create: `frontend/lib/screens/login_screen.dart`
- Create: `frontend/lib/screens/register_screen.dart`
- Create: `frontend/lib/screens/dashboard_screen.dart`
- Create: `frontend/lib/screens/sell_card_screen.dart`
- Create: `frontend/lib/screens/wallet_screen.dart`
- Create: `frontend/lib/screens/brands_screen.dart`
- Modify: `frontend/lib/main.dart`

**Steps:**

- [ ] **Create `frontend/lib/providers/auth_provider.dart`**:
```dart
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
      final data = await _api.login(email, password);
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
```

- [ ] **Create `frontend/lib/screens/login_screen.dart`**:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _login() {
    ref.read(authProvider.notifier).login(
      _emailController.text.trim(),
      _passwordController.text,
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    ref.listen(authProvider, (_, next) {
      if (next.isAuthenticated) context.go('/dashboard');
    });

    return Scaffold(
      appBar: AppBar(title: const Text('CardPulse')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(controller: _emailController, decoration: const InputDecoration(labelText: 'Email')),
            const SizedBox(height: 16),
            TextField(controller: _passwordController, decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
            const SizedBox(height: 24),
            if (authState.isLoading) const CircularProgressIndicator(),
            if (!authState.isLoading) ElevatedButton(onPressed: _login, child: const Text('Login')),
            if (authState.error != null) Text(authState.error!, style: const TextStyle(color: Colors.red)),
            TextButton(onPressed: () => context.go('/register'), child: const Text('Create account')),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Create `frontend/lib/screens/register_screen.dart`**:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _phoneController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  void _register() {
    ref.read(authProvider.notifier).register(
      _emailController.text.trim(),
      _passwordController.text,
      _phoneController.text.trim(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    ref.listen(authProvider, (_, next) {
      if (next.isAuthenticated) context.go('/dashboard');
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Register')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(controller: _emailController, decoration: const InputDecoration(labelText: 'Email')),
            const SizedBox(height: 16),
            TextField(controller: _phoneController, decoration: const InputDecoration(labelText: 'Phone')),
            const SizedBox(height: 16),
            TextField(controller: _passwordController, decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
            const SizedBox(height: 24),
            if (authState.isLoading) const CircularProgressIndicator(),
            if (!authState.isLoading) ElevatedButton(onPressed: _register, child: const Text('Register')),
            if (authState.error != null) Text(authState.error!, style: const TextStyle(color: Colors.red)),
            TextButton(onPressed: () => context.go('/login'), child: const Text('Already have an account? Login')),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Create `frontend/lib/screens/dashboard_screen.dart`**:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('CardPulse'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              ref.read(authProvider.notifier).logout();
              context.go('/login');
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Welcome, ${authState.user?.email ?? ''}', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 24),
            _MenuCard(icon: Icons.sell, title: 'Sell a Card', onTap: () => context.go('/sell')),
            _MenuCard(icon: Icons.store, title: 'Browse Brands', onTap: () => context.go('/brands')),
            _MenuCard(icon: Icons.account_balance_wallet, title: 'Wallet', onTap: () => context.go('/wallet')),
          ],
        ),
      ),
    );
  }
}

class _MenuCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;
  const _MenuCard({required this.icon, required this.title, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon, size: 32),
        title: Text(title, style: const TextStyle(fontSize: 18)),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
```

- [ ] **Create `frontend/lib/screens/sell_card_screen.dart`**:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/client.dart';
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
    final brands = await api.getBrands();
    setState(() => _brands = brands);
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
      setState(() => _quote = quote);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      setState(() => _loading = false);
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
      setState(() => _loading = false);
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
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DropdownButtonFormField<Brand>(
              value: _selectedBrand,
              decoration: const InputDecoration(labelText: 'Brand'),
              items: _brands.map((b) => DropdownMenuItem(value: b, child: Text(b.name))).toList(),
              onChanged: (b) => setState(() { _selectedBrand = b; _selectedDenomination = null; _quote = null; }),
            ),
            if (_selectedBrand != null) ...[
              const SizedBox(height: 16),
              DropdownButtonFormField<Denomination>(
                value: _selectedDenomination,
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
                  Text('Rate: ${(_quote!['buy_rate'] as num).toStringAsFixed(2)}%'),
                  Text('You receive: \$${(_quote!['quoted_amount'] as num).toStringAsFixed(2)}', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  ElevatedButton(onPressed: _loading ? null : _submitCard, child: const Text('Accept & Submit')),
                ]),
              )),
            ],
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Create `frontend/lib/screens/wallet_screen.dart`**:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/api/wallet_api.dart';
import 'package:cardpulse/models/wallet.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class WalletScreen extends ConsumerStatefulWidget {
  const WalletScreen({super.key});
  @override
  ConsumerState<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends ConsumerState<WalletScreen> {
  Wallet? _wallet;
  List<WalletTransaction> _transactions = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    final client = ref.read(apiClientProvider);
    final api = WalletApi(client);
    final wallet = await api.getWallet();
    final txs = await api.getTransactions();
    setState(() { _wallet = wallet; _transactions = txs; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Wallet')),
      body: RefreshIndicator(
        onRefresh: () async => _load(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(children: [
                const Text('Balance', style: TextStyle(color: Colors.grey)),
                Text('\$${_wallet?.balance.toStringAsFixed(2) ?? '0.00'}', style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold)),
              ]),
            )),
            const SizedBox(height: 16),
            const Text('Recent Transactions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            ..._transactions.map((t) => ListTile(
              leading: Icon(t.type == 'credit' ? Icons.arrow_downward : Icons.arrow_upward, color: t.type == 'credit' ? Colors.green : Colors.red),
              title: Text(t.description),
              trailing: Text('\$${t.amount.toStringAsFixed(2)}'),
              subtitle: Text(t.createdAt.substring(0, 10)),
            )),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Create `frontend/lib/screens/brands_screen.dart`**:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/client.dart';
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
    final brands = await api.getBrands();
    setState(() => _brands = brands);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Gift Card Brands')),
      body: RefreshIndicator(
        onRefresh: () async => _load(),
        child: ListView.builder(
          itemCount: _brands.length,
          itemBuilder: (_, i) {
            final brand = _brands[i];
            return Card(child: ListTile(
              leading: const Icon(Icons.card_giftcard, size: 32),
              title: Text(brand.name, style: const TextStyle(fontSize: 18)),
              subtitle: Text('${brand.denominations.length} denominations available'),
            ));
          },
        ),
      ),
    );
  }
}
```

- [ ] **Modify `frontend/lib/main.dart`** — replace with:
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cardpulse/screens/login_screen.dart';
import 'package:cardpulse/screens/register_screen.dart';
import 'package:cardpulse/screens/dashboard_screen.dart';
import 'package:cardpulse/screens/sell_card_screen.dart';
import 'package:cardpulse/screens/wallet_screen.dart';
import 'package:cardpulse/screens/brands_screen.dart';
import 'package:cardpulse/providers/auth_provider.dart';

final _router = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
    GoRoute(path: '/dashboard', builder: (_, __) => const DashboardScreen()),
    GoRoute(path: '/sell', builder: (_, __) => const SellCardScreen()),
    GoRoute(path: '/wallet', builder: (_, __) => const WalletScreen()),
    GoRoute(path: '/brands', builder: (_, __) => const BrandsScreen()),
  ],
);

void main() {
  runApp(const ProviderScope(child: CardPulseApp()));
}

class CardPulseApp extends StatelessWidget {
  const CardPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'CardPulse',
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
        brightness: Brightness.dark,
      ),
      routerConfig: _router,
    );
  }
}
```

- [ ] **Verify build**:
```bash
cd /Users/igeorge/CardPulse/frontend && flutter analyze 2>&1 | tail -10
```

- [ ] **Commit**:
```bash
git add . && git commit -m "feat(flutter): auth, screens, routing, and providers"
```
