import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:uuid/uuid.dart';
import '../../repositories/user_profile_repository.dart';
import '../../repositories/fixed_block_repository.dart';
import '../home/home_screen.dart';

class OnboardingProvider extends StateNotifier<OnboardingState> {
  OnboardingProvider() : super(OnboardingState());

  void setLearningStyle(String style) {
    state = state.copyWith(learningStyle: style);
  }

  void setMaxStudyHours(int hours) {
    state = state.copyWith(maxStudyHoursPerDay: hours);
  }

  void toggleStudyDay(String day) {
    final days = List<String>.from(state.preferredStudyDays);
    if (days.contains(day)) {
      days.remove(day);
    } else {
      days.add(day);
    }
    state = state.copyWith(preferredStudyDays: days);
  }

  void setStudyStartTime(TimeOfDay time) {
    state = state.copyWith(
      preferredStudyStartTime: '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}',
    );
  }

  void setStudyEndTime(TimeOfDay time) {
    state = state.copyWith(
      preferredStudyEndTime: '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}',
    );
  }

  void addFixedBlock(FixedBlockData block) {
    state = state.copyWith(
      fixedBlocks: [...state.fixedBlocks, block],
    );
  }

  void removeFixedBlock(int index) {
    final blocks = List<FixedBlockData>.from(state.fixedBlocks);
    blocks.removeAt(index);
    state = state.copyWith(fixedBlocks: blocks);
  }
}

class OnboardingState {
  final String learningStyle;
  final int maxStudyHoursPerDay;
  final List<String> preferredStudyDays;
  final String preferredStudyStartTime;
  final String preferredStudyEndTime;
  final List<FixedBlockData> fixedBlocks;

  OnboardingState({
    this.learningStyle = 'visual',
    this.maxStudyHoursPerDay = 4,
    this.preferredStudyDays = const [],
    this.preferredStudyStartTime = '08:00',
    this.preferredStudyEndTime = '22:00',
    this.fixedBlocks = const [],
  });

  OnboardingState copyWith({
    String? learningStyle,
    int? maxStudyHoursPerDay,
    List<String>? preferredStudyDays,
    String? preferredStudyStartTime,
    String? preferredStudyEndTime,
    List<FixedBlockData>? fixedBlocks,
  }) {
    return OnboardingState(
      learningStyle: learningStyle ?? this.learningStyle,
      maxStudyHoursPerDay: maxStudyHoursPerDay ?? this.maxStudyHoursPerDay,
      preferredStudyDays: preferredStudyDays ?? this.preferredStudyDays,
      preferredStudyStartTime: preferredStudyStartTime ?? this.preferredStudyStartTime,
      preferredStudyEndTime: preferredStudyEndTime ?? this.preferredStudyEndTime,
      fixedBlocks: fixedBlocks ?? this.fixedBlocks,
    );
  }
}

class FixedBlockData {
  final String title;
  final String type;
  final String dayOfWeek;
  final String startTime;
  final String endTime;

  FixedBlockData({
    required this.title,
    required this.type,
    required this.dayOfWeek,
    required this.startTime,
    required this.endTime,
  });
}

final onboardingProvider = StateNotifierProvider<OnboardingProvider, OnboardingState>((ref) {
  return OnboardingProvider();
});

class OnboardingFlow extends ConsumerStatefulWidget {
  const OnboardingFlow({super.key});

  @override
  ConsumerState<OnboardingFlow> createState() => _OnboardingFlowState();
}

