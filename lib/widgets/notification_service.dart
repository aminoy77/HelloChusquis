import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz_data;
import '../models/exam.dart';
import '../models/task.dart';
import '../models/study_session.dart';
import '../models/subject.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notifications =
      FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    tz_data.initializeTimeZones();

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const macOSSettings = DarwinInitializationSettings(
      requestSoundPermission: true,
      requestAlertPermission: true,
      requestBadgePermission: true,
    );
    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: macOSSettings,
    );

    await _notifications.initialize(initSettings);
  }

  static Future<bool> requestPermissions() async {
    final android = _notifications.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (android != null) {
      await android.requestNotificationsPermission();
    }
    return true;
  }

  static Future<void> scheduleExamReminder({
    required Exam exam,
    required Subject subject,
  }) async {
    final examDay = DateTime(
      exam.examDate.year,
      exam.examDate.month,
      exam.examDate.day,
    );
    final reminderDay = examDay.subtract(const Duration(days: 1));

    if (reminderDay.isBefore(DateTime.now())) return;

    await _notifications.zonedSchedule(
      exam.id.hashCode,
      'Exam Tomorrow!',
      'Tomorrow is your ${subject.name} exam! You\'ve got this.',
      tz.TZDateTime.from(reminderDay, tz.local),
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'exam_reminder',
          'Exam Reminders',
          channelDescription: 'Reminders for upcoming exams',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      matchDateTimeComponents: DateTimeComponents.dateAndTime,
      uiLocalNotificationDateInterpretation: UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

  static Future<void> scheduleSessionReminder({
    required StudySession session,
    required Subject subject,
  }) async {
    final sessionDateTime = DateTime(
      session.date.year,
      session.date.month,
      session.date.day,
      int.parse(session.startTime.split(':')[0]),
      int.parse(session.startTime.split(':')[1]) - 30,
    );

    if (sessionDateTime.isBefore(DateTime.now())) return;

    await _notifications.zonedSchedule(
      session.id.hashCode,
      'Study Session Starting Soon',
      '${subject.name} for ${session.durationMinutes} min',
      tz.TZDateTime.from(sessionDateTime, tz.local),
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'session_reminder',
          'Study Session Reminders',
          channelDescription: 'Reminders for study sessions',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      matchDateTimeComponents: DateTimeComponents.dateAndTime,
      uiLocalNotificationDateInterpretation: UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

  static Future<void> scheduleTaskReminder({
    required Task task,
  }) async {
    final dueDay = DateTime(
      task.dueDate.year,
      task.dueDate.month,
      task.dueDate.day,
    );
    final reminderDay = dueDay.subtract(const Duration(days: 1));

    if (reminderDay.isBefore(DateTime.now())) return;

    await _notifications.zonedSchedule(
      task.id.hashCode,
      'Task Due Tomorrow',
      'Task due tomorrow: ${task.title}',
      tz.TZDateTime.from(reminderDay, tz.local),
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'task_reminder',
          'Task Reminders',
          channelDescription: 'Reminders for tasks',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      matchDateTimeComponents: DateTimeComponents.dateAndTime,
      uiLocalNotificationDateInterpretation: UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

  static Future<void> cancelNotification(int id) async {
    await _notifications.cancel(id);
  }

  static Future<void> cancelAllNotifications() async {
    await _notifications.cancelAll();
  }
}