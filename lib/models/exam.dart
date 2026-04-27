class Exam {
  final String id;
  final String userId;
  final String subjectId;
  final String title;
  final DateTime examDate;
  final DateTime createdAt;

  Exam({
    required this.id,
    required this.userId,
    required this.subjectId,
    required this.title,
    required this.examDate,
    required this.createdAt,
  });

  factory Exam.fromMap(Map<String, dynamic> map) {
    return Exam(
      id: map['id'] as String,
      userId: map['user_id'] as String,
      subjectId: map['subject_id'] as String,
      title: map['title'] as String,
      examDate: DateTime.parse(map['exam_date'] as String),
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'user_id': userId,
      'subject_id': subjectId,
      'title': title,
      'exam_date': examDate.toIso8601String().split('T')[0],
    };
  }

  int get daysUntilExam {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final examDay =
        DateTime(examDate.year, examDate.month, examDate.day);
    return examDay.difference(today).inDays;
  }
}