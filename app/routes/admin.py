"""
Admin routes for backend management.
Provides authentication, dashboard, and CRUD operations for all models.
"""
from datetime import datetime
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
)
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Quiz, SchoolClass, Setting, Announcement

admin_bp = Blueprint('admin_bp', __name__)


# ==============================================================================
# Authentication Routes
# ==============================================================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Admin login page.
    GET: Display login form (redirect to dashboard if already logged in)
    POST: Authenticate user and redirect to dashboard
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('admin_bp.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('admin/login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            # Redirect to next page if specified, otherwise dashboard
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('admin_bp.dashboard'))

        flash('Invalid username or password.', 'error')
        return render_template('admin/login.html', username=username)

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    """
    Log out the current user and redirect to login page.
    """
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_bp.login'))


# ==============================================================================
# Dashboard Routes
# ==============================================================================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Admin dashboard overview.
    Shows current week, totals, and next quiz info.
    """
    # Get current datetime for determining active/upcoming quizzes
    now = datetime.utcnow()

    # Get all quizzes ordered by week
    quizzes = Quiz.query.order_by(Quiz.week_number).all()

    # Find current and next quiz
    current_quiz = None
    next_quiz = None
    for quiz in quizzes:
        if quiz.is_visible():
            current_quiz = quiz
        elif quiz.opens_at and quiz.opens_at > now and not next_quiz:
            next_quiz = quiz

    # Calculate totals
    online_total = float(Setting.get('online_total', '0') or '0')
    classes = SchoolClass.query.order_by(SchoolClass.name).all()
    rice_bowl_total = sum(c.rice_bowl_amount for c in classes)
    grand_total = online_total + rice_bowl_total

    # Get active announcements count
    active_announcements = Announcement.query.filter_by(enabled=True).count()

    return render_template(
        'admin/dashboard.html',
        current_quiz=current_quiz,
        next_quiz=next_quiz,
        quizzes=quizzes,
        online_total=online_total,
        rice_bowl_total=rice_bowl_total,
        grand_total=grand_total,
        class_count=len(classes),
        active_announcements=active_announcements,
    )


# ==============================================================================
# Quiz Routes
# ==============================================================================

@admin_bp.route('/quizzes')
@login_required
def quizzes():
    """
    List all 6 weeks with edit forms.
    """
    # Ensure all 6 quizzes exist
    _ensure_quizzes_exist()

    quizzes = Quiz.query.order_by(Quiz.week_number).all()
    return render_template('admin/quizzes.html', quizzes=quizzes)


@admin_bp.route('/quizzes/<int:week>', methods=['POST'])
@login_required
def update_quiz(week: int):
    """
    Update quiz data for a specific week.
    """
    quiz = Quiz.query.filter_by(week_number=week).first()

    if not quiz:
        flash(f'Quiz for week {week} not found.', 'error')
        return redirect(url_for('admin_bp.quizzes'))

    try:
        # Basic fields
        quiz.country_name = request.form.get('country_name', '').strip() or f'Week {week}'
        quiz.description = request.form.get('description', '').strip() or None
        quiz.forms_link = request.form.get('forms_link', '').strip() or None

        # Schedule fields
        quiz.schedule_mode = request.form.get('schedule_mode', 'manual')
        quiz.manual_visible = request.form.get('manual_visible') == 'on'

        # Parse datetime fields
        opens_at_str = request.form.get('opens_at', '').strip()
        closes_at_str = request.form.get('closes_at', '').strip()

        quiz.opens_at = _parse_datetime(opens_at_str) if opens_at_str else None
        quiz.closes_at = _parse_datetime(closes_at_str) if closes_at_str else None

        # Validate date range
        if quiz.opens_at and quiz.closes_at and quiz.opens_at >= quiz.closes_at:
            flash('Opening date must be before closing date.', 'error')
            return redirect(url_for('admin_bp.quizzes'))

        # Participant fields
        participant_count_str = request.form.get('participant_count', '0').strip()
        quiz.participant_count = int(participant_count_str) if participant_count_str else 0
        quiz.participants_text = request.form.get('participants_text', '').strip() or None

        # Winner fields
        quiz.winner_1 = request.form.get('winner_1', '').strip() or None
        quiz.winner_2 = request.form.get('winner_2', '').strip() or None
        quiz.winner_3 = request.form.get('winner_3', '').strip() or None

        db.session.commit()
        flash(f'Week {week} quiz updated successfully.', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating quiz: {str(e)}', 'error')

    return redirect(url_for('admin_bp.quizzes'))


# ==============================================================================
# Totals Routes
# ==============================================================================

@admin_bp.route('/totals', methods=['GET'])
@login_required
def totals():
    """
    Show CRS link, online total, and rice bowl totals by class.
    """
    crs_link = Setting.get('crs_donation_link', '')
    online_total = float(Setting.get('online_total', '0') or '0')
    classes = SchoolClass.query.order_by(SchoolClass.name).all()
    rice_bowl_total = sum(c.rice_bowl_amount for c in classes)

    return render_template(
        'admin/totals.html',
        crs_link=crs_link,
        online_total=online_total,
        classes=classes,
        rice_bowl_total=rice_bowl_total,
        grand_total=online_total + rice_bowl_total,
    )


@admin_bp.route('/totals', methods=['POST'])
@login_required
def update_totals():
    """
    Update CRS link and online total.
    """
    try:
        crs_link = request.form.get('crs_donation_link', '').strip()
        online_total_str = request.form.get('online_total', '0').strip()

        # Validate online total
        try:
            online_total = float(online_total_str) if online_total_str else 0.0
            if online_total < 0:
                raise ValueError('Online total cannot be negative.')
        except ValueError:
            flash('Please enter a valid number for online total.', 'error')
            return redirect(url_for('admin_bp.totals'))

        Setting.set('crs_donation_link', crs_link)
        Setting.set('online_total', str(online_total))

        flash('Totals updated successfully.', 'success')

    except Exception as e:
        flash(f'Error updating totals: {str(e)}', 'error')

    return redirect(url_for('admin_bp.totals'))


@admin_bp.route('/totals/class/<int:class_id>', methods=['POST'])
@login_required
def update_class_total(class_id: int):
    """
    Update a single class's rice bowl amount.
    """
    school_class = SchoolClass.query.get(class_id)

    if not school_class:
        flash('Class not found.', 'error')
        return redirect(url_for('admin_bp.totals'))

    try:
        amount_str = request.form.get('rice_bowl_amount', '0').strip()
        amount = float(amount_str) if amount_str else 0.0

        if amount < 0:
            flash('Amount cannot be negative.', 'error')
            return redirect(url_for('admin_bp.totals'))

        school_class.rice_bowl_amount = amount
        db.session.commit()

        flash(f'Updated {school_class.name} to ${amount:.2f}.', 'success')

    except ValueError:
        flash('Please enter a valid number.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating class total: {str(e)}', 'error')

    return redirect(url_for('admin_bp.totals'))


# ==============================================================================
# Classes Routes
# ==============================================================================

@admin_bp.route('/classes', methods=['GET'])
@login_required
def classes():
    """
    List all classes.
    """
    classes = SchoolClass.query.order_by(SchoolClass.name).all()
    return render_template('admin/classes.html', classes=classes)


@admin_bp.route('/classes', methods=['POST'])
@login_required
def add_class():
    """
    Add a new class.
    """
    name = request.form.get('name', '').strip()

    if not name:
        flash('Class name is required.', 'error')
        return redirect(url_for('admin_bp.classes'))

    # Check for duplicate
    existing = SchoolClass.query.filter_by(name=name).first()
    if existing:
        flash(f'A class named "{name}" already exists.', 'error')
        return redirect(url_for('admin_bp.classes'))

    try:
        initial_amount_str = request.form.get('rice_bowl_amount', '0').strip()
        initial_amount = float(initial_amount_str) if initial_amount_str else 0.0

        if initial_amount < 0:
            flash('Initial amount cannot be negative.', 'error')
            return redirect(url_for('admin_bp.classes'))

        new_class = SchoolClass(name=name, rice_bowl_amount=initial_amount)
        db.session.add(new_class)
        db.session.commit()

        flash(f'Class "{name}" added successfully.', 'success')

    except ValueError:
        flash('Please enter a valid number for the initial amount.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding class: {str(e)}', 'error')

    return redirect(url_for('admin_bp.classes'))


@admin_bp.route('/classes/<int:class_id>', methods=['POST'])
@login_required
def update_class(class_id: int):
    """
    Update a class's name and/or amount (form submission).
    """
    school_class = SchoolClass.query.get(class_id)

    if not school_class:
        flash('Class not found.', 'error')
        return redirect(url_for('admin_bp.classes'))

    try:
        new_name = request.form.get('name', '').strip()
        amount_str = request.form.get('rice_bowl_amount', '').strip()

        if new_name and new_name != school_class.name:
            # Check for duplicate name
            existing = SchoolClass.query.filter_by(name=new_name).first()
            if existing and existing.id != class_id:
                flash(f'A class named "{new_name}" already exists.', 'error')
                return redirect(url_for('admin_bp.classes'))
            school_class.name = new_name

        if amount_str:
            amount = float(amount_str)
            if amount < 0:
                flash('Amount cannot be negative.', 'error')
                return redirect(url_for('admin_bp.classes'))
            school_class.rice_bowl_amount = amount

        db.session.commit()
        flash(f'Class "{school_class.name}" updated successfully.', 'success')

    except ValueError:
        flash('Please enter a valid number for the amount.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating class: {str(e)}', 'error')

    return redirect(url_for('admin_bp.classes'))


@admin_bp.route('/classes/<int:class_id>/edit', methods=['POST'])
@login_required
def edit_class(class_id: int):
    """
    Update a class's name via AJAX (JSON response).
    """
    from flask import jsonify

    school_class = SchoolClass.query.get(class_id)

    if not school_class:
        return jsonify({'success': False, 'error': 'Class not found'}), 404

    try:
        data = request.get_json()
        new_name = data.get('name', '').strip() if data else ''

        if not new_name:
            return jsonify({'success': False, 'error': 'Class name is required'}), 400

        if new_name != school_class.name:
            # Check for duplicate name
            existing = SchoolClass.query.filter_by(name=new_name).first()
            if existing and existing.id != class_id:
                return jsonify({'success': False, 'error': f'A class named "{new_name}" already exists'}), 400
            school_class.name = new_name

        db.session.commit()
        return jsonify({'success': True, 'name': school_class.name})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/classes/<int:class_id>/delete', methods=['POST'])
@login_required
def delete_class(class_id: int):
    """
    Delete a class.
    """
    school_class = SchoolClass.query.get(class_id)

    if not school_class:
        flash('Class not found.', 'error')
        return redirect(url_for('admin_bp.classes'))

    try:
        name = school_class.name
        db.session.delete(school_class)
        db.session.commit()
        flash(f'Class "{name}" deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting class: {str(e)}', 'error')

    return redirect(url_for('admin_bp.classes'))


# ==============================================================================
# Announcements Routes
# ==============================================================================

@admin_bp.route('/announcements', methods=['GET'])
@login_required
def announcements():
    """
    List all announcements.
    """
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=announcements)


@admin_bp.route('/announcements', methods=['POST'])
@login_required
def add_announcement():
    """
    Add a new announcement.
    """
    text = request.form.get('text', '').strip()

    if not text:
        flash('Announcement text is required.', 'error')
        return redirect(url_for('admin_bp.announcements'))

    try:
        start_at_str = request.form.get('start_at', '').strip()
        end_at_str = request.form.get('end_at', '').strip()
        enabled = request.form.get('enabled') == 'on'

        start_at = _parse_datetime(start_at_str) if start_at_str else None
        end_at = _parse_datetime(end_at_str) if end_at_str else None

        # Validate date range
        if start_at and end_at and start_at >= end_at:
            flash('Start date must be before end date.', 'error')
            return redirect(url_for('admin_bp.announcements'))

        announcement = Announcement(
            text=text,
            start_at=start_at,
            end_at=end_at,
            enabled=enabled,
        )
        db.session.add(announcement)
        db.session.commit()

        flash('Announcement added successfully.', 'success')

    except ValueError as e:
        flash(f'Invalid date format: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding announcement: {str(e)}', 'error')

    return redirect(url_for('admin_bp.announcements'))


@admin_bp.route('/announcements/<int:id>', methods=['POST'])
@login_required
def update_announcement(id: int):
    """
    Update an announcement.
    """
    announcement = Announcement.query.get(id)

    if not announcement:
        flash('Announcement not found.', 'error')
        return redirect(url_for('admin_bp.announcements'))

    try:
        text = request.form.get('text', '').strip()

        if not text:
            flash('Announcement text is required.', 'error')
            return redirect(url_for('admin_bp.announcements'))

        start_at_str = request.form.get('start_at', '').strip()
        end_at_str = request.form.get('end_at', '').strip()
        enabled = request.form.get('enabled') == 'on'

        start_at = _parse_datetime(start_at_str) if start_at_str else None
        end_at = _parse_datetime(end_at_str) if end_at_str else None

        # Validate date range
        if start_at and end_at and start_at >= end_at:
            flash('Start date must be before end date.', 'error')
            return redirect(url_for('admin_bp.announcements'))

        announcement.text = text
        announcement.start_at = start_at
        announcement.end_at = end_at
        announcement.enabled = enabled

        db.session.commit()
        flash('Announcement updated successfully.', 'success')

    except ValueError as e:
        flash(f'Invalid date format: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating announcement: {str(e)}', 'error')

    return redirect(url_for('admin_bp.announcements'))


@admin_bp.route('/announcements/<int:id>/delete', methods=['POST'])
@login_required
def delete_announcement(id: int):
    """
    Delete an announcement.
    """
    announcement = Announcement.query.get(id)

    if not announcement:
        flash('Announcement not found.', 'error')
        return redirect(url_for('admin_bp.announcements'))

    try:
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting announcement: {str(e)}', 'error')

    return redirect(url_for('admin_bp.announcements'))


# ==============================================================================
# Design Routes
# ==============================================================================

@admin_bp.route('/design', methods=['GET'])
@login_required
def design():
    """
    Theme and logo settings page.
    """
    theme = Setting.get('theme', 'default')
    school_logo_url = Setting.get('school_logo_url', '')
    enable_crs_imagery = Setting.get('enable_crs_imagery', 'true') == 'true'

    return render_template(
        'admin/design.html',
        theme=theme,
        school_logo_url=school_logo_url,
        enable_crs_imagery=enable_crs_imagery,
    )


@admin_bp.route('/design', methods=['POST'])
@login_required
def update_design():
    """
    Update design settings.
    """
    try:
        theme = request.form.get('theme', 'default').strip()
        school_logo_url = request.form.get('school_logo_url', '').strip()
        enable_crs_imagery = request.form.get('enable_crs_imagery') == 'on'

        Setting.set('theme', theme)
        Setting.set('school_logo_url', school_logo_url)
        Setting.set('enable_crs_imagery', 'true' if enable_crs_imagery else 'false')

        flash('Design settings updated successfully.', 'success')

    except Exception as e:
        flash(f'Error updating design settings: {str(e)}', 'error')

    return redirect(url_for('admin_bp.design'))


# ==============================================================================
# Account Routes
# ==============================================================================

@admin_bp.route('/account', methods=['GET'])
@login_required
def account():
    """
    Password change form.
    """
    return render_template('admin/account.html')


@admin_bp.route('/account', methods=['POST'])
@login_required
def update_account():
    """
    Change password.
    Validates current password and confirms new password matches.
    """
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Validate all fields are provided
    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required.', 'error')
        return redirect(url_for('admin_bp.account'))

    # Validate current password
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('admin_bp.account'))

    # Validate new password matches confirmation
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('admin_bp.account'))

    # Validate password length
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'error')
        return redirect(url_for('admin_bp.account'))

    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error changing password: {str(e)}', 'error')

    return redirect(url_for('admin_bp.account'))


# ==============================================================================
# Helper Functions
# ==============================================================================

def _parse_datetime(dt_string: str) -> datetime:
    """
    Parse a datetime string from HTML datetime-local input.

    Args:
        dt_string: String in format 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DD HH:MM'

    Returns:
        datetime object

    Raises:
        ValueError: If string cannot be parsed
    """
    # Try common formats
    formats = [
        '%Y-%m-%dT%H:%M',      # HTML datetime-local format
        '%Y-%m-%d %H:%M',       # Space-separated format
        '%Y-%m-%dT%H:%M:%S',    # With seconds
        '%Y-%m-%d %H:%M:%S',    # With seconds, space-separated
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_string, fmt)
        except ValueError:
            continue

    raise ValueError(f'Cannot parse datetime: {dt_string}')


def _ensure_quizzes_exist() -> None:
    """
    Ensure all 6 weekly quizzes exist in the database.
    Creates missing weeks with default values.
    """
    for week in range(1, 7):
        quiz = Quiz.query.filter_by(week_number=week).first()
        if not quiz:
            quiz = Quiz(
                week_number=week,
                country_name=f'Week {week}',
                schedule_mode='manual',
                manual_visible=False,
            )
            db.session.add(quiz)

    db.session.commit()
