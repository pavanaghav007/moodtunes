// MoodTunes v3  -  Complete Frontend Script

const EMOJIS = {Happy:'😄',Sad:'😢',Angry:'😠',Neutral:'😐',Surprise:'😲',Fear:'😨',Disgust:'🤢'};
const CSS_CLS = {Happy:'happy',Sad:'sad',Angry:'angry',Neutral:'neutral',Surprise:'surprise',Fear:'fear',Disgust:'disgust'};
const BK_COL  = {Angry:'#ff5f5f',Disgust:'#b5e550',Fear:'#7ec8e3',Happy:'#f9d94e',Neutral:'#9090b8',Sad:'#5ba4f5',Surprise:'#d97cf5'};
const CHART_COL = {Happy:'#f9d94e',Sad:'#5ba4f5',Angry:'#ff5f5f',Neutral:'#9090b8',Surprise:'#d97cf5',Fear:'#7ec8e3',Disgust:'#b5e550'};
const PLAT_ICON = {YouTube:'▶',Spotify:'♫'};

// DOM refs
const $ = id => document.getElementById(id);
const video      = $('video');
const canvas     = $('canvas');
const snapshot   = $('snapshot');
const detectBtn  = $('detectBtn');
const scanOv     = $('scanOv');
const faceTag    = $('faceTag');
const statusChip = $('statusChip');
const emotionCard= $('emotionCard');
const emoEmoji   = $('emoEmoji');
const emoName    = $('emoName');
const confBar    = $('confBar');
const confPct    = $('confPct');
const bkBars     = $('bkBars');
const trackList  = $('trackList');
const songsEmpty = $('songsEmpty');
const songCount  = $('songCount');
const logList    = $('logList');
const logEmpty   = $('logEmpty');
const saveBtn    = $('saveBtn');
const autoBtn    = $('autoBtn');
const autoRow    = $('autoRow');
const autoSel    = $('autoSel');
const stTotal    = $('stTotal');
const stDominant = $('stDominant');
const stConf     = $('stConf');
const histCount  = $('histCount');
const chartEmpty = $('chartEmpty');

// State
let lastSnapshot = null;
let autoTimer    = null;
let isAuto       = false;
let voiceMuted   = false;
let histChart    = null;
let histData     = [];
let activeLang   = 'all';
let allSongs     = [];

// ── Chart ──────────────────────────────────────────────────
function initChart() {
  const ctx = $('histChart').getContext('2d');
  histChart = new Chart(ctx, {
    type: 'bar',
    data: { labels:[], datasets:[{label:'Confidence %',data:[],backgroundColor:[],borderRadius:5,borderSkipped:false}] },
    options: {
      responsive:true, maintainAspectRatio:false, animation:{duration:400},
      plugins:{ legend:{display:false}, tooltip:{callbacks:{
        title: i => histData[i[0].dataIndex]?.emotion || '',
        label: i => ` ${i.raw}% confidence`
      }}},
      scales:{
        x:{ticks:{color:'#3a3a58',font:{size:9}},grid:{color:'rgba(255,255,255,0.03)'}},
        y:{min:0,max:100,ticks:{color:'#3a3a58',font:{size:9},callback:v=>v+'%'},grid:{color:'rgba(255,255,255,0.03)'}}
      }
    }
  });
}

function pushChart(emotion, conf) {
  if (histChart.data.labels.length >= 14) {
    histChart.data.labels.shift();
    histChart.data.datasets[0].data.shift();
    histChart.data.datasets[0].backgroundColor.shift();
  }
  histChart.data.labels.push(emotion.slice(0,3));
  histChart.data.datasets[0].data.push(conf);
  histChart.data.datasets[0].backgroundColor.push(CHART_COL[emotion]||'#7c6cff');
  histChart.update();
  chartEmpty.style.display = 'none';
  histCount.textContent = histChart.data.labels.length + ' records';
}

// ── Camera ─────────────────────────────────────────────────
async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video:{facingMode:'user',width:{ideal:640},height:{ideal:480}}, audio:false});
    video.srcObject = stream;
    video.style.display = 'block';
  } catch(e) {
    $('camErr').style.display = 'block';
    detectBtn.disabled = true;
  }
}

function captureFrame() {
  canvas.width  = video.videoWidth  || 640;
  canvas.height = video.videoHeight || 480;
  canvas.getContext('2d').drawImage(video, 0, 0);
  return canvas.toDataURL('image/jpeg', 0.88);
}

