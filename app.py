# ============================================================
# app.py  -  MoodTunes v3 FINAL
# Login, Signup, Emotion Detection, Spotify + Static Songs
# Hindi / English / Punjabi / Spiritual
# ============================================================

import cv2, numpy as np, json, base64, os, datetime, io
from flask import (Flask, render_template, request,
                   jsonify, send_file, redirect, url_for)
from tensorflow.keras.models import model_from_json
from tensorflow.keras.preprocessing.image import img_to_array
from models import db, User, Detection
from flask_login import (LoginManager, login_user,
                         logout_user, login_required, current_user)
from spotify_helper import get_spotify_songs

app = Flask(__name__)
app.config['SECRET_KEY']                     = 'moodtunes-secret-key-v3-2024'
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///moodtunes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

with app.app_context():
    db.create_all()

# ── Emotion config ─────────────────────────────────────────
# FER2013 has 7 classes
EMOTION_LABELS = ['Angry','Disgust','Fear','Happy','Neutral','Sad','Surprise']

# Map FER label → music_data key
FER_TO_MUSIC = {
    'Angry':    'angry',
    'Disgust':  'disgusted',
    'Fear':     'fearful',
    'Happy':    'happy',
    'Neutral':  'neutral',
    'Sad':      'sad',
    'Surprise': 'surprised',
}

# Nice display names + emoji for each music key
MOOD_META = {
    'happy':      {'label': 'Happy',      'emoji': '😄', 'color': '#f9d94e'},
    'sad':        {'label': 'Sad',        'emoji': '😢', 'color': '#5ba4f5'},
    'romantic':   {'label': 'Romantic',   'emoji': '💕', 'color': '#ff6eb4'},
    'angry':      {'label': 'Angry',      'emoji': '😠', 'color': '#ff5f5f'},
    'neutral':    {'label': 'Neutral',    'emoji': '😐', 'color': '#9090b8'},
    'surprised':  {'label': 'Surprised',  'emoji': '😲', 'color': '#d97cf5'},
    'passionate': {'label': 'Passionate', 'emoji': '🔥', 'color': '#ff9f3f'},
    'fearful':    {'label': 'Fearful',    'emoji': '😨', 'color': '#7ec8e3'},
    'spiritual':  {'label': 'Spiritual',  'emoji': '🙏', 'color': '#a8e6a3'},
    'disgusted':  {'label': 'Disgusted',  'emoji': '🤢', 'color': '#b5e550'},
}

# ── Model paths ────────────────────────────────────────────
MODEL_JSON    = os.path.join('model', 'emotion_model.json')
MODEL_WEIGHTS = os.path.join('model', 'emotion_model.weights.h5')
emotion_model = None

# ── Music data ─────────────────────────────────────────────
with open('music_data.json', 'r', encoding='utf-8') as f:
    MUSIC_DATA = json.load(f)

# ── Face detector ──────────────────────────────────────────
FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

HISTORY_FILE = 'detection_history.json'

# ── Session stats (reset on restart) ──────────────────────
_stats = {
    'total': 0,
    'counts': {e: 0 for e in EMOTION_LABELS},
    'confidences': [],
}


# ── Helpers ────────────────────────────────────────────────

def load_model():
    global emotion_model
    if emotion_model is not None:
        return True
    try:
        if not os.path.exists(MODEL_JSON) or not os.path.exists(MODEL_WEIGHTS):
            print("[WARN] Model files not found — DEMO mode (Happy always).")
            return False
        with open(MODEL_JSON, 'r') as f:
            emotion_model = model_from_json(f.read())
        emotion_model.load_weights(MODEL_WEIGHTS)
        print("[OK] Emotion model loaded successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Model load: {e}")
        return False


def save_history(entry):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            pass
    history = (history + [entry])[-500:]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)


