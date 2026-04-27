import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/task.dart';

class TaskRepository {
  final SupabaseClient _client = Supabase.instance.client;

  Future<List<Task>> getTasks(String userId, {bool includeCompleted = true}) async {
    var query = _client
        .from('tasks')
        .select()
        .eq('user_id', userId);
    
    if (!includeCompleted) {
      query = query.eq('completed', false);
    }
    
    final response = await query.order('due_date', ascending: true);
    return response.map((e) => Task.fromMap(e)).toList();
  }

  Future<Task?> getTask(String taskId) async {
    final response = await _client
        .from('tasks')
        .select()
        .eq('id', taskId)
        .maybeSingle();
    if (response == null) return null;
    return Task.fromMap(response);
  }

  Future<Task> createTask(
    String userId,
    String subjectId,
    String title,
    DateTime dueDate,
  ) async {
    final response = await _client.from('tasks').insert({
      'user_id': userId,
      'subject_id': subjectId,
      'title': title,
      'due_date': dueDate.toIso8601String().split('T')[0],
      'completed': false,
    }).select().single();
    return Task.fromMap(response);
  }

  Future<void> updateTask(String taskId, Map<String, dynamic> data) async {
    await _client.from('tasks').update(data).eq('id', taskId);
  }

  Future<void> toggleTaskComplete(String taskId, bool completed) async {
    await _client.from('tasks').update({'completed': completed}).eq('id', taskId);
  }

  Future<void> deleteTask(String taskId) async {
    await _client.from('tasks').delete().eq('id', taskId);
  }
}