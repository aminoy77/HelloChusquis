# Python Flask

- Flask routes map URLs to functions via `@app.route('/hello')` decorators.
- `render_template` separates Jinja HTML from view logic cleanly.
- `request.args/form/json` read query, form, and JSON inputs respectively.
- `jsonify` serializes responses with correct content types automatically.
- Blueprints split large apps into registered modules with prefixes.
- `app.config` centralizes secrets and flags (load from env, never code).
- Extensions (SQLAlchemy, Login) plug in without framework forks.
- Dev server (`flask run`) reloads; production needs gunicorn/uwsgi behind proxies.
- `url_for` builds URLs from endpoint names, surviving route renames.
- Application factories (`create_app`) enable testing with isolated configs.
