class Task {
  final String id;
  final String userId;
  final String subjectId;
  final String title;
  final DateTime dueDate;
  final bool completed;
  final DateTime createdAt;

  Task({
    required this.id,
    required this.userId,
    required this.subjectId,
    required this.title,
    required this.dueDate,
    required this.completed,
    required this.createdAt,
  });

  factory Task.fromMap(Map<String, dynamic> map) {
    return Task(
      id: map['id'] as String,
      userId: map['user_id'] as String,
      subjectId: map['subject_id'] as String,
      title: map['title'] as String,
      dueDate: DateTime.parse(map['due_date'] as String),
      completed: map['completed'] as bool? ?? false,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'user_id': userId,
      'subject_id': subjectId,
      'title': title,
      'due_date': dueDate.toIso8601String().split('T')[0],
      'completed': completed,
    };
  }

  Task copyWith({
    String? id,
    String? userId,
    String? subjectId,
    String? title,
    DateTime? dueDate,
    bool? completed,
    DateTime? createdAt,
  }) {
    return Task(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      subjectId: subjectId ?? this.subjectId,
      title: title ?? this.title,
      dueDate: dueDate ?? this.dueDate,
      completed: completed ?? this.completed,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}