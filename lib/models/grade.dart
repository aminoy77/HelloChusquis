class Grade {
  final String id;
  final String userId;
  final String subjectId;
  final double grade;
  final DateTime recordedAt;

  Grade({
    required this.id,
    required this.userId,
    required this.subjectId,
    required this.grade,
    required this.recordedAt,
  });

  factory Grade.fromMap(Map<String, dynamic> map) {
    return Grade(
      id: map['id'] as String,
      userId: map['user_id'] as String,
      subjectId: map['subject_id'] as String,
      grade: (map['grade'] as num).toDouble(),
      recordedAt: DateTime.parse(map['recorded_at'] as String),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'user_id': userId,
      'subject_id': subjectId,
      'grade': grade,
      'recorded_at': recordedAt.toIso8601String(),
    };
  }
}