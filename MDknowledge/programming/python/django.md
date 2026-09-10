# Python Django

- Django batteries-include admin, ORM, auth, and migrations out of the box.
- Models define schema in Python; `makemigrations` plus `migrate` evolve databases.
- Admin auto-UI (`admin.site.register`) manages content in minutes.
- Views map URLs (`urls.py`) to responses; templates render HTML separately.
- ORM querysets (`filter/exclude/annotate`) compose lazily until evaluated.
- `select_related/prefetch_related` kill N+1 queries before they reach production.
- Forms validate and clean user input with declared fields.
- Authentication, sessions, and CSRF protection ship enabled by default.
- `manage.py test` runs the suite; fixtures/factories seed repeatable data.
- Settings modules per environment keep secrets out of version control.
