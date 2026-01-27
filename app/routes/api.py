"""
API routes for public frontend access.
"""
from datetime import datetime
from flask import Blueprint, jsonify
from app.models import Quiz, SchoolClass, Setting, Announcement, db

api_bp = Blueprint('api', __name__)


@api_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@api_bp.route('/data')
def get_data():
    """
    Get all data needed for the public page.

    Returns JSON with:
    - current_week: Current week number based on quiz schedules
    - quizzes: All quizzes with visibility, participants, winners
    - classes: All school classes with rice bowl amounts
    - settings: Application settings
    - announcements: Active announcements
    - rice_bowl_total: Sum of all class amounts
    - grand_total: Online alms + rice bowl total
    """
    try:
        # Get current week based on visible quizzes
        current_week = _determine_current_week()

        # Get all quizzes
        quizzes = Quiz.query.order_by(Quiz.week_number).all()
        quiz_data = []

        for quiz in quizzes:
            # Parse participants (one per line)
            participants = []
            if quiz.participants_text:
                participants = [
                    line.strip()
                    for line in quiz.participants_text.split('\n')
                    if line.strip()
                ]

            # Parse winners
            winners = []
            if quiz.winner_1:
                winners.append(quiz.winner_1)
            if quiz.winner_2:
                winners.append(quiz.winner_2)
            if quiz.winner_3:
                winners.append(quiz.winner_3)

            # Determine visibility
            is_visible = quiz.is_visible()

            quiz_data.append({
                'week_number': quiz.week_number,
                'country_name': quiz.country_name,
                'description': quiz.description or '',
                'forms_link': quiz.forms_link or '',
                'opens_at': quiz.opens_at.isoformat() if quiz.opens_at else None,
                'closes_at': quiz.closes_at.isoformat() if quiz.closes_at else None,
                'is_visible': is_visible,
                'participant_count': quiz.participant_count,
                'participants': participants,
                'winners': winners
            })

        # Get all school classes
        classes = SchoolClass.query.order_by(SchoolClass.name).all()
        class_data = [
            {
                'id': cls.id,
                'name': cls.name,
                'rice_bowl_amount': cls.rice_bowl_amount
            }
            for cls in classes
        ]

        # Get settings with defaults
        settings = {
            'crs_donation_link': Setting.get('crs_donation_link', ''),
            'online_alms_total': Setting.get('online_alms_total', '0.00'),
            'show_grand_total': Setting.get('show_grand_total', 'false'),
            'theme': Setting.get('theme', 'lenten-purple'),
            'school_logo_url': Setting.get('school_logo_url', ''),
            'enable_crs_imagery': Setting.get('enable_crs_imagery', 'true')
        }

        # Get active announcements
        all_announcements = Announcement.query.all()
        active_announcements = [
            {
                'id': ann.id,
                'text': ann.text,
                'enabled': ann.enabled
            }
            for ann in all_announcements
            if ann.is_active()
        ]

        # Calculate totals
        rice_bowl_total = sum(cls.rice_bowl_amount for cls in classes)

        try:
            online_alms = float(settings['online_alms_total'])
        except (ValueError, TypeError):
            online_alms = 0.0

        grand_total = online_alms + rice_bowl_total

        # Build response
        response = {
            'current_week': current_week,
            'quizzes': quiz_data,
            'classes': class_data,
            'settings': settings,
            'announcements': active_announcements,
            'rice_bowl_total': rice_bowl_total,
            'grand_total': grand_total
        }

        # Add CORS headers for public access
        resp = jsonify(response)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'

        return resp

    except Exception as e:
        # Log error and return fallback response
        print(f"Error in /api/data: {e}")

        error_response = {
            'current_week': 1,
            'quizzes': [],
            'classes': [],
            'settings': {
                'crs_donation_link': '',
                'online_alms_total': '0.00',
                'show_grand_total': 'false',
                'theme': 'lenten-purple',
                'school_logo_url': '',
                'enable_crs_imagery': 'true'
            },
            'announcements': [],
            'rice_bowl_total': 0.0,
            'grand_total': 0.0
        }

        resp = jsonify(error_response)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 500


def _determine_current_week() -> int:
    """
    Determine the current week number based on quiz schedules.

    Returns:
        Current week number (defaults to 1 if no visible quizzes)
    """
    now = datetime.utcnow()

    # Get all quizzes ordered by week
    quizzes = Quiz.query.order_by(Quiz.week_number).all()

    if not quizzes:
        return 1

    # Find the first visible quiz
    for quiz in quizzes:
        if quiz.is_visible():
            return quiz.week_number

    # Find the latest quiz that has closed
    for quiz in reversed(quizzes):
        if quiz.schedule_mode == 'scheduled' and quiz.closes_at:
            if now > quiz.closes_at:
                # Return next week (capped at max week + 1)
                return min(quiz.week_number + 1, max(q.week_number for q in quizzes))

    # Default to first week
    return 1
