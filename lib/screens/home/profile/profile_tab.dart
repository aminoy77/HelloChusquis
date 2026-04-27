import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../../models/user_profile.dart';
import '../../../models/fixed_block.dart';
import '../../../providers/app_providers.dart';
import '../../../repositories/user_profile_repository.dart';
import '../../../repositories/fixed_block_repository.dart';

class ProfileTab extends ConsumerWidget {
  const ProfileTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final profileAsync = ref.watch(userProfileProvider2(user.id));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => _showEditProfileDialog(context, ref, user.id),
          ),
        ],
      ),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (profile) {
          if (profile == null) {
            return const Center(child: Text('No profile found'));
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: const Color(0xFF1E3A8A),
                    child: Text(
                      profile.fullName.isNotEmpty ? profile.fullName[0].toUpperCase() : '?',
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                  title: Text(profile.fullName),
                  subtitle: Text(user.email ?? 'No email'),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      title: const Text('Learning style'),
                      trailing: Text(
                        profile.learningStyle[0].toUpperCase() +
                            profile.learningStyle.substring(1),
                      ),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Max study hours per day'),
                      trailing: Text('${profile.maxStudyHoursPerDay} hours'),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Preferred study days'),
                      trailing: Text(profile.preferredStudyDays.join(', ')),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Study window'),
                      trailing: Text(
                        '${profile.preferredStudyStartTime} - ${profile.preferredStudyEndTime}',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'My weekly schedule',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              _FixedBlocksList(userId: user.id),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => _showAddBlockDialog(context, ref, user.id),
                  child: const Text('Add fixed block'),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFEF4444),
                  ),
                  onPressed: () => _logout(context),
                  child: const Text('Logout'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showEditProfileDialog(BuildContext context, WidgetRef ref, String userId) {
    final profileAsync = ref.read(userProfileProvider2(userId));

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        final profile = profileAsync.valueOrNull;
        if (profile == null) {
          return const Center(child: CircularProgressIndicator());
        }

        final nameController = TextEditingController(text: profile.fullName);
        String learningStyle = profile.learningStyle;
        int maxHours = profile.maxStudyHoursPerDay;
        List<String> studyDays = List.from(profile.preferredStudyDays);
        TimeOfDay startTime = TimeOfDay(
          hour: int.parse(profile.preferredStudyStartTime.split(':')[0]),
          minute: int.parse(profile.preferredStudyStartTime.split(':')[1]),
        );
        TimeOfDay endTime = TimeOfDay(
          hour: int.parse(profile.preferredStudyEndTime.split(':')[0]),
          minute: int.parse(profile.preferredStudyEndTime.split(':')[1]),
        );

        return StatefulBuilder(
          builder: (context, setState) => SingleChildScrollView(
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
                  'Edit profile',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(labelText: 'Full name'),
                ),
                const SizedBox(height: 16),
                const Text('Learning style'),
                const SizedBox(height: 8),
                Wrap(
                  children: [
                    ChoiceChip(
                      label: const Text('Visual'),
                      selected: learningStyle == 'visual',
                      onSelected: (_) => setState(() => learningStyle = 'visual'),
                    ),
                    const SizedBox(width: 8),
                    ChoiceChip(
                      label: const Text('Auditory'),
                      selected: learningStyle == 'auditory',
                      onSelected: (_) => setState(() => learningStyle = 'auditory'),
                    ),
                    const SizedBox(width: 8),
                    ChoiceChip(
                      label: const Text('Reader'),
                      selected: learningStyle == 'reader',
                      onSelected: (_) => setState(() => learningStyle = 'reader'),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text('Max study hours: $maxHours'),
                Slider(
                  value: maxHours.toDouble(),
                  min: 1,
                  max: 8,
                  divisions: 7,
                  onChanged: (v) => setState(() => maxHours = v.toInt()),
                ),
                const SizedBox(height: 16),
                const Text('Preferred days'),
                Wrap(
                  children: [
                    for (final day in [
                      'monday',
                      'tuesday',
                      'wednesday',
                      'thursday',
                      'friday',
                      'saturday',
                      'sunday'
                    ])
                      FilterChip(
                        label: Text(day[0].toUpperCase() + day.substring(1, 3)),
                        selected: studyDays.contains(day),
                        onSelected: (selected) {
                          setState(() {
                            if (selected) {
                              studyDays.add(day);
                            } else {
                              studyDays.remove(day);
                            }
                          });
                        },
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Start'),
                        trailing: Text(startTime.format(context)),
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
                        contentPadding: EdgeInsets.zero,
                        title: const Text('End'),
                        trailing: Text(endTime.format(context)),
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
                    onPressed: () async {
                      final repo = UserProfileRepository();
                      await repo.updateProfile(userId, {
                        'full_name': nameController.text,
                        'learning_style': learningStyle,
                        'max_study_hours_per_day': maxHours,
                        'preferred_study_days': studyDays,
                        'preferred_study_start_time':
                            '${startTime.hour.toString().padLeft(2, '0')}:${startTime.minute.toString().padLeft(2, '0')}',
                        'preferred_study_end_time':
                            '${endTime.hour.toString().padLeft(2, '0')}:${endTime.minute.toString().padLeft(2, '0')}',
                      });

                      ref.invalidate(userProfileProvider2(userId));

                      if (context.mounted) Navigator.pop(context);
                    },
                    child: const Text('Save'),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showAddBlockDialog(BuildContext context, WidgetRef ref, String userId) {
    final titleController = TextEditingController();
    String type = 'school';
    String day = 'monday';
    TimeOfDay startTime = const TimeOfDay(hour: 8, minute: 0);
    TimeOfDay endTime = const TimeOfDay(hour: 14, minute: 0);

    final days = [
      'monday',
      'tuesday',
      'wednesday',
      'thursday',
      'friday',
      'saturday',
      'sunday'
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
              Text('Add block', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 16),
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Title'),
              ),
              const SizedBox(height: 16),
              const Text('Type'),
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
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Start'),
                      trailing: Text(startTime.format(context)),
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
                      contentPadding: EdgeInsets.zero,
                      title: const Text('End'),
                      trailing: Text(endTime.format(context)),
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
                  onPressed: () async {
                    if (titleController.text.isEmpty) return;

                    final repo = FixedBlockRepository();
                    await repo.createFixedBlock(
                      userId,
                      titleController.text,
                      type,
                      day,
                      '${startTime.hour.toString().padLeft(2, '0')}:${startTime.minute.toString().padLeft(2, '0')}',
                      '${endTime.hour.toString().padLeft(2, '0')}:${endTime.minute.toString().padLeft(2, '0')}',
                    );

                    ref.invalidate(fixedBlocksProvider2(userId));

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

  void _logout(BuildContext context) async {
    await Supabase.instance.client.auth.signOut();
    if (context.mounted) {
      Navigator.of(context).pushReplacementNamed('/auth');
    }
  }
}

class _FixedBlocksList extends ConsumerWidget {
  final String userId;

  const _FixedBlocksList({required this.userId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final blocksAsync = ref.watch(fixedBlocksProvider2(userId));

    return blocksAsync.when(
      loading: () => const CircularProgressIndicator(),
      error: (e, _) => Text('Error: $e'),
      data: (blocks) {
        if (blocks.isEmpty) {
          return const Card(
            child: ListTile(
              title: Text('No fixed blocks', style: TextStyle(color: Colors.grey)),
            ),
          );
        }

        return Card(
          child: Column(
            children: blocks.map((block) => ListTile(
              title: Text(block.title),
              subtitle: Text(
                '${block.dayOfWeek[0].toUpperCase() + block.dayOfWeek.substring(1)} ${block.startTime} - ${block.endTime}',
              ),
              trailing: IconButton(
                icon: const Icon(Icons.delete, size: 20),
                onPressed: () async {
                  final repo = FixedBlockRepository();
                  await repo.deleteFixedBlock(block.id);
                  ref.invalidate(fixedBlocksProvider2(userId));
                },
              ),
            )).toList(),
          ),
        );
      },
    );
  }
}