// ── Detect ─────────────────────────────────────────────────
async function detectEmotion() {
  detectBtn.disabled = true;
  scanOv.classList.add('active');
  faceTag.style.display  = 'none';
  snapshot.style.display = 'none';
  video.style.display    = 'block';
  setStatus('Detecting…','detecting');

  try {
    const res  = await fetch('/detect', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({image: captureFrame()})
    });
    const data = await res.json();
    scanOv.classList.remove('active');

    if (data.error) { setStatus('Error',''); toast('❌ ' + data.error); detectBtn.disabled=false; return; }

    if (!data.emotion) {
      setStatus('No face','');
      toast('👤 ' + (data.message||'No face detected'));
      detectBtn.disabled = false; return;
    }

    // Show snapshot
    if (data.annotated_image) {
      lastSnapshot = data.annotated_image;
      snapshot.src = data.annotated_image;
      snapshot.style.display = 'block';
      video.style.display    = 'none';
      saveBtn.style.display  = 'flex';
    }

    // Face tag
    $('faceTagEmoji').textContent = data.emoji || EMOJIS[data.emotion] || '🎵';
    $('faceTagLabel').textContent = data.mood_label || data.emotion;
    faceTag.style.display = 'flex';

    setStatus(data.mood_label || data.emotion, 'ok');
    updateEmotionCard(data);
    if (data.breakdown) renderBreakdown(data.breakdown);
    allSongs = data.songs || [];
    renderSongs(allSongs);
    if (data.stats)     updateStats(data.stats);
    pushChart(data.emotion, data.confidence);
    if (data.log_entry) addLog(data.log_entry);
    highlightMoodChip(data.mood_key);
    if (!voiceMuted)    speakEmotion(data.mood_label || data.emotion, data.confidence);

  } catch(e) {
    scanOv.classList.remove('active');
    setStatus('Error','');
    toast('❌ Connection failed — is Flask running?');
  }
  detectBtn.disabled = false;
}

// ── Emotion card ───────────────────────────────────────────
function updateEmotionCard(data) {
  emoEmoji.textContent = data.emoji || EMOJIS[data.emotion] || '🎵';
  emoName.textContent  = data.mood_label || data.emotion;
  confBar.style.width  = data.confidence + '%';
  confPct.textContent  = data.confidence + '%';

  emotionCard.className = 'card emotion-card';
  const cls = data.mood_key || CSS_CLS[data.emotion] || 'neutral';
  emotionCard.classList.add(cls);

  document.querySelectorAll('.mp').forEach(p => {
    p.className = 'mp';
    if (p.dataset.e === data.emotion)
      p.classList.add('active-' + (CSS_CLS[data.emotion]||'neutral'));
  });
}

// ── Breakdown bars ─────────────────────────────────────────
function renderBreakdown(breakdown) {
  bkBars.innerHTML = '';
  Object.entries(breakdown).sort((a,b)=>b[1]-a[1]).forEach(([emo,pct]) => {
    const row = document.createElement('div');
    row.className = 'bk-row';
    row.innerHTML = `<span class="bk-label">${emo}</span>
      <div class="bk-track"><div class="bk-fill" style="width:${pct}%;background:${BK_COL[emo]||'#7c6cff'}"></div></div>
      <span class="bk-val">${pct}%</span>`;
    bkBars.appendChild(row);
  });
}

// ── Songs ──────────────────────────────────────────────────
function renderSongs(songs) {
  trackList.innerHTML = '';
  // Filter by language
  const filtered = activeLang === 'all'
    ? songs
    : songs.filter(s => (s.language||'').toLowerCase() === activeLang.toLowerCase());

  if (!filtered.length) {
    songsEmpty.style.display = 'block';
    songCount.textContent    = '';
    return;
  }
  songsEmpty.style.display = 'none';
  songCount.textContent    = filtered.length + ' tracks';

  filtered.forEach((song, i) => {
    const li = document.createElement('li');
    const a  = document.createElement('a');
    a.href = song.url; a.target='_blank'; a.rel='noopener noreferrer'; a.className='ti';
    a.innerHTML = `
      <span class="ti-num">${String(i+1).padStart(2,'0')}</span>
      <div class="ti-thumb">${PLAT_ICON[song.platform]||'♪'}</div>
      <div class="ti-meta">
        <div class="ti-title">${song.title}</div>
        <div class="ti-artist">${song.artist}</div>
      </div>
      <div class="ti-right">
        <span class="ti-plat">${song.platform}</span>
        <span class="ti-lang">${song.language||''}</span>
      </div>`;
    li.appendChild(a);
    trackList.appendChild(li);
  });
}

