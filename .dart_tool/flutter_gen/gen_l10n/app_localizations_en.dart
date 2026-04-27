import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'StudyFlow';

  @override
  String get createAccount => 'Create account';

  @override
  String get login => 'Log in';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get fullName => 'Full name';

  @override
  String get learningStyle => 'Learning style';

  @override
  String get learningStyleVisual => 'Visual';

  @override
  String get learningStyleVisualDesc => 'I learn with diagrams/color';

  @override
  String get learningStyleAuditory => 'Auditory';

  @override
  String get learningStyleAuditoryDesc => 'I prefer listening/explaining';

  @override
  String get learningStyleReader => 'Reader';

  @override
  String get learningStyleReaderDesc => 'I learn by reading/writing';

  @override
  String get maxStudyHours => 'How many hours can you study per day maximum?';

  @override
  String studyHoursLabel(int hours) {
    return '$hours hours';
  }

  @override
  String get preferredStudyDays => 'Which days do you prefer to study?';

  @override
  String get availableStudyWindow => 'What is your available study window each day?';

  @override
  String get startTime => 'Start time';

  @override
  String get endTime => 'End time';

  @override
  String get addFixedSchedule => 'Add your fixed weekly schedule';

  @override
  String get fixedScheduleSkip => 'Skip';

  @override
  String get addBlock => 'Add block';

  @override
  String get title => 'Title';

  @override
  String get type => 'Type';

  @override
  String get typeSchool => 'School';

  @override
  String get typeExtracurricular => 'Extracurricular';

  @override
  String get dayOfWeek => 'Day of week';

  @override
  String get monday => 'Monday';

  @override
  String get tuesday => 'Tuesday';

  @override
  String get wednesday => 'Wednesday';

  @override
  String get thursday => 'Thursday';

  @override
  String get friday => 'Friday';

  @override
  String get saturday => 'Saturday';

  @override
  String get sunday => 'Sunday';

  @override
  String get continue => 'Continue';

  @override
  String get calendar => 'Calendar';

  @override
  String get examsTasks => 'Exams & Tasks';

  @override
  String get subjectsGrades => 'Subjects & Grades';

  @override
  String get profile => 'Profile';

  @override
  String get exams => 'Exams';

  @override
  String get tasks => 'Tasks';

  @override
  String get addExam => 'Add exam';

  @override
  String get addTask => 'Add task';

  @override
  String get noExamsYet => 'No exams yet — add one!';

  @override
  String get noTasksYet => 'No tasks yet — add one!';

  @override
  String get dueDate => 'Due date';

  @override
  String get examDate => 'Exam date';

  @override
  String daysRemaining(int days) {
    return '$days days remaining';
  }

  @override
  String studySessionsScheduled(int count) {
    return '$count study sessions';
  }

  @override
  String get addSubject => 'Add subject';

  @override
  String get subjectName => 'Subject name';

  @override
  String get selectColor => 'Select color';

  @override
  String get averageGrade => 'Average grade';

  @override
  String get gradeHistory => 'Grade history';

  @override
  String get addGrade => 'Add grade';

  @override
  String get gradeTrend => 'Grade trend';

  @override
  String get editProfile => 'Edit profile';

  @override
  String get myWeeklySchedule => 'My weekly schedule';

  @override
  String get logout => 'Logout';

  @override
  String get save => 'Save';

  @override
  String get cancel => 'Cancel';

  @override
  String get delete => 'Delete';

  @override
  String get edit => 'Edit';

  @override
  String get completed => 'Completed';

  @override
  String get upcoming => 'Upcoming';

  @override
  String get loading => 'Loading...';

  @override
  String get error => 'An error occurred';

  @override
  String get retry => 'Retry';

  @override
  String get selectSubject => 'Select subject';

  @override
  String get writeTitle => 'Write title';

  @override
  String get tomorrow => 'Tomorrow';

  @override
  String studySessionStarting(String subject, int duration) {
    return 'Study session starting soon: $subject for $duration min';
  }

  @override
  String examTomorrow(String subject) {
    return 'Tomorrow is your $subject exam! You\'ve got this.';
  }

  @override
  String taskDueTomorrow(String taskTitle) {
    return 'Task due tomorrow: $taskTitle';
  }
}
