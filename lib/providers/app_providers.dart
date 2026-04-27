import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../repositories/user_profile_repository.dart';
import '../repositories/subject_repository.dart';
import '../repositories/grade_repository.dart';
import '../repositories/fixed_block_repository.dart';
import '../repositories/exam_repository.dart';
import '../repositories/task_repository.dart';
import '../repositories/study_session_repository.dart';
import '../models/user_profile.dart';
import '../models/subject.dart';
import '../models/grade.dart';
import '../models/fixed_block.dart';
import '../models/exam.dart';
import '../models/task.dart';
import '../models/study_session.dart';

final supabaseClientProvider = Provider<SupabaseClient>((ref) => Supabase.instance.client);

final currentUserProvider = Provider<User?>((ref) {
  return ref.watch(supabaseClientProvider).auth.currentUser;
});

final userProfileRepositoryProvider = Provider<UserProfileRepository>((ref) {
  return UserProfileRepository();
});

final subjectRepositoryProvider = Provider<SubjectRepository>((ref) {
  return SubjectRepository();
});

final gradeRepositoryProvider = Provider<GradeRepository>((ref) {
  return GradeRepository();
});

final fixedBlockRepositoryProvider = Provider<FixedBlockRepository>((ref) {
  return FixedBlockRepository();
});

final examRepositoryProvider = Provider<ExamRepository>((ref) {
  return ExamRepository();
});

final taskRepositoryProvider = Provider<TaskRepository>((ref) {
  return TaskRepository();
});

final studySessionRepositoryProvider = Provider<StudySessionRepository>((ref) {
  return StudySessionRepository();
});

final userProfileProvider2 = FutureProvider.family<UserProfile?, String>((ref, userId) async {
  final repo = ref.watch(userProfileRepositoryProvider);
  return repo.getProfile(userId);
});

final subjectsProvider2 = FutureProvider.family<List<Subject>, String>((ref, userId) async {
  final repo = ref.watch(subjectRepositoryProvider);
  return repo.getSubjects(userId);
});

final gradesProvider2 = FutureProvider.family<List<Grade>, (String, String)>((ref, params) async {
  final (userId, subjectId) = params;
  final repo = ref.watch(gradeRepositoryProvider);
  return repo.getGrades(userId, subjectId);
});

final latestGradeProvider2 = FutureProvider.family<Grade?, (String, String)>((ref, params) async {
  final (userId, subjectId) = params;
  final repo = ref.watch(gradeRepositoryProvider);
  return repo.getLatestGrade(userId, subjectId);
});

final averageGradeProvider2 = FutureProvider.family<double?, (String, String)>((ref, params) async {
  final (userId, subjectId) = params;
  final repo = ref.watch(gradeRepositoryProvider);
  return repo.getAverageGrade(userId, subjectId);
});

final fixedBlocksProvider2 = FutureProvider.family<List<FixedBlock>, String>((ref, userId) async {
  final repo = ref.watch(fixedBlockRepositoryProvider);
  return repo.getFixedBlocks(userId);
});

final examsProvider2 = FutureProvider.family<List<Exam>, String>((ref, userId) async {
  final repo = ref.watch(examRepositoryProvider);
  return repo.getUpcomingExams(userId);
});

final tasksProvider2 = FutureProvider.family<List<Task>, String>((ref, userId) async {
  final repo = ref.watch(taskRepositoryProvider);
  return repo.getTasks(userId);
});

final studySessionsProvider2 = FutureProvider.family<List<StudySession>, String>((ref, userId) async {
  final repo = ref.watch(studySessionRepositoryProvider);
  return repo.getStudySessions(userId);
});

final studySessionsByDateProvider2 = FutureProvider.family<List<StudySession>, (String, DateTime)>((ref, params) async {
  final (userId, date) = params;
  final repo = ref.watch(studySessionRepositoryProvider);
  return repo.getStudySessionsByDate(userId, date);
});

final studySessionsByExamProvider2 = FutureProvider.family<List<StudySession>, (String, String)>((ref, params) async {
  final (userId, examId) = params;
  final repo = ref.watch(studySessionRepositoryProvider);
  return repo.getStudySessionsByExam(userId, examId);
});