def predict_emotion(frame_bgr):
    """Detect face → predict emotion → return results."""
    gray  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        return None, 0.0, frame_bgr, np.zeros(len(EMOTION_LABELS))

    # Use largest face
    x, y, w, h = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]

    # Draw detection box
    cv2.rectangle(frame_bgr, (x, y), (x+w, y+h), (124, 108, 255), 2)

    # Preprocess
    roi     = cv2.resize(gray[y:y+h, x:x+w], (64, 64))
    roi_arr = np.expand_dims(img_to_array(roi) / 255.0, axis=0)

    if emotion_model is None:
        # Demo mode
        scores     = np.array([0.05, 0.02, 0.03, 0.75, 0.08, 0.04, 0.03])
        emotion    = 'Happy'
        confidence = 0.75
    else:
        scores     = emotion_model.predict(roi_arr, verbose=0)[0]
        idx        = int(np.argmax(scores))
        emotion    = EMOTION_LABELS[idx]
        confidence = float(scores[idx])

    # Draw label
    meta  = MOOD_META.get(FER_TO_MUSIC.get(emotion, 'neutral'), {})
    label = f"{meta.get('emoji','')} {emotion}  {confidence*100:.0f}%"
    cv2.putText(frame_bgr, label, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (124, 108, 255), 2)

    return emotion, confidence, frame_bgr, scores


# ══════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login_page'))
    return render_template('index.html', user=current_user)


@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/register')
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))


# ══════════════════════════════════════════════════════════
#  AUTH API
# ══════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def api_register():
    data     = request.get_json()
    username = data.get('username', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({'message': 'Account created!', 'username': user.username})


@app.route('/api/login', methods=['POST'])
def api_login():
    data     = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user     = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user, remember=True)
        return jsonify({'message': f'Welcome back, {user.username}!',
                        'username': user.username})
    return jsonify({'error': 'Wrong username or password'}), 401


# ══════════════════════════════════════════════════════════
#  DETECT API
# ══════════════════════════════════════════════════════════

@app.route('/detect', methods=['POST'])
@login_required
def detect():
    load_model()
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image received'}), 400

    # Decode image
    try:
        raw = data['image']
        if ',' in raw:
            raw = raw.split(',')[1]
        frame = cv2.imdecode(
            np.frombuffer(base64.b64decode(raw), dtype=np.uint8),
            cv2.IMREAD_COLOR)
    except Exception as e:
        return jsonify({'error': f'Image decode failed: {e}'}), 400

    if frame is None:
        return jsonify({'error': 'Could not read image'}), 400

    # Predict
    emotion, conf, annotated, scores = predict_emotion(frame)

    if emotion is None:
        return jsonify({
            'emotion': None,
            'message': 'No face detected — centre your face in the frame',
            'songs': []})

    # Build response data
    music_key = FER_TO_MUSIC.get(emotion, 'neutral')
    meta      = MOOD_META.get(music_key, {'label': emotion, 'emoji': '🎵', 'color': '#7c6cff'})

    # Update session stats
    _stats['total'] += 1
    _stats['counts'][emotion] = _stats['counts'].get(emotion, 0) + 1
    _stats['confidences'].append(round(conf * 100, 1))

    # Save history
    entry = {
        'timestamp':  datetime.datetime.now().isoformat(),
        'emotion':    emotion,
        'mood_key':   music_key,
        'confidence': round(conf * 100, 1),
        'user':       current_user.username,
        'scores':     {EMOTION_LABELS[i]: round(float(scores[i])*100, 1)
                       for i in range(len(EMOTION_LABELS))}
    }
    save_history(entry)

    # Save to DB
    db.session.add(Detection(
        user_id=current_user.id,
        emotion=emotion,
        confidence=round(conf * 100, 1)))
    db.session.commit()

    # Songs — try Spotify first, fall back to static
    songs = get_spotify_songs(music_key, limit=6)
    if not songs:
        songs = MUSIC_DATA.get(music_key, [])

    # Encode annotated frame
    _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 88])
    img_b64 = 'data:image/jpeg;base64,' + base64.b64encode(buf).decode()

    breakdown = {EMOTION_LABELS[i]: round(float(scores[i])*100, 1)
                 for i in range(len(EMOTION_LABELS))}

    avg_conf = round(sum(_stats['confidences']) / len(_stats['confidences']), 1)
    dominant = max(_stats['counts'], key=_stats['counts'].get)

    return jsonify({
        'emotion':    emotion,
        'mood_key':   music_key,
        'mood_label': meta['label'],
        'emoji':      meta['emoji'],
        'color':      meta['color'],
        'confidence': round(conf * 100, 1),
        'breakdown':  breakdown,
        'songs':      songs,
        'annotated_image': img_b64,
        'log_entry':  entry,
        'stats': {
            'total':    _stats['total'],
            'counts':   _stats['counts'],
            'avg_conf': avg_conf,
            'dominant': dominant,
        }
    })


# ══════════════════════════════════════════════════════════
#  UTILITY ROUTES
# ══════════════════════════════════════════════════════════

