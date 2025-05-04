import os

from flask import Flask

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    from . import lists
    app.register_blueprint(lists.bp)

    from . import genres
    app.register_blueprint(genres.bp)

    @app.route('/dashboard')
    def dashboard():
        from flaskr.db import get_db
        db = get_db()
        user_id = g.user['id'] if g.user else None

        # Get lists the user belongs to
        lists = db.execute(
            'SELECT l.id, l.name, lu.can_edit '
            'FROM list l JOIN list_user lu ON l.id = lu.list_id '
            'WHERE lu.user_id = ?',
            (user_id,)
        ).fetchall()

        # Get recent movie activity
        activity = db.execute(
            'SELECT m.title, m.watched, m.created, u.firstname, l.name AS list_name '
            'FROM movie m '
            'JOIN user u ON m.added_by = u.id '
            'JOIN list l ON m.list_id = l.id '
            'ORDER BY m.created DESC '
            'LIMIT 5'
        ).fetchall()

        return render_template('dashboard.html', lists=lists, activity=activity)

    return app
