from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('genres', __name__, url_prefix='/genres')


@bp.route('/<int:list_id>')
@login_required
def select_genre(list_id):
    db = get_db()

    genres = db.execute(
        'SELECT id, name FROM genre ORDER BY name ASC'
    ).fetchall()

    return render_template('genres/select_genre.html', genres=genres, list_id=list_id)


@bp.route('/<int:list_id>/<int:genre_id>', methods=('GET', 'POST'))
@login_required
def genre_detail(list_id, genre_id):
    db = get_db()

    # Handle new movie creation
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        if not title:
            flash("Movie title is required.")
        else:
            db.execute(
                'INSERT INTO movie (title, description, genre_id, list_id, added_by) '
                'VALUES (?, ?, ?, ?, ?)',
                (title, description, genre_id, list_id, g.user['id'])
            )
            db.commit()
            return redirect(url_for('genres.genre_detail', list_id=list_id, genre_id=genre_id))

    # Fetch genre name
    genre = db.execute(
        'SELECT name FROM genre WHERE id = ?', (genre_id,)
    ).fetchone()

    # Get watched/unwatched movies
    unwatched = db.execute(
        'SELECT id, title, description FROM movie '
        'WHERE genre_id = ? AND list_id = ? AND watched = 0',
        (genre_id, list_id)
    ).fetchall()

    watched = db.execute(
        'SELECT id, title, description, recommended, rating FROM movie '
        'WHERE genre_id = ? AND list_id = ? AND watched = 1',
        (genre_id, list_id)
    ).fetchall()

    return render_template('genres/genre_detail.html',
                           genre=genre, list_id=list_id,
                           genre_id=genre_id, unwatched=unwatched, watched=watched)


@bp.route('/toggle/<int:movie_id>/<int:list_id>/<int:genre_id>')
@login_required
def toggle_movie(movie_id, list_id, genre_id):
    db = get_db()
    db.execute(
        'UPDATE movie SET watched = NOT watched WHERE id = ?',
        (movie_id,)
    )
    db.commit()
    return redirect(url_for('genres.genre_detail', list_id=list_id, genre_id=genre_id))

@bp.route('/<int:list_id>/<int:genre_id>/<int:movie_id>/mark_watched', methods=('GET', 'POST'))
@login_required
def mark_watched_form(list_id, genre_id, movie_id):
    db = get_db()

    if request.method == 'POST':
        recommended = request.form.get('recommended') == 'yes'
        rating = request.form.get('rating')

        try:
            rating = float(rating)
            if not (1.0 <= rating <= 10.0):
                raise ValueError
        except ValueError:
            flash("Rating must be a number between 1 and 10.")
            return redirect(url_for('genres.mark_watched_form', list_id=list_id, genre_id=genre_id, movie_id=movie_id))

        db.execute(
            'UPDATE movie SET watched = 1, recommended = ?, rating = ? WHERE id = ?',
            (recommended, rating, movie_id)
        )
        db.commit()
        return redirect(url_for('genres.genre_detail', list_id=list_id, genre_id=genre_id))

    return render_template('genres/mark_watched.html', list_id=list_id, genre_id=genre_id, movie_id=movie_id)