function setLang(btn) {
  document.querySelectorAll('.lf-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeLang = btn.dataset.lang;
  renderSongs(allSongs);
}

// ── Stats ──────────────────────────────────────────────────
function updateStats(stats) {
  stTotal.textContent    = stats.total    || 0;
  stDominant.textContent = stats.dominant || '—';
  stConf.textContent     = stats.avg_conf ? stats.avg_conf + '%' : '—';
}

// ── Log entry ──────────────────────────────────────────────
function addLog(entry) {
  histData.unshift(entry);
  logEmpty.style.display = 'none';
  const li   = document.createElement('li');
  li.className = 'li';
  const time = new Date(entry.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  li.innerHTML = `<span class="li-emoji">${EMOJIS[entry.emotion]||'🎵'}</span>
    <div class="li-meta"><div class="li-emotion">${entry.emotion}</div><div class="li-time">${time}</div></div>
    <span class="li-conf">${entry.confidence}%</span>`;
  logList.prepend(li);
  while (logList.children.length > 20) logList.removeChild(logList.lastChild);
}

// ── Mood chip highlight ────────────────────────────────────
function highlightMoodChip(moodKey) {
  document.querySelectorAll('.mc').forEach(c => {
    c.classList.toggle('active', c.dataset.key === moodKey);
  });
}

// ── Voice ──────────────────────────────────────────────────
function speakEmotion(emotion, conf) {
  window.speechSynthesis.cancel();
  const msgs = {
    Happy:      `You look Happy with ${conf} percent confidence! Here are some upbeat tracks for you!`,
    Sad:        `You seem Sad. Here are some soothing songs to comfort you.`,
    Angry:      `You look Angry! Here is some powerful music to channel your energy.`,
    Neutral:    `You look calm. Here is some chill music for you.`,
    Surprised:  `You look Surprised! Here are some exciting tracks!`,
    Romantic:   `You are in a Romantic mood! Here are some love songs for you.`,
    Passionate: `You feel Passionate! Here is some motivating music!`,
    Fearful:    `You seem anxious. Here is some calming music to help.`,
    Spiritual:  `You are in a Spiritual mood. Here are some peaceful tracks.`,
    Disgusted:  `Here is some music to help lift your mood.`,
  };
  const utt   = new SpeechSynthesisUtterance(msgs[emotion] || `Detected: ${emotion}. Enjoy your playlist!`);
  utt.rate    = 0.95; utt.pitch = 1.05; utt.volume = 1;
  const voice = speechSynthesis.getVoices().find(v => v.lang.startsWith('en'));
  if (voice) utt.voice = voice;
  speechSynthesis.speak(utt);
}

function toggleMute() {
  voiceMuted = !voiceMuted;
  const btn  = $('muteBtn');
  btn.textContent = voiceMuted ? '🔇' : '🔊';
  btn.classList.toggle('active', voiceMuted);
  if (voiceMuted) speechSynthesis.cancel();
  toast(voiceMuted ? '🔇 Voice muted' : '🔊 Voice on');
}

// ── Snapshot ───────────────────────────────────────────────
async function saveSnapshot() {
  if (!lastSnapshot) return;
  const a = document.createElement('a');
  a.href = lastSnapshot; a.download = `moodtunes_${Date.now()}.jpg`; a.click();
  try { await fetch('/save-snapshot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:lastSnapshot})}); } catch(e){}
  toast('📸 Snapshot saved!');
}

// ── Auto detect ────────────────────────────────────────────
function toggleAuto() {
  isAuto = !isAuto;
  autoBtn.classList.toggle('active', isAuto);
  autoRow.style.display = isAuto ? 'flex' : 'none';
  if (isAuto) {
    detectEmotion();
    const ms = parseInt(autoSel.value) || 5000;
    autoTimer = setInterval(() => { if (!detectBtn.disabled) detectEmotion(); }, ms);
    toast(`⟳ Auto every ${ms/1000}s`);
  } else {
    clearInterval(autoTimer); autoTimer = null;
    toast('Auto stopped');
  }
}
autoSel.addEventListener('change', () => {
  if (isAuto) { clearInterval(autoTimer); const ms=parseInt(autoSel.value)||5000; autoTimer=setInterval(()=>{if(!detectBtn.disabled)detectEmotion();},ms); }
});

// ── PDF / Clear ────────────────────────────────────────────
function exportPDF() { toast('📄 Generating PDF…'); window.open('/export-pdf','_blank'); }

async function clearHistory() {
  await fetch('/history/clear',{method:'POST'});
  histData=[]; logList.innerHTML=''; logEmpty.style.display='block';
  stTotal.textContent='0'; stDominant.textContent='—'; stConf.textContent='—';
  histChart.data.labels=[]; histChart.data.datasets[0].data=[]; histChart.data.datasets[0].backgroundColor=[];
  histChart.update(); histCount.textContent='0 records'; chartEmpty.style.display='block';
  toast('🗑 History cleared');
}

// ── Status / Toast ─────────────────────────────────────────
function setStatus(txt, cls) {
  statusChip.textContent = txt;
  statusChip.className   = 'chip' + (cls ? ' '+cls : '');
}

function toast(msg) {
  const t = document.createElement('div');
  t.textContent = msg;
  Object.assign(t.style,{
    position:'fixed',bottom:'24px',left:'50%',transform:'translateX(-50%)',
    background:'rgba(14,14,28,.94)',backdropFilter:'blur(14px)',
    border:'1px solid rgba(255,255,255,.1)',color:'#eeeeff',
    padding:'.5rem 1.2rem',borderRadius:'99px',fontSize:'.8rem',
    fontWeight:'600',zIndex:'9999',fontFamily:"'Space Grotesk',sans-serif",
    whiteSpace:'nowrap',pointerEvents:'none'
  });
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

// ── Init ───────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  startCamera();
  initChart();
  chartEmpty.style.display = 'block';
});
