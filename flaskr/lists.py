from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('lists', __name__, url_prefix='/lists')

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create_list():
    if request.method == 'POST':
        name = request.form['name']
        error = None

        if not name:
            error = 'List name is required.'

        if error is None:
            db = get_db()
            cursor = db.cursor()

            # Insert the new list
            cursor.execute(
                'INSERT INTO list (name, created_by) VALUES (?, ?)',
                (name, g.user['id'])
            )
            list_id = cursor.lastrowid

            # Add the creator to the list with edit access
            cursor.execute(
                'INSERT INTO list_user (list_id, user_id, can_edit) VALUES (?, ?, ?)',
                (list_id, g.user['id'], True)
            )

            db.commit()
            return redirect(url_for('view_list', list_id=list_id))

        flash(error)

    return render_template('lists/create_list.html')


@bp.route('/<int:list_id>')
@login_required
def view_list(list_id):
    db = get_db()

    # Confirm user has access
    access = db.execute(
        'SELECT * FROM list_user WHERE list_id = ? AND user_id = ?',
        (list_id, g.user['id'])
    ).fetchone()

    if access is None:
        flash("You don't have access to this list.")
        return redirect(url_for('dashboard'))

    # Get list info
    list_info = db.execute(
        'SELECT * FROM list WHERE id = ?', (list_id,)
    ).fetchone()

    return render_template('lists/view_list.html', list=list_info)


@bp.route('/<int:list_id>/invite', methods=('GET', 'POST'))
@login_required
def invite_user(list_id):
    db = get_db()

    # Check that current user can edit the list
    access = db.execute(
        'SELECT can_edit FROM list_user WHERE list_id = ? AND user_id = ?',
        (list_id, g.user['id'])
    ).fetchone()

    if access is None or not access['can_edit']:
        flash("You don't have permission to invite users to this list.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        permission = request.form.get('permission')  # 'view' or 'edit'
        can_edit = permission == 'edit'

        # Look up user
        user = db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            flash("User not found.")
        else:
            # Check if already added
            existing = db.execute(
                'SELECT * FROM list_user WHERE list_id = ? AND user_id = ?',
                (list_id, user['id'])
            ).fetchone()

            if existing:
                flash("User is already added to this list.")
            else:
                db.execute(
                    'INSERT INTO list_user (list_id, user_id, can_edit) VALUES (?, ?, ?)',
                    (list_id, user['id'], can_edit)
                )
                db.commit()
                flash(f"User {username} added with {'edit' if can_edit else 'view'} access.")
                return redirect(url_for('view_list', list_id=list_id))

    return render_template('lists/invite_user.html', list_id=list_id)
