import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'calendar/calendar_tab.dart';
import 'exams_tasks/exams_tasks_tab.dart';
import 'subjects_grades/subjects_grades_tab.dart';
import 'profile/profile_tab.dart';

final selectedTabProvider = StateProvider<int>((ref) => 0);

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedTab = ref.watch(selectedTabProvider);

    return Scaffold(
      body: IndexedStack(
        index: selectedTab,
        children: const [
          CalendarTab(),
          ExamsTasksTab(),
          SubjectsGradesTab(),
          ProfileTab(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: selectedTab,
        onTap: (index) {
          ref.read(selectedTabProvider.notifier).state = index;
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.calendar_month),
            label: 'Calendar',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.assignment),
            label: 'Exams & Tasks',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.school),
            label: 'Subjects',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
      floatingActionButton: selectedTab == 0 || selectedTab == 1
          ? FloatingActionButton(
              onPressed: () => _showAddDialog(context, selectedTab),
              child: const Icon(Icons.add),
            )
          : null,
    );
  }

  void _showAddDialog(BuildContext context, int tab) {
    if (tab == 0) {
      _showQuickAddDialog(context);
    } else if (tab == 1) {
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
                Navigator.pushNamed(context, '/add-exam');
              },
            ),
            ListTile(
              leading: const Icon(Icons.task),
              title: const Text('Add task'),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/add-task');
              },
            ),
          ],
        ),
      );
    }
  }

  void _showQuickAddDialog(BuildContext context) {
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
              Navigator.pushNamed(context, '/add-exam');
            },
          ),
          ListTile(
            leading: const Icon(Icons.task),
            title: const Text('Add task'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/add-task');
            },
          ),
        ],
      ),
    );
  }
}