@app.route('/history')
@login_required
def get_history():
    if not os.path.exists(HISTORY_FILE):
        return jsonify([])
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    global _stats
    _stats = {'total': 0, 'counts': {e: 0 for e in EMOTION_LABELS}, 'confidences': []}
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return jsonify({'message': 'History cleared'})


@app.route('/save-snapshot', methods=['POST'])
@login_required
def save_snapshot():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image'}), 400
    raw = data['image']
    if ',' in raw:
        raw = raw.split(',')[1]
    os.makedirs('snapshots', exist_ok=True)
    fname = f"snap_{current_user.username}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    with open(os.path.join('snapshots', fname), 'wb') as f:
        f.write(base64.b64decode(raw))
    return jsonify({'message': f'Saved: {fname}'})


@app.route('/export-pdf')
@login_required
def export_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                        Spacer, Table, TableStyle, HRFlowable)
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
    except ImportError:
        return 'Run: pip install reportlab', 500

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)

    counts   = {}
    for e in history:
        k = e.get('emotion', '?')
        counts[k] = counts.get(k, 0) + 1
    dominant = max(counts, key=counts.get) if counts else 'None'
    avg_conf = round(sum(e.get('confidence', 0) for e in history) / len(history), 1) if history else 0

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
          rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = []

    P = lambda txt, **kw: Paragraph(txt, ParagraphStyle('x', **kw))
    TS = TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), colors.HexColor('#1a1a32')),
        ('TEXTCOLOR',     (0,0),(-1,0), colors.HexColor('#a98fff')),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), 9),
        ('TEXTCOLOR',     (0,1),(-1,-1), colors.HexColor('#ccccee')),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('GRID',          (0,0),(-1,-1), 0.5, colors.HexColor('#2a2a44')),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
    ])

    story += [
        P('MoodTunes', fontSize=28, fontName='Helvetica-Bold',
          textColor=colors.HexColor('#7c6cff'), spaceAfter=4),
        P(f'Report for {current_user.username}', fontSize=13,
          textColor=colors.HexColor('#9090b8'), spaceAfter=4),
        P(f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}",
          fontSize=10, textColor=colors.HexColor('#555566'), spaceAfter=16),
        HRFlowable(width='100%', thickness=1, color=colors.HexColor('#2a2a44')),
        Spacer(1, 0.4*cm),
    ]

    H2 = dict(fontSize=14, fontName='Helvetica-Bold',
              textColor=colors.HexColor('#eeeeff'), spaceAfter=10, spaceBefore=10)

    # Summary
    story.append(P('Summary', **H2))
    t = Table([['Total Detections','Dominant Mood','Avg Confidence'],
               [str(len(history)), dominant, f'{avg_conf}%']],
              colWidths=[5.5*cm]*3)
    t.setStyle(TS); story += [t, Spacer(1, 0.4*cm)]

    # Breakdown
    if counts:
        story.append(P('Emotion Breakdown', **H2))
        rows = [['Emotion','Count','%']]
        for emo, cnt in sorted(counts.items(), key=lambda x:-x[1]):
            rows.append([emo, str(cnt), f"{round(cnt/len(history)*100,1)}%"])
        bt = Table(rows, colWidths=[5.5*cm]*3); bt.setStyle(TS)
        story += [bt, Spacer(1, 0.4*cm)]

    # Recent
    if history:
        story.append(P('Recent Detections (Last 20)', **H2))
        rows = [['Time','Emotion','Confidence']]
        for e in history[-20:][::-1]:
            rows.append([e.get('timestamp','')[:19].replace('T',' '),
                         e.get('emotion','?'), f"{e.get('confidence',0)}%"])
        dt = Table(rows, colWidths=[7*cm, 4.5*cm, 4.5*cm]); dt.setStyle(TS)
        story.append(dt)

    story += [
        Spacer(1, 0.8*cm),
        HRFlowable(width='100%', thickness=1, color=colors.HexColor('#2a2a44')),
        P('MoodTunes · Flask + TensorFlow + OpenCV · FER2013 Model',
          fontSize=8, textColor=colors.HexColor('#555566'), alignment=1, spaceBefore=6),
    ]

    doc.build(story); buf.seek(0)
    fname = f"moodtunes_{current_user.username}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return send_file(buf, as_attachment=True, download_name=fname, mimetype='application/pdf')


if __name__ == '__main__':
    print("=" * 55)
    print("  MoodTunes v3  |  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)