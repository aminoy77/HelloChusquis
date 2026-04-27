import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'gen_l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates = <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es')
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'StudyFlow'**
  String get appTitle;

  /// No description provided for @createAccount.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get createAccount;

  /// No description provided for @login.
  ///
  /// In en, this message translates to:
  /// **'Log in'**
  String get login;

  /// No description provided for @email.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @fullName.
  ///
  /// In en, this message translates to:
  /// **'Full name'**
  String get fullName;

  /// No description provided for @learningStyle.
  ///
  /// In en, this message translates to:
  /// **'Learning style'**
  String get learningStyle;

  /// No description provided for @learningStyleVisual.
  ///
  /// In en, this message translates to:
  /// **'Visual'**
  String get learningStyleVisual;

  /// No description provided for @learningStyleVisualDesc.
  ///
  /// In en, this message translates to:
  /// **'I learn with diagrams/color'**
  String get learningStyleVisualDesc;

  /// No description provided for @learningStyleAuditory.
  ///
  /// In en, this message translates to:
  /// **'Auditory'**
  String get learningStyleAuditory;

  /// No description provided for @learningStyleAuditoryDesc.
  ///
  /// In en, this message translates to:
  /// **'I prefer listening/explaining'**
  String get learningStyleAuditoryDesc;

  /// No description provided for @learningStyleReader.
  ///
  /// In en, this message translates to:
  /// **'Reader'**
  String get learningStyleReader;

  /// No description provided for @learningStyleReaderDesc.
  ///
  /// In en, this message translates to:
  /// **'I learn by reading/writing'**
  String get learningStyleReaderDesc;

  /// No description provided for @maxStudyHours.
  ///
  /// In en, this message translates to:
  /// **'How many hours can you study per day maximum?'**
  String get maxStudyHours;

  /// No description provided for @studyHoursLabel.
  ///
  /// In en, this message translates to:
  /// **'{hours} hours'**
  String studyHoursLabel(int hours);

  /// No description provided for @preferredStudyDays.
  ///
  /// In en, this message translates to:
  /// **'Which days do you prefer to study?'**
  String get preferredStudyDays;

  /// No description provided for @availableStudyWindow.
  ///
  /// In en, this message translates to:
  /// **'What is your available study window each day?'**
  String get availableStudyWindow;

  /// No description provided for @startTime.
  ///
  /// In en, this message translates to:
  /// **'Start time'**
  String get startTime;

  /// No description provided for @endTime.
  ///
  /// In en, this message translates to:
  /// **'End time'**
  String get endTime;

  /// No description provided for @addFixedSchedule.
  ///
  /// In en, this message translates to:
  /// **'Add your fixed weekly schedule'**
  String get addFixedSchedule;

  /// No description provided for @fixedScheduleSkip.
  ///
  /// In en, this message translates to:
  /// **'Skip'**
  String get fixedScheduleSkip;

  /// No description provided for @addBlock.
  ///
  /// In en, this message translates to:
  /// **'Add block'**
  String get addBlock;

  /// No description provided for @title.
  ///
  /// In en, this message translates to:
  /// **'Title'**
  String get title;

  /// No description provided for @type.
  ///
  /// In en, this message translates to:
  /// **'Type'**
  String get type;

  /// No description provided for @typeSchool.
  ///
  /// In en, this message translates to:
  /// **'School'**
  String get typeSchool;

  /// No description provided for @typeExtracurricular.
  ///
  /// In en, this message translates to:
  /// **'Extracurricular'**
  String get typeExtracurricular;

  /// No description provided for @dayOfWeek.
  ///
  /// In en, this message translates to:
  /// **'Day of week'**
  String get dayOfWeek;

  /// No description provided for @monday.
  ///
  /// In en, this message translates to:
  /// **'Monday'**
  String get monday;

  /// No description provided for @tuesday.
  ///
  /// In en, this message translates to:
  /// **'Tuesday'**
  String get tuesday;

  /// No description provided for @wednesday.
  ///
  /// In en, this message translates to:
  /// **'Wednesday'**
  String get wednesday;

  /// No description provided for @thursday.
  ///
  /// In en, this message translates to:
  /// **'Thursday'**
  String get thursday;

  /// No description provided for @friday.
  ///
  /// In en, this message translates to:
  /// **'Friday'**
  String get friday;

  /// No description provided for @saturday.
  ///
  /// In en, this message translates to:
  /// **'Saturday'**
  String get saturday;

  /// No description provided for @sunday.
  ///
  /// In en, this message translates to:
  /// **'Sunday'**
  String get sunday;

  /// No description provided for @continue.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get continue;

  /// No description provided for @calendar.
  ///
  /// In en, this message translates to:
  /// **'Calendar'**
  String get calendar;

  /// No description provided for @examsTasks.
  ///
  /// In en, this message translates to:
  /// **'Exams & Tasks'**
  String get examsTasks;

  /// No description provided for @subjectsGrades.
  ///
  /// In en, this message translates to:
  /// **'Subjects & Grades'**
  String get subjectsGrades;

  /// No description provided for @profile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// No description provided for @exams.
  ///
  /// In en, this message translates to:
  /// **'Exams'**
  String get exams;

  /// No description provided for @tasks.
  ///
  /// In en, this message translates to:
  /// **'Tasks'**
  String get tasks;

  /// No description provided for @addExam.
  ///
  /// In en, this message translates to:
  /// **'Add exam'**
  String get addExam;

  /// No description provided for @addTask.
  ///
  /// In en, this message translates to:
  /// **'Add task'**
  String get addTask;

  /// No description provided for @noExamsYet.
  ///
  /// In en, this message translates to:
  /// **'No exams yet — add one!'**
  String get noExamsYet;

  /// No description provided for @noTasksYet.
  ///
  /// In en, this message translates to:
  /// **'No tasks yet — add one!'**
  String get noTasksYet;

  /// No description provided for @dueDate.
  ///
  /// In en, this message translates to:
  /// **'Due date'**
  String get dueDate;

  /// No description provided for @examDate.
  ///
  /// In en, this message translates to:
  /// **'Exam date'**
  String get examDate;

  /// No description provided for @daysRemaining.
  ///
  /// In en, this message translates to:
  /// **'{days} days remaining'**
  String daysRemaining(int days);

  /// No description provided for @studySessionsScheduled.
  ///
  /// In en, this message translates to:
  /// **'{count} study sessions'**
  String studySessionsScheduled(int count);

  /// No description provided for @addSubject.
  ///
  /// In en, this message translates to:
  /// **'Add subject'**
  String get addSubject;

  /// No description provided for @subjectName.
  ///
  /// In en, this message translates to:
  /// **'Subject name'**
  String get subjectName;

  /// No description provided for @selectColor.
  ///
  /// In en, this message translates to:
  /// **'Select color'**
  String get selectColor;

  /// No description provided for @averageGrade.
  ///
  /// In en, this message translates to:
  /// **'Average grade'**
  String get averageGrade;

  /// No description provided for @gradeHistory.
  ///
  /// In en, this message translates to:
  /// **'Grade history'**
  String get gradeHistory;

  /// No description provided for @addGrade.
  ///
  /// In en, this message translates to:
  /// **'Add grade'**
  String get addGrade;

  /// No description provided for @gradeTrend.
  ///
  /// In en, this message translates to:
  /// **'Grade trend'**
  String get gradeTrend;

  /// No description provided for @editProfile.
  ///
  /// In en, this message translates to:
  /// **'Edit profile'**
  String get editProfile;

  /// No description provided for @myWeeklySchedule.
  ///
  /// In en, this message translates to:
  /// **'My weekly schedule'**
  String get myWeeklySchedule;

  /// No description provided for @logout.
  ///
  /// In en, this message translates to:
  /// **'Logout'**
  String get logout;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @edit.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get edit;

  /// No description provided for @completed.
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get completed;

  /// No description provided for @upcoming.
  ///
  /// In en, this message translates to:
  /// **'Upcoming'**
  String get upcoming;

  /// No description provided for @loading.
  ///
  /// In en, this message translates to:
  /// **'Loading...'**
  String get loading;

  /// No description provided for @error.
  ///
  /// In en, this message translates to:
  /// **'An error occurred'**
  String get error;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @selectSubject.
  ///
  /// In en, this message translates to:
  /// **'Select subject'**
  String get selectSubject;

  /// No description provided for @writeTitle.
  ///
  /// In en, this message translates to:
  /// **'Write title'**
  String get writeTitle;

  /// No description provided for @tomorrow.
  ///
  /// In en, this message translates to:
  /// **'Tomorrow'**
  String get tomorrow;

  /// No description provided for @studySessionStarting.
  ///
  /// In en, this message translates to:
  /// **'Study session starting soon: {subject} for {duration} min'**
  String studySessionStarting(String subject, int duration);

  /// No description provided for @examTomorrow.
  ///
  /// In en, this message translates to:
  /// **'Tomorrow is your {subject} exam! You\'ve got this.'**
  String examTomorrow(String subject);

  /// No description provided for @taskDueTomorrow.
  ///
  /// In en, this message translates to:
  /// **'Task due tomorrow: {taskTitle}'**
  String taskDueTomorrow(String taskTitle);
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>['en', 'es'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {


  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en': return AppLocalizationsEn();
    case 'es': return AppLocalizationsEs();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.'
  );
}
