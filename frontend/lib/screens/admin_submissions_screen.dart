import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/admin_api.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class AdminSubmissionsScreen extends ConsumerStatefulWidget {
  const AdminSubmissionsScreen({super.key});
  @override
  ConsumerState<AdminSubmissionsScreen> createState() => _AdminSubmissionsScreenState();
}

class _AdminSubmissionsScreenState extends ConsumerState<AdminSubmissionsScreen> {
  List<Map<String, dynamic>> _submissions = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    setState(() => _loading = true);
    try {
      final client = ref.read(apiClientProvider);
      final api = AdminApi(client);
      final subs = await api.getSubmissions(statusFilter: 'pending');
      if (mounted) setState(() => _submissions = subs);
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _approve(int id) async {
    final client = ref.read(apiClientProvider);
    final api = AdminApi(client);
    await api.reviewSubmission(id, 'approved', notes: 'Verified');
    _load();
  }

  Future<void> _reject(int id) async {
    final client = ref.read(apiClientProvider);
    final api = AdminApi(client);
    await api.reviewSubmission(id, 'rejected', notes: 'Invalid code');
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Admin - Review Submissions')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _submissions.isEmpty
              ? const Center(child: Text('No pending submissions'))
              : RefreshIndicator(
                  onRefresh: () async => _load(),
                  child: ListView.builder(
                    itemCount: _submissions.length,
                    itemBuilder: (_, i) {
                      final s = _submissions[i];
                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        child: ListTile(
                          title: Text('Submission #${s['id']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                          subtitle: Text('\$${s['quoted_amount']} - ${s['admin_notes'] ?? ''}'),
                          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                            IconButton(
                              icon: const Icon(Icons.check_circle, color: Colors.green),
                              onPressed: () => _approve(s['id'] as int),
                            ),
                            IconButton(
                              icon: const Icon(Icons.cancel, color: Colors.red),
                              onPressed: () => _reject(s['id'] as int),
                            ),
                          ]),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
