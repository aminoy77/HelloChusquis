class Subject {
  final String id;
  final String userId;
  final String name;
  final String color;
  final DateTime createdAt;

  Subject({
    required this.id,
    required this.userId,
    required this.name,
    required this.color,
    required this.createdAt,
  });

  factory Subject.fromMap(Map<String, dynamic> map) {
    return Subject(
      id: map['id'] as String,
      userId: map['user_id'] as String,
      name: map['name'] as String,
      color: map['color'] as String,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'user_id': userId,
      'name': name,
      'color': color,
    };
  }

  Subject copyWith({
    String? id,
    String? userId,
    String? name,
    String? color,
    DateTime? createdAt,
  }) {
    return Subject(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      name: name ?? this.name,
      color: color ?? this.color,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}