class _OnboardingFlowState extends ConsumerState<OnboardingFlow> {
  final PageController _pageController = PageController();
  int _currentPage = 0;
  bool _loading = false;

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _nextPage() {
    if (_currentPage < 4) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
      setState(() {
        _currentPage++;
      });
    } else {
      _completeOnboarding();
    }
  }

  Future<void> _completeOnboarding() async {
    setState(() {
      _loading = true;
    });

    try {
      final user = Supabase.instance.client.auth.currentUser;
      if (user == null) return;

      final repo = UserProfileRepository();
      final state = ref.read(onboardingProvider);

      await repo.updateProfile(user.id, {
        'learning_style': state.learningStyle,
        'max_study_hours_per_day': state.maxStudyHoursPerDay,
        'preferred_study_days': state.preferredStudyDays,
        'preferred_study_start_time': state.preferredStudyStartTime,
        'preferred_study_end_time': state.preferredStudyEndTime,
      });

      await repo.setOnboardingComplete(user.id);

      final blockRepo = FixedBlockRepository();
      for (final block in state.fixedBlocks) {
        await blockRepo.createFixedBlock(
          user.id,
          block.title,
          block.type,
          block.dayOfWeek,
          block.startTime,
          block.endTime,
        );
      }

      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/home');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: List.generate(5, (index) {
                  return Expanded(
                    child: Container(
                      height: 4,
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      decoration: BoxDecoration(
                        color: index <= _currentPage
                            ? const Color(0xFF1E3A8A)
                            : Colors.grey,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
            ),
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  _Step1LearningStyle(),
                  _Step2StudyHours(),
                  _Step3StudyDays(),
                  _Step4StudyWindow(),
                  _Step5FixedSchedule(onNext: _nextPage),
                ],
              ),
            ),
            if (_currentPage < 4)
              Padding(
                padding: const EdgeInsets.all(24),
                child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _loading ? null : _nextPage,
                    child: _loading
                        ? const CircularProgressIndicator()
                        : const Text('Continue'),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Step1LearningStyle extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(onboardingProvider);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'What is your learning style?',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'This will help us personalize your study sessions.',
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 32),
          _OptionCard(
            title: 'Visual',
            description: 'I learn with diagrams and color',
            icon: Icons.palette,
            selected: state.learningStyle == 'visual',
            onTap: () => ref.read(onboardingProvider.notifier).setLearningStyle('visual'),
          ),
          const SizedBox(height: 16),
          _OptionCard(
            title: 'Auditory',
            description: 'I prefer listening and explaining',
            icon: Icons.headphones,
            selected: state.learningStyle == 'auditory',
            onTap: () => ref.read(onboardingProvider.notifier).setLearningStyle('auditory'),
          ),
          const SizedBox(height: 16),
          _OptionCard(
            title: 'Reader',
            description: 'I learn by reading and writing',
            icon: Icons.book,
            selected: state.learningStyle == 'reader',
            onTap: () => ref.read(onboardingProvider.notifier).setLearningStyle('reader'),
          ),
        ],
      ),
    );
  }
}

class _Step2StudyHours extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(onboardingProvider);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'How many hours can you study per day maximum?',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 32),
          Center(
            child: Text(
              '${state.maxStudyHoursPerDay} hours',
              style: const TextStyle(
                fontSize: 48,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1E3A8A),
              ),
            ),
          ),
          const SizedBox(height: 32),
          Slider(
            value: state.maxStudyHoursPerDay.toDouble(),
            min: 1,
            max: 8,
            divisions: 7,
            activeColor: const Color(0xFF1E3A8A),
            onChanged: (value) {
              ref.read(onboardingProvider.notifier).setMaxStudyHours(value.toInt());
            },
          ),
          const SizedBox(height: 16),
          const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('1 hour', style: TextStyle(color: Colors.grey)),
              Text('8 hours', style: TextStyle(color: Colors.grey)),
            ],
          ),
        ],
      ),
    );
  }
}

