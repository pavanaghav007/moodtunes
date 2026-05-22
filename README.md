# 🎵 MoodTunes v3 — AI Emotion Music Recommender

> Detect your emotion via webcam → get a curated playlist in Hindi, Punjabi, English & Spiritual

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)

---

## ✨ Features

| Feature | Details |
|---|---|
| 😄 Emotion Detection | Happy, Sad, Angry, Neutral, Surprised, Fearful, Disgusted |
| 🎵 Music Moods | Happy, Sad, Romantic, Angry, Passionate, Fearful, Spiritual |
| 🌍 Languages | Hindi · Punjabi · English · Spiritual |
| 🎧 Spotify | Real songs via Spotify API (optional) |
| 👤 Login/Signup | Personal account with detection history |
| 📊 Dashboard | Live chart, breakdown bars, session stats |
| 📄 PDF Export | Download your mood report |
| 🔊 Voice | App speaks detected emotion out loud |
| ⟳ Auto Mode | Auto-detect every 3/5/10 seconds |
| 📸 Snapshot | Save annotated face photo |

---

## 🚀 Quick Start (Local)

### 1 — Install Python 3.9-3.11
https://www.python.org/downloads/

### 2 — Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### 4 — Download AI model
```bash
python download_model.py
```

### 5 — Run app
```bash
python app.py
```

### 6 — Open browser
```
http://localhost:5000
```

---

## 🎧 Add Spotify API (Optional)

1. Go to https://developer.spotify.com/dashboard
2. Click **Create App**
3. Copy **Client ID** and **Client Secret**
4. Open `spotify_helper.py` and paste:
```python
SPOTIFY_CLIENT_ID     = 'paste_your_client_id_here'
SPOTIFY_CLIENT_SECRET = 'paste_your_client_secret_here'
```

---

## 🌍 Deploy on Render (FREE — Public URL)

### Step 1 — Push to GitHub
1. Create account at https://github.com
2. Create new repository: `moodtunes-app`
3. Upload all project files

### Step 2 — Deploy on Render
1. Create account at https://render.com
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Fill in:
   - **Build Command:** `pip install -r requirements.txt && python download_model.py`
   - **Start Command:** `gunicorn app:app`
5. Click **Deploy**
6. Get your public URL: `https://moodtunes-app.onrender.com`

### Step 3 — Add Spotify keys on Render (optional)
In Render dashboard → Environment → Add:
- `SPOTIFY_CLIENT_ID` = your key
- `SPOTIFY_CLIENT_SECRET` = your key

---

## 📁 Project Structure

```
moodtunes-app/
├── app.py                  ← Flask backend
├── models.py               ← Database models (User, Detection)
├── spotify_helper.py       ← Spotify API integration
├── download_model.py       ← Download AI model
├── music_data.json         ← 72 songs (Hindi/Punjabi/English/Spiritual)
├── requirements.txt
├── model/
│   ├── emotion_model.json
│   └── emotion_model.weights.h5
├── static/
│   ├── style.css           ← Dashboard styles
│   ├── auth.css            ← Login/Register styles
│   └── script.js           ← Frontend logic
└── templates/
    ├── index.html          ← Main dashboard
    ├── login.html          ← Login page
    └── register.html       ← Register page
```

---

## 🎭 Emotions Detected

| FER Model Output | Music Mood | Songs |
|---|---|---|
| Happy | 😄 Happy | Bollywood, Pop |
| Sad | 😢 Sad | Emotional Hindi, English |
| Angry | 😠 Angry | Punjabi Rap, Rock |
| Neutral | 😐 Neutral | Lofi, Chill |
| Surprise | 😲 Surprised | Upbeat, Exciting |
| Fear | 😨 Fearful | Calming, Peaceful |
| Disgust | 🤢 Disgusted | Slow Sad Songs |

---

## 🛠 Tech Stack

- **Backend:** Python, Flask, Flask-Login, SQLAlchemy
- **AI/ML:** TensorFlow, Keras, OpenCV, FER2013 model
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Database:** SQLite
- **Music:** Spotify API + Static JSON fallback
- **Deploy:** Gunicorn + Render.com

---

## 📄 License
MIT — Free to use and share
