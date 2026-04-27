import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../../models/subject.dart';
import '../../../models/grade.dart';
import '../../../providers/app_providers.dart';
import '../../../repositories/subject_repository.dart';
import '../../../repositories/grade_repository.dart';

class SubjectsGradesTab extends ConsumerWidget {
  const SubjectsGradesTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final subjectsAsync = ref.watch(subjectsProvider2(user.id));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Subjects & Grades'),
      ),
      body: subjectsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (subjects) {
          if (subjects.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.school, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('No subjects yet — add one!', style: TextStyle(color: Colors.grey)),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: subjects.length,
            itemBuilder: (context, index) {
              final subject = subjects[index];
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
                  title: Text(subject.name),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => _SubjectDetailScreen(subject: subject),
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddSubjectDialog(context, ref, user.id),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddSubjectDialog(BuildContext context, WidgetRef ref, String userId) {
    final nameController = TextEditingController();
    String selectedColor = '#1E3A8A';

    final colors = [
      '#EF4444', '#F97316', '#EAB308', '#22C55E', '#14B8A6',
      '#06B6D4', '#3B82F6', '#6366F1', '#8B5CF6', '#EC4899',
    ];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Padding(
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
              Text('Add subject', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 16),
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Subject name'),
              ),
              const SizedBox(height: 16),
              const Text('Select color'),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: colors.map((color) {
                  final isSelected = selectedColor == color;
                  return GestureDetector(
                    onTap: () => setState(() => selectedColor = color),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Color(int.parse(color.replaceFirst('#', '0xFF'))),
                        shape: BoxShape.circle,
                        border: isSelected
                            ? Border.all(color: Colors.white, width: 3)
                            : null,
                      ),
                      child: isSelected
                          ? const Icon(Icons.check, color: Colors.white, size: 20)
                          : null,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () async {
                    if (nameController.text.isEmpty) return;

                    final repo = SubjectRepository();
                    await repo.createSubject(
                      userId,
                      nameController.text,
                      selectedColor,
                    );

                    ref.invalidate(subjectsProvider2(userId));

                    if (context.mounted) Navigator.pop(context);
                  },
                  child: const Text('Add'),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class _SubjectDetailScreen extends ConsumerWidget {
  final Subject subject;

  const _SubjectDetailScreen({required this.subject});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = Supabase.instance.client.auth.currentUser!;
    final averageAsync = ref.watch(averageGradeProvider2((user.id, subject.id)));
    final gradesAsync = ref.watch(gradesProvider2((user.id, subject.id)));

    return Scaffold(
      appBar: AppBar(
        title: Text(subject.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () => _deleteSubject(context, ref, user.id),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            averageAsync.when(
              loading: () => const Card(
                child: ListTile(
                  title: Text('Average grade'),
                  trailing: CircularProgressIndicator(),
                ),
              ),
              error: (e, _) => Card(
                child: ListTile(title: Text('Error: $e')),
              ),
              data: (average) => Card(
                child: ListTile(
                  title: const Text('Average grade'),
                  trailing: Text(
                    average?.toStringAsFixed(1) ?? '-',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text('Grade trend', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            SizedBox(
              height: 200,
              child: gradesAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => Center(child: Text('Error: $e')),
                data: (grades) {
                  if (grades.isEmpty) {
                    return const Center(child: Text('No grades yet'));
                  }

                  final spots = grades.reversed.toList().asMap().entries.map((entry) {
                    return FlSpot(entry.key.toDouble(), entry.value.grade);
                  }).toList();

                  return LineChart(
                    LineChartData(
                      gridData: const FlGridData(show: true),
                      titlesData: const FlTitlesData(show: false),
                      borderData: FlBorderData(show: false),
                      minY: 0,
                      maxY: 10,
                      lineBarsData: [
                        LineChartBarData(
                          spots: spots,
                          isCurved: true,
                          color: Color(int.parse(subject.color.replaceFirst('#', '0xFF'))),
                          barWidth: 3,
                          dotData: const FlDotData(show: true),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            const Text('Grade history', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            gradesAsync.when(
              loading: () => const CircularProgressIndicator(),
              error: (e, _) => Text('Error: $e'),
              data: (grades) {
                if (grades.isEmpty) {
                  return const Text('No grades recorded');
                }

                return ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: grades.length,
                  itemBuilder: (context, index) {
                    final grade = grades[index];
                    return ListTile(
                      title: Text(grade.grade.toStringAsFixed(1)),
                      subtitle: Text(DateFormat('dd/MM/yyyy').format(grade.recordedAt)),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete, size: 20),
                        onPressed: () async {
                          final repo = GradeRepository();
                          await repo.deleteGrade(grade.id);
                          ref.invalidate(gradesProvider2((user.id, subject.id)));
                          ref.invalidate(averageGradeProvider2((user.id, subject.id)));
                        },
                      ),
                    );
                  },
                );
              },
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddGradeDialog(context, ref, user.id),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddGradeDialog(BuildContext context, WidgetRef ref, String userId) {
    final gradeController = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
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
            Text('Add grade', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 16),
            TextField(
              controller: gradeController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Grade (0.0 - 10.0)',
                hintText: 'e.g. 7.5',
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () async {
                  final gradeValue = double.tryParse(gradeController.text);
                  if (gradeValue == null ||
                      gradeValue < 0 ||
                      gradeValue > 10) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Please enter a grade between 0 and 10')),
                    );
                    return;
                  }

                  final repo = GradeRepository();
                  await repo.createGrade(userId, subject.id, gradeValue);

                  ref.invalidate(gradesProvider2((userId, subject.id)));
                  ref.invalidate(averageGradeProvider2((userId, subject.id)));

                  if (context.mounted) {
                    Navigator.pop(context);
                  }
                },
                child: const Text('Add'),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _deleteSubject(BuildContext context, WidgetRef ref, String userId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete subject?'),
        content: const Text('This will also delete all grades for this subject.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      final repo = SubjectRepository();
      await repo.deleteSubject(subject.id);

      ref.invalidate(subjectsProvider2(userId));

      if (context.mounted) {
        Navigator.pop(context);
      }
    }
  }
}