class _Step3StudyDays extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(onboardingProvider);
    final days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Which days do you prefer to study?',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 32),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: days.map((day) {
              final selected = state.preferredStudyDays.contains(day);
              return FilterChip(
                label: Text(day[0].toUpperCase() + day.substring(1)),
                selected: selected,
                onSelected: (_) {
                  ref.read(onboardingProvider.notifier).toggleStudyDay(day);
                },
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class _Step4StudyWindow extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(onboardingProvider);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'What is your available study window each day?',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 32),
          ListTile(
            title: const Text('Start time', style: TextStyle(color: Colors.grey)),
            trailing: TextButton(
              onPressed: () async {
                final time = await showTimePicker(
                  context: context,
                  initialTime: TimeOfDay(
                    hour: int.parse(state.preferredStudyStartTime.split(':')[0]),
                    minute: int.parse(state.preferredStudyStartTime.split(':')[1]),
                  ),
                );
                if (time != null) {
                  ref.read(onboardingProvider.notifier).setStudyStartTime(time);
                }
              },
              child: Text(
                state.preferredStudyStartTime,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E3A8A),
                ),
              ),
            ),
          ),
          const Divider(),
          ListTile(
            title: const Text('End time', style: TextStyle(color: Colors.grey)),
            trailing: TextButton(
              onPressed: () async {
                final time = await showTimePicker(
                  context: context,
                  initialTime: TimeOfDay(
                    hour: int.parse(state.preferredStudyEndTime.split(':')[0]),
                    minute: int.parse(state.preferredStudyEndTime.split(':')[1]),
                  ),
                );
                if (time != null) {
                  ref.read(onboardingProvider.notifier).setStudyEndTime(time);
                }
              },
              child: Text(
                state.preferredStudyEndTime,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E3A8A),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Step5FixedSchedule extends ConsumerWidget {
  final VoidCallback onNext;
  
  const _Step5FixedSchedule({required this.onNext});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(onboardingProvider);
    final days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Add your fixed weekly schedule',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'School hours, extracurriculars, etc. (Skip if not needed)',
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: state.fixedBlocks.length,
              itemBuilder: (context, index) {
                final block = state.fixedBlocks[index];
                return Card(
                  child: ListTile(
                    title: Text(block.title),
                    subtitle: Text('${block.dayOfWeek} ${block.startTime} - ${block.endTime}'),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete),
                      onPressed: () {
                        ref.read(onboardingProvider.notifier).removeFixedBlock(index);
                      },
                    ),
                  ),
                );
              },
            ),
          ),
          ElevatedButton.icon(
            onPressed: () => _showAddBlockDialog(context, ref, days),
            icon: const Icon(Icons.add),
            label: const Text('Add block'),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              TextButton(
                onPressed: onNext,
                child: const Text('Skip'),
              ),
              ElevatedButton(
                onPressed: state.fixedBlocks.isEmpty ? null : onNext,
                child: const Text('Continue'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showAddBlockDialog(BuildContext context, WidgetRef ref, List<String> days) {
    final titleController = TextEditingController();
    String type = 'school';
    String day = 'monday';
    TimeOfDay startTime = const TimeOfDay(hour: 8, minute: 0);
    TimeOfDay endTime = const TimeOfDay(hour: 14, minute: 0);

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
              Text(
                'Add block',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Title'),
              ),
              const SizedBox(height: 16),
              const Text('Type'),
              const SizedBox(height: 8),
              Wrap(
                children: [
                  ChoiceChip(
                    label: const Text('School'),
                    selected: type == 'school',
                    onSelected: (_) => setState(() => type = 'school'),
                  ),
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text('Extracurricular'),
                    selected: type == 'extracurricular',
                    onSelected: (_) => setState(() => type = 'extracurricular'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text('Day'),
              const SizedBox(height: 8),
              Wrap(
                children: days.map((d) => ChoiceChip(
                  label: Text(d[0].toUpperCase() + d.substring(1, 3)),
                  selected: day == d,
                  onSelected: (_) => setState(() => day = d),
                )).toList(),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: ListTile(
                      title: const Text('Start'),
                      subtitle: Text(startTime.format(context)),
                      onTap: () async {
                        final time = await showTimePicker(
                          context: context,
                          initialTime: startTime,
                        );
                        if (time != null) {
                          setState(() => startTime = time);
                        }
                      },
                    ),
                  ),
                  Expanded(
                    child: ListTile(
                      title: const Text('End'),
                      subtitle: Text(endTime.format(context)),
                      onTap: () async {
                        final time = await showTimePicker(
                          context: context,
                          initialTime: endTime,
                        );
                        if (time != null) {
                          setState(() => endTime = time);
                        }
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    if (titleController.text.isEmpty) return;
                    ref.read(onboardingProvider.notifier).addFixedBlock(
                      FixedBlockData(
                        title: titleController.text,
                        type: type,
                        dayOfWeek: day,
                        startTime: '${startTime.hour.toString().padLeft(2, '0')}:${startTime.minute.toString().padLeft(2, '0')}',
                        endTime: '${endTime.hour.toString().padLeft(2, '0')}:${endTime.minute.toString().padLeft(2, '0')}',
                      ),
                    );
                    Navigator.pop(context);
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

class _OptionCard extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  const _OptionCard({
    required this.title,
    required this.description,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      color: selected ? const Color(0xFF1E3A8A) : const Color(0xFF1E1E1E),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(icon, size: 32),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      description,
                      style: TextStyle(
                        color: Colors.grey[400],
                      ),
                    ),
                  ],
                ),
              ),
              if (selected)
                const Icon(Icons.check_circle),
            ],
          ),
        ),
      ),
    );
  }
}