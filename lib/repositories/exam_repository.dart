import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/exam.dart';

class ExamRepository {
  final SupabaseClient _client = Supabase.instance.client;

  Future<List<Exam>> getExams(String userId) async {
    final response = await _client
        .from('exams')
        .select()
        .eq('user_id', userId)
        .order('exam_date', ascending: true);
    return response.map((e) => Exam.fromMap(e)).toList();
  }

  Future<List<Exam>> getUpcomingExams(String userId) async {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final response = await _client
        .from('exams')
        .select()
        .eq('user_id', userId)
        .gte('exam_date', today.toIso8601String().split('T')[0])
        .order('exam_date', ascending: true);
    return response.map((e) => Exam.fromMap(e)).toList();
  }

  Future<Exam?> getExam(String examId) async {
    final response = await _client
        .from('exams')
        .select()
        .eq('id', examId)
        .maybeSingle();
    if (response == null) return null;
    return Exam.fromMap(response);
  }

  Future<Exam> createExam(
    String userId,
    String subjectId,
    String title,
    DateTime examDate,
  ) async {
    final response = await _client.from('exams').insert({
      'user_id': userId,
      'subject_id': subjectId,
      'title': title,
      'exam_date': examDate.toIso8601String().split('T')[0],
    }).select().single();
    return Exam.fromMap(response);
  }

  Future<void> updateExam(
    String examId,
    String subjectId,
    String title,
    DateTime examDate,
  ) async {
    await _client.from('exams').update({
      'subject_id': subjectId,
      'title': title,
      'exam_date': examDate.toIso8601String().split('T')[0],
    }).eq('id', examId);
  }

  Future<void> deleteExam(String examId) async {
    await _client.from('exams').delete().eq('id', examId);
  }
}