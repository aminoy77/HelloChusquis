import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../../../models/exam.dart';
import '../../../../models/task.dart';
import '../../../../models/study_session.dart';
import '../../../../models/subject.dart';
import '../../../../providers/app_providers.dart';
import '../../../../repositories/study_session_repository.dart';

class CalendarTab extends ConsumerStatefulWidget {
  const CalendarTab({super.key});

  @override
  ConsumerState<CalendarTab> createState() => _CalendarTabState();
}

class _CalendarTabState extends ConsumerState<CalendarTab> {
  CalendarFormat _calendarFormat = CalendarFormat.month;
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;

  @override
  void initState() {
    super.initState();
    _selectedDay = DateTime.now();
  }

  @override
  Widget build(BuildContext context) {
    final client = Supabase.instance;
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final examsAsync = ref.watch(examsProvider2(user.id));
    final tasksAsync = ref.watch(tasksProvider2(user.id));
    final sessionsAsync = ref.watch(studySessionsProvider2(user.id));
    final subjectsAsync = ref.watch(subjectsProvider2(user.id));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Calendar'),
      ),
      body: Column(
        children: [
          TableCalendar(
            firstDay: DateTime.now().subtract(const Duration(days: 365)),
            lastDay: DateTime.now().add(const Duration(days: 365)),
            focusedDay: _focusedDay,
            calendarFormat: _calendarFormat,
            selectedDayPredicate: (day) {
              return isSameDay(_selectedDay, day);
            },
            onDaySelected: (selectedDay, focusedDay) {
              setState(() {
                _selectedDay = selectedDay;
                _focusedDay = focusedDay;
              });
            },
            onFormatChanged: (format) {
              setState(() {
                _calendarFormat = format;
              });
            },
            eventLoader: (day) {
              final events = <dynamic>[];
              
              examsAsync.whenData((exams) {
                for (final exam in exams) {
                  if (isSameDay(exam.examDate, day)) {
                    events.add(exam);
                  }
                }
              });
              
              tasksAsync.whenData((tasks) {
                for (final task in tasks) {
                  if (isSameDay(task.dueDate, day) && !task.completed) {
                    events.add(task);
                  }
                }
              });
              
              sessionsAsync.whenData((sessions) {
                for (final session in sessions) {
                  if (isSameDay(session.date, day)) {
                    events.add(session);
                  }
                }
              });
              
              return events;
            },
            calendarStyle: CalendarStyle(
              markerDecoration: const BoxDecoration(
                color: Color(0xFFEF4444),
                shape: BoxShape.circle,
              ),
              selectedDecoration: const BoxDecoration(
                color: Color(0xFF1E3A8A),
                shape: BoxShape.circle,
              ),
              todayDecoration: BoxDecoration(
                color: const Color(0xFF1E3A8A).withOpacity(0.5),
                shape: BoxShape.circle,
              ),
            ),
            headerStyle: const HeaderStyle(
              formatButtonVisible: true,
              titleCentered: true,
            ),
          ),
          const Divider(),
          Expanded(
            child: _buildEventList(
              user.id,
              examsAsync,
              tasksAsync,
              sessionsAsync,
              subjectsAsync,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEventList(
    String userId,
    AsyncValue<List<Exam>> examsAsync,
    AsyncValue<List<Task>> tasksAsync,
    AsyncValue<List<StudySession>> sessionsAsync,
    AsyncValue<List<Subject>> subjectsAsync,
  ) {
    if (_selectedDay == null) {
      return const Center(child: Text('Select a day'));
    }

    return examsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (exams) {
        final dayExams = exams.where((e) => isSameDay(e.examDate, _selectedDay!)).toList();
        
        return sessionsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text('Error: $e')),
          data: (sessions) {
            final daySessions = sessions.where((s) => isSameDay(s.date, _selectedDay!)).toList();
            
            return tasksAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
              data: (tasks) {
                final dayTasks = tasks.where((t) => isSameDay(t.dueDate, _selectedDay!) && !t.completed).toList();
                
                if (dayExams.isEmpty && daySessions.isEmpty && dayTasks.isEmpty) {
                  return const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.event_available, size: 48, color: Colors.grey),
                        SizedBox(height: 8),
                        Text('No events for this day', style: TextStyle(color: Colors.grey)),
                      ],
                    ),
                  );
                }
                
                return ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    ...dayExams.map((exam) {
                      return subjectsAsync.when(
                        loading: () => const SizedBox(),
                        error: (_, __) => const SizedBox(),
                        data: (subjects) {
                          final subject = subjects.firstWhere(
                            (s) => s.id == exam.subjectId,
                            orElse: () => Subject(
                              id: '',
                              userId: '',
                              name: 'Unknown',
                              color: '#808080',
                              createdAt: DateTime.now(),
                            ),
                          );
                          return _EventCard(
                            title: exam.title,
                            subtitle: subject.name,
                            time: null,
                            color: Color(int.parse(subject.color.replaceFirst('#', '0xFF'))),
                            type: 'exam',
                          );
                        },
                      );
                    }),
                    ...daySessions.map((session) {
                      return subjectsAsync.when(
                        loading: () => const SizedBox(),
                        error: (_, __) => const SizedBox(),
                        data: (subjects) {
                          final subject = subjects.firstWhere(
                            (s) => s.id == session.subjectId,
                            orElse: () => Subject(
                              id: '',
                              userId: '',
                              name: 'Unknown',
                              color: '#808080',
                              createdAt: DateTime.now(),
                            ),
                          );
                          return _EventCard(
                            title: subject.name,
                            subtitle: 'Study session',
                            time: '${session.startTime} - ${session.endTime}',
                            color: Color(int.parse(subject.color.replaceFirst('#', '0xFF'))),
                            type: 'session',
                            session: session,
                          );
                        },
                      );
                    }),
                    ...dayTasks.map((task) {
                      return subjectsAsync.when(
                        loading: () => const SizedBox(),
                        error: (_, __) => const SizedBox(),
                        data: (subjects) {
                          final subject = subjects.firstWhere(
                            (s) => s.id == task.subjectId,
                            orElse: () => Subject(
                              id: '',
                              userId: '',
                              name: 'Unknown',
                              color: '#808080',
                              createdAt: DateTime.now(),
                            ),
                          );
                          return _EventCard(
                            title: task.title,
                            subtitle: subject.name,
                            time: null,
                            color: const Color(0xFFF97316),
                            type: 'task',
                          );
                        },
                      );
                    }),
                  ],
                );
              },
            );
          },
        );
      },
    );
  }
}

class _EventCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final String? time;
  final Color color;
  final String type;
  final StudySession? session;

  const _EventCard({
    required this.title,
    required this.subtitle,
    this.time,
    required this.color,
    required this.type,
    this.session,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color,
          child: Icon(
            type == 'exam'
                ? Icons.assignment
                : type == 'session'
                    ? Icons.timer
                    : Icons.task,
            color: Colors.white,
            size: 20,
          ),
        ),
        title: Text(title),
        subtitle: Text(subtitle + (time != null ? ' $time' : '')),
        trailing: type == 'session'
            ? Checkbox(
                value: session?.completed ?? false,
                onChanged: (value) async {
                  if (session != null) {
                    final repo = StudySessionRepository();
                    await repo.toggleSessionComplete(session!.id, value ?? false);
                  }
                },
              )
            : null,
      ),
    );
  }
}