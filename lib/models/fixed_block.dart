class FixedBlock {
  final String id;
  final String userId;
  final String title;
  final String type;
  final String dayOfWeek;
  final String startTime;
  final String endTime;

  FixedBlock({
    required this.id,
    required this.userId,
    required this.title,
    required this.type,
    required this.dayOfWeek,
    required this.startTime,
    required this.endTime,
  });

  factory FixedBlock.fromMap(Map<String, dynamic> map) {
    return FixedBlock(
      id: map['id'] as String,
      userId: map['user_id'] as String,
      title: map['title'] as String,
      type: map['type'] as String,
      dayOfWeek: map['day_of_week'] as String,
      startTime: map['start_time'] as String,
      endTime: map['end_time'] as String,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'user_id': userId,
      'title': title,
      'type': type,
      'day_of_week': dayOfWeek,
      'start_time': startTime,
      'end_time': endTime,
    };
  }

  int get durationMinutes {
    final startParts = startTime.split(':');
    final endParts = endTime.split(':');
    final startMinutes =
        int.parse(startParts[0]) * 60 + int.parse(startParts[1]);
    final endMinutes = int.parse(endParts[0]) * 60 + int.parse(endParts[1]);
    return endMinutes - startMinutes;
  }
}