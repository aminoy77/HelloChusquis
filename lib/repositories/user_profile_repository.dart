import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/user_profile.dart';

class UserProfileRepository {
  final SupabaseClient _client = Supabase.instance.client;

  Future<UserProfile?> getProfile(String userId) async {
    final response = await _client
        .from('users_profile')
        .select()
        .eq('id', userId)
        .maybeSingle();
    if (response == null) return null;
    return UserProfile.fromMap(response);
  }

  Future<void> createProfile(String userId, String fullName) async {
    await _client.from('users_profile').insert({
      'id': userId,
      'full_name': fullName,
      'learning_style': 'visual',
      'max_study_hours_per_day': 4,
      'preferred_study_days': [],
      'preferred_study_start_time': '08:00',
      'preferred_study_end_time': '22:00',
      'onboarding_complete': false,
    });
  }

  Future<void> updateProfile(String userId, Map<String, dynamic> data) async {
    await _client
        .from('users_profile')
        .update(data)
        .eq('id', userId);
  }

  Future<void> setOnboardingComplete(String userId) async {
    await _client
        .from('users_profile')
        .update({'onboarding_complete': true})
        .eq('id', userId);
  }
}