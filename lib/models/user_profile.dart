class UserProfile {
  final String id;
  final String fullName;
  final String learningStyle;
  final int maxStudyHoursPerDay;
  final List<String> preferredStudyDays;
  final String preferredStudyStartTime;
  final String preferredStudyEndTime;
  final bool onboardingComplete;
  final DateTime createdAt;

  UserProfile({
    required this.id,
    required this.fullName,
    required this.learningStyle,
    required this.maxStudyHoursPerDay,
    required this.preferredStudyDays,
    required this.preferredStudyStartTime,
    required this.preferredStudyEndTime,
    required this.onboardingComplete,
    required this.createdAt,
  });

  factory UserProfile.fromMap(Map<String, dynamic> map) {
    return UserProfile(
      id: map['id'] as String,
      fullName: map['full_name'] as String? ?? '',
      learningStyle: map['learning_style'] as String? ?? 'visual',
      maxStudyHoursPerDay: map['max_study_hours_per_day'] as int? ?? 4,
      preferredStudyDays: (map['preferred_study_days'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      preferredStudyStartTime:
          map['preferred_study_start_time'] as String? ?? '08:00',
      preferredStudyEndTime:
          map['preferred_study_end_time'] as String? ?? '22:00',
      onboardingComplete: map['onboarding_complete'] as bool? ?? false,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'full_name': fullName,
      'learning_style': learningStyle,
      'max_study_hours_per_day': maxStudyHoursPerDay,
      'preferred_study_days': preferredStudyDays,
      'preferred_study_start_time': preferredStudyStartTime,
      'preferred_study_end_time': preferredStudyEndTime,
      'onboarding_complete': onboardingComplete,
    };
  }

  UserProfile copyWith({
    String? id,
    String? fullName,
    String? learningStyle,
    int? maxStudyHoursPerDay,
    List<String>? preferredStudyDays,
    String? preferredStudyStartTime,
    String? preferredStudyEndTime,
    bool? onboardingComplete,
    DateTime? createdAt,
  }) {
    return UserProfile(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      learningStyle: learningStyle ?? this.learningStyle,
      maxStudyHoursPerDay: maxStudyHoursPerDay ?? this.maxStudyHoursPerDay,
      preferredStudyDays: preferredStudyDays ?? this.preferredStudyDays,
      preferredStudyStartTime:
          preferredStudyStartTime ?? this.preferredStudyStartTime,
      preferredStudyEndTime: preferredStudyEndTime ?? this.preferredStudyEndTime,
      onboardingComplete: onboardingComplete ?? this.onboardingComplete,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}