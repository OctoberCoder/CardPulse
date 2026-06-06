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
