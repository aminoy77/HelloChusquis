import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/subject.dart';

class SubjectRepository {
  final SupabaseClient _client = Supabase.instance.client;

  Future<List<Subject>> getSubjects(String userId) async {
    final response = await _client
        .from('subjects')
        .select()
        .eq('user_id', userId)
        .order('created_at', ascending: true);
    return response.map((e) => Subject.fromMap(e)).toList();
  }

  Future<Subject?> getSubject(String subjectId) async {
    final response = await _client
        .from('subjects')
        .select()
        .eq('id', subjectId)
        .maybeSingle();
    if (response == null) return null;
    return Subject.fromMap(response);
  }

  Future<Subject> createSubject(String userId, String name, String color) async {
    final response = await _client.from('subjects').insert({
      'user_id': userId,
      'name': name,
      'color': color,
    }).select().single();
    return Subject.fromMap(response);
  }

  Future<void> updateSubject(String subjectId, String name, String color) async {
    await _client.from('subjects').update({
      'name': name,
      'color': color,
    }).eq('id', subjectId);
  }

  Future<void> deleteSubject(String subjectId) async {
    await _client.from('subjects').delete().eq('id', subjectId);
  }
}