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
