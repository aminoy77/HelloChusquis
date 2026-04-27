import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:intl/intl.dart';
import '../../../models/exam.dart';
import '../../../models/task.dart';
import '../../../models/subject.dart';
import '../../../providers/app_providers.dart';
import '../../../repositories/exam_repository.dart';
import '../../../repositories/task_repository.dart';
import '../../../repositories/study_session_repository.dart';
import '../../../repositories/user_profile_repository.dart';
import '../../../algorithms/study_session_generator.dart';

class ExamsTasksTab extends ConsumerStatefulWidget {
  const ExamsTasksTab({super.key});

  @override
  ConsumerState<ExamsTasksTab> createState() => _ExamsTasksTabState();
}

class _ExamsTasksTabState extends ConsumerState<ExamsTasksTab> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Exams & Tasks'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Exams'),
            Tab(text: 'Tasks'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _ExamsList(),
          _TasksList(),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddDialog(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.assignment),
            title: const Text('Add exam'),
            onTap: () {
              Navigator.pop(context);
              _showAddExamDialog(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.task),
            title: const Text('Add task'),
            onTap: () {
              Navigator.pop(context);
              _showAddTaskDialog(context);
            },
          ),
        ],
      ),
    );
  }

  void _showAddExamDialog(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;

    final titleController = TextEditingController();
    String? selectedSubjectId;
    DateTime selectedDate = DateTime.now().add(const Duration(days: 7));

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          final subjectsAsync = ref.watch(subjectsProvider2(user.id));
          
          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).viewInsets.bottom,
              left: 16,
              right: 16,
              top: 16,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Add exam', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 16),
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(labelText: 'Title'),
                ),
                const SizedBox(height: 16),
                subjectsAsync.when(
                  loading: () => const CircularProgressIndicator(),
                  error: (e, _) => Text('Error: $e'),
                  data: (subjects) => DropdownButtonFormField<String>(
                    value: selectedSubjectId,
                    decoration: const InputDecoration(labelText: 'Subject'),
                    items: subjects.map((s) => DropdownMenuItem(
                      value: s.id,
                      child: Text(s.name),
                    )).toList(),
                    onChanged: (value) => setState(() => selectedSubjectId = value),
                  ),
                ),
                const SizedBox(height: 16),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Exam date'),
                  trailing: Text(
                    DateFormat('dd/MM/yyyy').format(selectedDate),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  onTap: () async {
                    final date = await showDatePicker(
                      context: context,
                      initialDate: selectedDate,
                      firstDate: DateTime.now(),
                      lastDate: DateTime.now().add(const Duration(days: 365)),
                    );
                    if (date != null) {
                      setState(() => selectedDate = date);
                    }
                  },
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () async {
                      if (titleController.text.isEmpty || selectedSubjectId == null) return;
                      
                      final repo = ExamRepository();
                      await repo.createExam(
                        user.id,
                        selectedSubjectId!,
                        titleController.text,
                        selectedDate,
                      );
                      
                      final profileRepo = UserProfileRepository();
                      final profile = await profileRepo.getProfile(user.id);
                      final fixedBlocks = await ref.read(fixedBlocksProvider2(user.id).future);
                      final sessions = await ref.read(studySessionsProvider2(user.id).future);

                      if (profile != null) {
                        final newExam = await repo.getExams(user.id).then(
                          (exams) => exams.last,
                        );
                        
                        final studySessions = StudySessionGenerator.generateStudySessions(
                          exam: newExam,
                          latestGrade: null,
                          userProfile: profile,
                          fixedBlocks: fixedBlocks,
                          existingStudySessions: sessions,
                        );
                        
                        final sessionRepo = StudySessionRepository();
                        await sessionRepo.createStudySessions(studySessions);
                      }
                      
                      ref.invalidate(examsProvider2(user.id));
                      ref.invalidate(studySessionsProvider2(user.id));
                      
                      if (context.mounted) Navigator.pop(context);
                    },
                    child: const Text('Add exam'),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showAddTaskDialog(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;

    final titleController = TextEditingController();
    String? selectedSubjectId;
    DateTime selectedDate = DateTime.now().add(const Duration(days: 3));

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          final subjectsAsync = ref.watch(subjectsProvider2(user.id));
          
          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).viewInsets.bottom,
              left: 16,
              right: 16,
              top: 16,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Add task', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 16),
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(labelText: 'Title'),
                ),
                const SizedBox(height: 16),
                subjectsAsync.when(
                  loading: () => const CircularProgressIndicator(),
                  error: (e, _) => Text('Error: $e'),
                  data: (subjects) => DropdownButtonFormField<String>(
                    value: selectedSubjectId,
                    decoration: const InputDecoration(labelText: 'Subject'),
                    items: subjects.map((s) => DropdownMenuItem(
                      value: s.id,
                      child: Text(s.name),
                    )).toList(),
                    onChanged: (value) => setState(() => selectedSubjectId = value),
                  ),
                ),
                const SizedBox(height: 16),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Due date'),
                  trailing: Text(
                    DateFormat('dd/MM/yyyy').format(selectedDate),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  onTap: () async {
                    final date = await showDatePicker(
                      context: context,
                      initialDate: selectedDate,
                      firstDate: DateTime.now(),
                      lastDate: DateTime.now().add(const Duration(days: 365)),
                    );
                    if (date != null) {
                      setState(() => selectedDate = date);
                    }
                  },
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () async {
                      if (titleController.text.isEmpty || selectedSubjectId == null) return;
                      
                      final repo = TaskRepository();
                      await repo.createTask(
                        user.id,
                        selectedSubjectId!,
                        titleController.text,
                        selectedDate,
                      );
                      
                      ref.invalidate(tasksProvider2(user.id));
                      
                      if (context.mounted) Navigator.pop(context);
                    },
                    child: const Text('Add task'),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ExamsList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final examsAsync = ref.watch(examsProvider2(user.id));
    final subjectsAsync = ref.watch(subjectsProvider2(user.id));

    return examsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (exams) {
        if (exams.isEmpty) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.assignment, size: 64, color: Colors.grey),
                SizedBox(height: 16),
                Text('No exams yet — add one!', style: TextStyle(color: Colors.grey)),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: exams.length,
          itemBuilder: (context, index) {
            final exam = exams[index];
            
            return subjectsAsync.when(
              loading: () => const Card(child: ListTile(title: Text('...'))),
              error: (e, _) => Card(child: ListTile(title: Text('Error: $e'))),
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
                
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: Color(int.parse(subject.color.replaceFirst('#', '0xFF'))),
                      child: Text(
                        subject.name[0],
                        style: const TextStyle(color: Colors.white),
                      ),
                    ),
                    title: Text(exam.title),
                    subtitle: Text(
                      '${DateFormat('dd/MM/yyyy').format(exam.examDate)} - ${exam.daysUntilExam} days',
                    ),
                    trailing: _ExamBadge(examId: exam.id, userId: user.id),
                    onTap: () => _showExamDetail(context, ref, exam, subject),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  void _showExamDetail(BuildContext context, WidgetRef ref, Exam exam, Subject subject) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        expand: false,
        builder: (context, scrollController) {
          final user = Supabase.instance.client.auth.currentUser!;
          final sessionsAsync = ref.watch(studySessionsByExamProvider2((user.id, exam.id)));
          
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(exam.title, style: Theme.of(context).textTheme.headlineSmall),
                Text(subject.name, style: TextStyle(color: Colors.grey)),
                const SizedBox(height: 16),
                Text('Study sessions:'),
                const SizedBox(height: 8),
                Expanded(
                  child: sessionsAsync.when(
                    loading: () => const CircularProgressIndicator(),
                    error: (e, _) => Text('Error: $e'),
                    data: (sessions) {
                      if (sessions.isEmpty) {
                        return const Center(child: Text('No study sessions scheduled'));
                      }
                      
                      return ListView.builder(
                        controller: scrollController,
                        itemCount: sessions.length,
                        itemBuilder: (context, index) {
                          final session = sessions[index];
                          return ListTile(
                            title: Text('${session.date.day}/${session.date.month}'),
                            subtitle: Text('${session.startTime} - ${session.endTime}'),
                            trailing: Text('${session.durationMinutes} min'),
                          );
                        },
                      );
                    },
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton(
                      onPressed: () async {
                        final repo = ExamRepository();
                        await repo.deleteExam(exam.id);
                        ref.invalidate(examsProvider2(user.id));
                        
                        if (context.mounted) Navigator.pop(context);
                      },
                      child: const Text('Delete exam', style: TextStyle(color: Colors.red)),
                    ),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Close'),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ExamBadge extends ConsumerWidget {
  final String examId;
  final String userId;

  const _ExamBadge({required this.examId, required this.userId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessionsAsync = ref.watch(studySessionsByExamProvider2((userId, examId)));
    
    return sessionsAsync.when(
      loading: () => const SizedBox(),
      error: (_, __) => const SizedBox(),
      data: (sessions) {
        return Chip(
          label: Text('${sessions.length}'),
          backgroundColor: const Color(0xFF1E3A8A),
        );
      },
    );
  }
}

class _TasksList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final tasksAsync = ref.watch(tasksProvider2(user.id));
    final subjectsAsync = ref.watch(subjectsProvider2(user.id));

    return tasksAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (tasks) {
        final upcoming = tasks.where((t) => !t.completed).toList();
        final completed = tasks.where((t) => t.completed).toList();

        if (tasks.isEmpty) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.task, size: 64, color: Colors.grey),
                SizedBox(height: 16),
                Text('No tasks yet — add one!', style: TextStyle(color: Colors.grey)),
              ],
            ),
          );
        }

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (upcoming.isNotEmpty) ...[
              const Text('Upcoming', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ...upcoming.map((task) => subjectsAsync.when(
                loading: () => const Card(child: ListTile()),
                error: (e, _) => Card(child: ListTile(title: Text('Error: $e'))),
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
                  
                  return Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: Color(int.parse(subject.color.replaceFirst('#', '0xFF'))),
                        child: Text(subject.name[0], style: const TextStyle(color: Colors.white)),
                      ),
                      title: Text(task.title),
                      subtitle: Text(DateFormat('dd/MM/yyyy').format(task.dueDate)),
                      trailing: Checkbox(
                        value: task.completed,
                        onChanged: (value) async {
                          final repo = TaskRepository();
                          await repo.toggleTaskComplete(task.id, value ?? false);
                          ref.invalidate(tasksProvider2(user.id));
                        },
                      ),
                    ),
                  );
                },
              )),
            ],
            if (completed.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text('Completed', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey)),
              const SizedBox(height: 8),
              ...completed.map((task) => subjectsAsync.when(
                loading: () => const Card(child: ListTile()),
                error: (e, _) => Card(child: ListTile(title: Text('Error: $e'))),
                data: (subjects) {
                  final subject = subjects.firstWhere(
                    (s) => s.id == task.subjectId,
                    orElse: () => Subject(id: '', userId: '', name: 'Unknown', color: '#808080', createdAt: DateTime.now()),
                  );
                  
                  return Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    color: const Color(0xFF2A2A2A),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: Colors.grey,
                        child: Text(subject.name[0], style: const TextStyle(color: Colors.white)),
                      ),
                      title: Text(task.title, style: const TextStyle(decoration: TextDecoration.lineThrough)),
                      subtitle: Text(DateFormat('dd/MM/yyyy').format(task.dueDate)),
                      trailing: Checkbox(
                        value: task.completed,
                        onChanged: (value) async {
                          final repo = TaskRepository();
                          await repo.toggleTaskComplete(task.id, value ?? false);
                          ref.invalidate(tasksProvider2(user.id));
                        },
                      ),
                    ),
                  );
                },
              )),
            ],
          ],
        );
      },
    );
  }
}