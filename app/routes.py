from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, NewsInputForm, NewsArticle
from .services.ai_utils import analyze_article, rewrite_article, generate_diff_html, suggest_headlines, fact_check_claims, bias_framing_analysis, tone_effect_analysis
from urllib.parse import urlparse
from .rbac import role_required
import json, requests
import re
from bs4 import BeautifulSoup

main = Blueprint('main', __name__)

def fetch_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join([p.get_text() for p in paragraphs])[:5000]
    except Exception as e:
        print("Fetch error:", e)
        return ""

def clean_bullet_points(raw_text):
    """
    Converts raw bullet points into HTML-safe list items,
    with **Heading**: converted to <strong>Heading</strong>:
    """
    lines = []
    for line in raw_text.splitlines():
        line = line.strip().lstrip("-•* ").strip()
        if not line:
            continue

        # Convert Markdown-style bold heading (**Heading**:) to <strong>Heading</strong>:
        line = re.sub(r"\*\*(.+?)\*\*:", r"<strong>\1</strong>:", line)
        line = re.sub(r"(.+?)\*\*:", r"<strong>\1</strong>:", line)  # Handle: Heading**:
        line = re.sub(r"\*\*(.+?):", r"<strong>\1</strong>:", line)  # Handle: **Heading:
        
        lines.append(line)
    return lines

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if session['role'] == 'employee':
        return render_template('dashboard_employee.html')

    total_articles = NewsArticle.query.count()

    # Most common tone
    common_tone = db.session.query(
        NewsArticle.tone,
        db.func.count(NewsArticle.tone).label("count")
    ).group_by(NewsArticle.tone).order_by(db.desc("count")).first()
    most_common_tone = common_tone[0] if common_tone else "N/A"

    # Most common perspective
    common_perspective = db.session.query(
        NewsArticle.bias,
        db.func.count(NewsArticle.bias).label("count")
    ).group_by(NewsArticle.bias).order_by(db.desc("count")).first()
    most_common_perspective = common_perspective[0] if common_perspective else "N/A"

    # Avg anger
    emotion_scores = NewsArticle.query.with_entities(NewsArticle.emotion_score).all()
    total_anger = 0.0
    count = 0
    for row in emotion_scores:
        try:
            parsed = json.loads(row[0])
            total_anger += parsed.get("anger", 0)
            count += 1
        except Exception:
            pass
    avg_anger = round(total_anger / count, 2) if count else 0.0

    # Get last 10 articles
    recent_articles_raw = NewsArticle.query.order_by(NewsArticle.id.desc()).limit(10).all()
    recent_articles = []
    for art in recent_articles_raw:
        try:
            emotions = json.loads(art.emotion_score)
        except Exception:
            emotions = {"anger": 0, "joy": 0, "fear": 0, "surprise": 0}
        
        parsed_url = urlparse(art.url or "")
        domain = parsed_url.netloc.replace("www.", "") if parsed_url.netloc else "N/A"

        recent_articles.append({
            "summary": art.summary[:100] + ("..." if len(art.summary) > 100 else ""),
            "tone": art.tone,
            "bias": art.bias,
            "anger": emotions.get("anger", 0),
            "joy": emotions.get("joy", 0),
            "fear": emotions.get("fear", 0),
            "surprise": emotions.get("surprise", 0),
            "url": art.url or "#",
            "domain": domain
        })

    return render_template(
        'dashboard.html',
        total_articles=total_articles,
        most_common_tone=most_common_tone,
        most_common_perspective=most_common_perspective,
        avg_anger=avg_anger,
        recent_articles=recent_articles
    )


@main.route('/users')
@role_required('super_admin')
def users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template('users.html', users=users)

