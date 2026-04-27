import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get appTitle => 'StudyFlow';

  @override
  String get createAccount => 'Crear cuenta';

  @override
  String get login => 'Iniciar sesión';

  @override
  String get email => 'Correo electrónico';

  @override
  String get password => 'Contraseña';

  @override
  String get fullName => 'Nombre completo';

  @override
  String get learningStyle => 'Estilo de aprendizaje';

  @override
  String get learningStyleVisual => 'Visual';

  @override
  String get learningStyleVisualDesc => 'Aprendo con diagramas/colores';

  @override
  String get learningStyleAuditory => 'Auditivo';

  @override
  String get learningStyleAuditoryDesc => 'Prefiero escuchar/explicar';

  @override
  String get learningStyleReader => 'Lector';

  @override
  String get learningStyleReaderDesc => 'Aprendo leyendo/escribiendo';

  @override
  String get maxStudyHours => '¿Cuántas horas puedes estudiar al día como máximo?';

  @override
  String studyHoursLabel(int hours) {
    return '$hours horas';
  }

  @override
  String get preferredStudyDays => '¿Qué días prefieres estudiar?';

  @override
  String get availableStudyWindow => '¿Cuál es tu horario de estudio disponible cada día?';

  @override
  String get startTime => 'Hora de inicio';

  @override
  String get endTime => 'Hora de fin';

  @override
  String get addFixedSchedule => 'Agrega tu horario semanal fijo';

  @override
  String get fixedScheduleSkip => 'Omitir';

  @override
  String get addBlock => 'Agregar bloque';

  @override
  String get title => 'Título';

  @override
  String get type => 'Tipo';

  @override
  String get typeSchool => 'Escuela';

  @override
  String get typeExtracurricular => 'Extracurricular';

  @override
  String get dayOfWeek => 'Día de la semana';

  @override
  String get monday => 'Lunes';

  @override
  String get tuesday => 'Martes';

  @override
  String get wednesday => 'Miércoles';

  @override
  String get thursday => 'Jueves';

  @override
  String get friday => 'Viernes';

  @override
  String get saturday => 'Sábado';

  @override
  String get sunday => 'Domingo';

  @override
  String get continue => 'Continuar';

  @override
  String get calendar => 'Calendario';

  @override
  String get examsTasks => 'Exámenes y Tareas';

  @override
  String get subjectsGrades => 'Materias y Calificaciones';

  @override
  String get profile => 'Perfil';

  @override
  String get exams => 'Exámenes';

  @override
  String get tasks => 'Tareas';

  @override
  String get addExam => 'Agregar examen';

  @override
  String get addTask => 'Agregar tarea';

  @override
  String get noExamsYet => 'No hay exámenes aún — ¡agrega uno!';

  @override
  String get noTasksYet => 'No hay tareas aún — ¡agrega una!';

  @override
  String get dueDate => 'Fecha de entrega';

  @override
  String get examDate => 'Fecha del examen';

  @override
  String daysRemaining(int days) {
    return '$days días restantes';
  }

  @override
  String studySessionsScheduled(int count) {
    return '$count sesiones de estudio';
  }

  @override
  String get addSubject => 'Agregar materia';

  @override
  String get subjectName => 'Nombre de la materia';

  @override
  String get selectColor => 'Seleccionar color';

  @override
  String get averageGrade => 'Promedio';

  @override
  String get gradeHistory => 'Historial de calificaciones';

  @override
  String get addGrade => 'Agregar calificación';

  @override
  String get gradeTrend => 'Tendencia de notas';

  @override
  String get editProfile => 'Editar perfil';

  @override
  String get myWeeklySchedule => 'Mi horario semanal';

  @override
  String get logout => 'Cerrar sesión';

  @override
  String get save => 'Guardar';

  @override
  String get cancel => 'Cancelar';

  @override
  String get delete => 'Eliminar';

  @override
  String get edit => 'Editar';

  @override
  String get completed => 'Completado';

  @override
  String get upcoming => 'Próximos';

  @override
  String get loading => 'Cargando...';

  @override
  String get error => 'Ocurrió un error';

  @override
  String get retry => 'Reintentar';

  @override
  String get selectSubject => 'Seleccionar materia';

  @override
  String get writeTitle => 'Escribir título';

  @override
  String get tomorrow => 'Mañana';

  @override
  String studySessionStarting(String subject, int duration) {
    return 'Sesión de estudio pronto: $subject por $duration min';
  }

  @override
  String examTomorrow(String subject) {
    return '¡Mañana es tu examen de $subject! Tú puedes.';
  }

  @override
  String taskDueTomorrow(String taskTitle) {
    return 'Tarea pendiente para mañana: $taskTitle';
  }
}
