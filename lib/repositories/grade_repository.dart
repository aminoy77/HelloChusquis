import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/grade.dart';

class GradeRepository {
  final SupabaseClient _client = Supabase.instance.client;

  Future<List<Grade>> getGrades(String userId, String subjectId) async {
    final response = await _client
        .from('grades')
        .select()
        .eq('user_id', userId)
        .eq('subject_id', subjectId)
        .order('recorded_at', ascending: false);
    return response.map((e) => Grade.fromMap(e)).toList();
  }

  Future<Grade?> getLatestGrade(String userId, String subjectId) async {
    final response = await _client
        .from('grades')
        .select()
        .eq('user_id', userId)
        .eq('subject_id', subjectId)
        .order('recorded_at', ascending: false)
        .limit(1)
        .maybeSingle();
    if (response == null) return null;
    return Grade.fromMap(response);
  }

  Future<double?> getAverageGrade(String userId, String subjectId) async {
    final response = await _client
        .from('grades')
        .select('grade')
        .eq('user_id', userId)
        .eq('subject_id', subjectId);
    if (response.isEmpty) return null;
    final sum = response.fold<double>(0, (sum, e) => sum + (e['grade'] as num).toDouble());
    return sum / response.length;
  }

  Future<Grade> createGrade(String userId, String subjectId, double grade) async {
    final response = await _client.from('grades').insert({
      'user_id': userId,
      'subject_id': subjectId,
      'grade': grade,
    }).select().single();
    return Grade.fromMap(response);
  }

  Future<void> deleteGrade(String gradeId) async {
    await _client.from('grades').delete().eq('id', gradeId);
  }
}