@main.route('/users/add', methods=['GET', 'POST'])
@role_required('super_admin')
def add_user():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('main.add_user'))
        new_user = User(
            name=request.form['name'],
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            role=request.form['role']
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully.', 'success')
        return redirect(url_for('main.users'))
    return render_template('add_user.html')

@main.route('/users/promote/<int:user_id>')
@role_required('super_admin')
def promote_user(user_id):
    if 'user_id' not in session or session.get('role') != 'super_admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'employee':
        user.role = 'admin'
        db.session.commit()
        flash(f'{user.username} promoted to Admin.', 'success')
    return redirect(url_for('main.users'))

@main.route('/users/demote/<int:user_id>')
@role_required('super_admin')
def demote_user(user_id):
    if 'user_id' not in session or session.get('role') != 'super_admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        user.role = 'employee'
        db.session.commit()
        flash(f'{user.username} demoted to Employee.', 'warning')
    return redirect(url_for('main.users'))

@main.route('/users/delete/<int:user_id>')
@role_required('super_admin')
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'super_admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role != 'super_admin':
        db.session.delete(user)
        db.session.commit()
        flash(f'{user.username} deleted.', 'danger')
    return redirect(url_for('main.users'))

@main.route('/mediaaudit', methods=['GET', 'POST'])
def mediaaudit():
    form = NewsInputForm()
    result = None

    def fetch_text_from_url(url):
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all("p")
            return " ".join([p.get_text() for p in paragraphs])[:5000]
        except Exception as e:
            print("Fetch error:", e)
            return ""

    if form.validate_on_submit():
        text = form.raw_text.data or fetch_text_from_url(form.url.data)
        analysis = analyze_article(text)

        summary = analysis.get("summary", "Not available")
        perspective_label = analysis.get("perspective_label", "Unknown")
        tone = analysis.get("tone", "Unknown")
        tone_color = analysis.get("tone_color", "secondary")
        emotion_score = analysis.get("emotion_score", {})

        headline_suggestion, headline_variants = suggest_headlines(text)
        claims_factcheck = fact_check_claims(text)

        # Split bias and tone into bullet list items
        claims_factcheck_raw = fact_check_claims(text)
        bias_framing_raw = bias_framing_analysis(text)
        tone_effect_raw = tone_effect_analysis(text)

        claims_factcheck = clean_bullet_points(claims_factcheck_raw)
        bias_framing = clean_bullet_points(bias_framing_raw)
        tone_effect = clean_bullet_points(tone_effect_raw)

        # Store minimal to DB
        article = NewsArticle(
            title='',
            url=form.url.data,
            full_text=text,
            summary=summary,
            bias=perspective_label,
            tone=tone,
            emotion_score=json.dumps(emotion_score),
        )
        db.session.add(article)
        db.session.commit()

        result = {
            "summary": summary,
            "perspective_label": perspective_label,
            "tone": tone,
            "tone_color": tone_color,
            "emotion_score": emotion_score,
            "headline_suggestion": headline_suggestion,
            "headline_variants": headline_variants,
            "claims_factcheck": claims_factcheck,
            "bias_framing": bias_framing,
            "tone_effect": tone_effect,
        }

    return render_template('mediaaudit.html', form=form, result=result)


@main.route('/compare', methods=['GET', 'POST'])
def compare_articles():
    results = []

    if request.method == 'POST':
        url1 = request.form.get('url1', '').strip()
        url2 = request.form.get('url2', '').strip()
        text1 = request.form.get('text1', '').strip()
        text2 = request.form.get('text2', '').strip()

        article_1_text = text1 or fetch_text_from_url(url1)
        article_2_text = text2 or fetch_text_from_url(url2)

        if article_1_text:
            a1 = analyze_article(article_1_text)
            results.append({
                "summary": a1.get("summary"),
                "perspective_label": a1.get("perspective_label"),
                "tone": a1.get("tone"),
                "tone_color": a1.get("tone_color"),
                "emotion_score": a1.get("emotion_score")
            })

        if article_2_text:
            a2 = analyze_article(article_2_text)
            results.append({
                "summary": a2.get("summary"),
                "perspective_label": a2.get("perspective_label"),
                "tone": a2.get("tone"),
                "tone_color": a2.get("tone_color"),
                "emotion_score": a2.get("emotion_score")
            })

    return render_template('compare.html', results=results)


@main.route('/rewrite', methods=['GET', 'POST'])
def rewrite_assistant():
    form = NewsInputForm()
    result = None

    if form.validate_on_submit():
        text = form.raw_text.data or fetch_text_from_url(form.url.data)

        rewritten = rewrite_article(text)
        original_analysis = analyze_article(text)
        rewritten_analysis = analyze_article(rewritten)
        diff_html = generate_diff_html(text, rewritten)

        result = {
            "original_text": text,
            "rewritten_text": rewritten,
            "original_analysis": original_analysis,
            "rewritten_analysis": rewritten_analysis,
            "diff_html": diff_html
        }

    return render_template('rewrite.html', form=form, result=result)