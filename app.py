# ═══════════════════════════════════════════════════════════
#  🏸 BALL BADMINTON — COMPLETE LIVE SCOREBOARD
#  Admin: full control | Viewer: OTP read-only access
#  Data saved to JSON | No lag | Hidden credentials
# ═══════════════════════════════════════════════════════════
import streamlit as st
import json, os, random, string
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

# ─── CONSTANTS ───────────────────────────────────────────
SET_POINTS          = 35
COURT_CHANGE_PTS    = [9, 18, 27]
PLAYERS             = 5
TOTAL_PLAYERS       = 10
DATA_FILE           = "match_data.json"

# ─── CREDENTIALS (hidden — not shown in UI) ──────────────
ADMIN_USER  = "Ballbadminton"
ADMIN_PASS  = "partha@2025"
VIEWER_OTP_LENGTH = 6

# ─── PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="Ball Badminton Live",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── THEME CSS ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --bg1: #0a0e1a;
  --bg2: #0f1629;
  --card: rgba(255,255,255,0.04);
  --border: rgba(255,255,255,0.08);
  --accent: #f97316;
  --accent2: #3b82f6;
  --green: #22c55e;
  --red: #ef4444;
  --gold: #f59e0b;
  --text: #e2e8f0;
  --muted: rgba(226,232,240,0.5);
}

html, body, .stApp {
    background: linear-gradient(160deg, var(--bg1) 0%, var(--bg2) 100%) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    min-height: 100vh;
}
.stApp .block-container { max-width: 1380px; padding: 1.2rem 2rem; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1220 0%, #0a0e1a 100%) !important;
    border-right: 1px solid rgba(249,115,22,0.3) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* All buttons */
.stButton > button {
    background: linear-gradient(135deg, #f97316, #ea580c) !important;
    color: #fff !important;
    border: none !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 11px 18px !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(249,115,22,0.3) !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(249,115,22,0.45) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }

/* Blue variant buttons via class */
.btn-blue .stButton > button {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    box-shadow: 0 4px 15px rgba(59,130,246,0.3) !important;
}
.btn-green .stButton > button {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    box-shadow: 0 4px 15px rgba(34,197,94,0.3) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(249,115,22,0.15) !important;
}

/* Containers */
[data-testid="stContainer"] {
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 18px !important;
    background: var(--card) !important;
    backdrop-filter: blur(12px) !important;
}

/* Score display */
.score-giant {
    font-family: 'Rajdhani', sans-serif;
    font-size: 96px;
    font-weight: 700;
    line-height: 1;
    color: #fff;
    text-shadow: 0 0 40px rgba(249,115,22,0.4);
}
.score-giant.serving { color: var(--accent); }
.team-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.set-score { font-size: 18px; opacity: 0.7; margin-top: 4px; }

/* Badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.b-orange  { background: rgba(249,115,22,0.2); color: #f97316; border:1px solid rgba(249,115,22,0.3); }
.b-blue    { background: rgba(59,130,246,0.2); color: #60a5fa; border:1px solid rgba(59,130,246,0.3); }
.b-green   { background: rgba(34,197,94,0.2);  color: #4ade80; border:1px solid rgba(34,197,94,0.3); }
.b-red     { background: rgba(239,68,68,0.2);  color: #f87171; border:1px solid rgba(239,68,68,0.3); }
.b-gold    { background: rgba(245,158,11,0.2); color: #fbbf24; border:1px solid rgba(245,158,11,0.3); }

/* Stat card */
.stat-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.stat-num  { font-family:'Rajdhani',sans-serif; font-size:36px; font-weight:700; color:var(--accent); }
.stat-lbl  { font-size:11px; opacity:0.55; text-transform:uppercase; letter-spacing:1px; margin-top:2px; }

/* Events feed */
.event-item {
    font-size: 12px;
    padding: 6px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: var(--muted);
}
.event-item:first-child { color: var(--text); }

/* Winner banner */
.winner-wrap {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    border-radius: 20px;
    padding: 24px;
    text-align: center;
    font-family: 'Rajdhani', sans-serif;
    font-size: 32px;
    font-weight: 700;
    box-shadow: 0 8px 32px rgba(245,158,11,0.4);
    margin-bottom: 16px;
}

/* Login card */
.login-wrap {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 36px;
}

/* OTP display */
.otp-display {
    font-family: 'Rajdhani', monospace;
    font-size: 48px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 8px;
    text-align: center;
    background: rgba(249,115,22,0.1);
    border: 2px dashed rgba(249,115,22,0.4);
    border-radius: 16px;
    padding: 20px;
    margin: 16px 0;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 16px 0;
}

/* Metric override */
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; }

/* Multiselect */
.stMultiSelect > div { background: rgba(255,255,255,0.06) !important; border-radius:10px !important; }

/* Radio */
.stRadio > div { gap: 12px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(249,115,22,0.4); border-radius:4px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  DATA PERSISTENCE
# ═══════════════════════════════════════════════════════════
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"match_history": [], "tournament_bracket": [], "tournament_info": {}, "current_otp": None}

def save_data(data: dict):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save data: {e}")

def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=VIEWER_OTP_LENGTH))


# ═══════════════════════════════════════════════════════════
#  MATCH STATE
# ═══════════════════════════════════════════════════════════
@dataclass
class MatchState:
    teamA: str; teamB: str
    all_playersA: List[str]; all_playersB: List[str]
    playersA: List[str]; playersB: List[str]
    orderA: List[str]; orderB: List[str]
    set_no: int; setsA: int; setsB: int
    scoreA: int; scoreB: int
    serving_team: str; hand: str; side_swapped: bool
    current_server_A: Optional[str]; current_server_B: Optional[str]
    next_idx_A: int; next_idx_B: int
    subs_left_A: int; subs_left_B: int
    timeouts_left_A: int; timeouts_left_B: int
    milestones_done: Dict[int, bool]
    history: List[Dict[str, Any]]
    events: List[str]
    match_over: bool; winner: Optional[str]
    points_per_set_A: List[int]; points_per_set_B: List[int]
    player_points_A: Dict[str, int]; player_points_B: Dict[str, int]
    start_time: str; end_time: Optional[str]
    match_id: str
    tournament_name: Optional[str]; round_name: Optional[str]

def default_players(prefix): return [f"{prefix}{i+1}" for i in range(TOTAL_PLAYERS)]
def safe_name(s, fb): s = (s or "").strip(); return s if s else fb
def unique_ok(lst): return len(set(lst)) == len(lst)
def clamp_idx(i, n): return i if 0 <= i < n else 0
def cyclic_next(i, n): return (i + 1) % n

def build_order(p5, idxs):
    if len(p5) != PLAYERS or len(idxs) != PLAYERS: return []
    out = []
    for idx in idxs:
        if not (1 <= idx <= PLAYERS): return []
        out.append(p5[idx - 1])
    return out

def milestone_hit(sA, sB, done):
    for p in COURT_CHANGE_PTS:
        if not done.get(p, False) and (sA == p or sB == p): return p
    return None

def init_match(tA, tB, allA, allB, pA, pB, oA, oB, first, t_name=None, r_name=None):
    if len(oA) != PLAYERS: oA = pA[:]
    if len(oB) != PLAYERS: oB = pB[:]
    cA, cB, nA, nB = (oA[0], None, 1, 0) if first == "A" else (None, oB[0], 0, 1)
    return MatchState(
        teamA=tA, teamB=tB, all_playersA=allA, all_playersB=allB,
        playersA=pA, playersB=pB, orderA=oA, orderB=oB,
        set_no=1, setsA=0, setsB=0, scoreA=0, scoreB=0,
        serving_team=first, hand="R", side_swapped=False,
        current_server_A=cA, current_server_B=cB,
        next_idx_A=nA, next_idx_B=nB,
        subs_left_A=3, subs_left_B=3, timeouts_left_A=1, timeouts_left_B=1,
        milestones_done={9: False, 18: False, 27: False},
        history=[], events=[f"Match started — First serve: {tA if first=='A' else tB}"],
        match_over=False, winner=None,
        points_per_set_A=[], points_per_set_B=[],
        player_points_A={p: 0 for p in pA}, player_points_B={p: 0 for p in pB},
        start_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        end_time=None, match_id=datetime.now().strftime("%Y%m%d%H%M%S"),
        tournament_name=t_name, round_name=r_name
    )

def snap(s): return asdict(s)
def restore(d): return MatchState(**d)


# ═══════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ═══════════════════════════════════════════════════════════
_data = load_data()
for k, v in [
    ("role", None),           # "admin" | "viewer" | None
    ("setup_done", False),
    ("match", None),
    ("active_tab", "🏸 Score"),
    ("match_history", _data.get("match_history", [])),
    ("tournament_bracket", _data.get("tournament_bracket", [])),
    ("tournament_info", _data.get("tournament_info", {})),
    ("current_otp", _data.get("current_otp")),
    ("setup", {
        "teamA": "Team A", "teamB": "Team B",
        "all_playersA": default_players("A"), "all_playersB": default_players("B"),
        "main_playersA": [f"A{i+1}" for i in range(PLAYERS)],
        "main_playersB": [f"B{i+1}" for i in range(PLAYERS)],
        "orderA_idx": [1,2,3,4,5], "orderB_idx": [1,2,3,4,5],
        "firstServe": "A", "tournament_name": "", "round_name": ""
    }),
]:
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.setup_done and st.session_state.match is None:
    st.session_state.setup_done = False


# ═══════════════════════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════════════════════
if st.session_state.role is None:
    st.markdown("""
    <div style='text-align:center;padding:32px 0 16px'>
        <div style='font-size:72px;margin-bottom:8px'>🏸</div>
        <div style='font-family:Rajdhani,sans-serif;font-size:42px;font-weight:700;letter-spacing:2px'>BALL BADMINTON</div>
        <div style='opacity:0.5;font-size:14px;margin-top:4px'>Live Scoreboard System</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        tab_admin, tab_viewer = st.tabs(["🔐 Admin Login", "👁️ Viewer Access"])

        with tab_admin:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            uname = st.text_input("Username", placeholder="Enter username", key="login_u")
            pw    = st.text_input("Password", type="password", placeholder="Enter password", key="login_p")
            if st.button("🔓 Login as Admin", use_container_width=True, key="admin_login"):
                if uname == ADMIN_USER and pw == ADMIN_PASS:
                    st.session_state.role = "admin"
                    st.success("✅ Welcome, Admin!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

        with tab_viewer:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.info("Enter the OTP shared by the Admin to view the live score.")
            otp_input = st.text_input("Enter OTP", placeholder="6-digit code", max_chars=6, key="otp_input")
            if st.button("👁️ View Score", use_container_width=True, key="viewer_login"):
                if st.session_state.current_otp and otp_input.strip() == str(st.session_state.current_otp):
                    st.session_state.role = "viewer"
                    st.success("✅ Access granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid or expired OTP")
    st.stop()


# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
is_admin = st.session_state.role == "admin"

with st.sidebar:
    st.markdown("""
    <div style='padding:12px 0 8px'>
        <div style='font-family:Rajdhani,sans-serif;font-size:22px;font-weight:700'>🏸 Ball Badminton</div>
        <div style='font-size:11px;opacity:0.4;margin-top:2px'>Live Scoreboard</div>
    </div>
    """, unsafe_allow_html=True)

    role_badge = "<span class='badge b-orange'>ADMIN</span>" if is_admin else "<span class='badge b-blue'>VIEWER</span>"
    st.markdown(f"Role: {role_badge}", unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    nav_items = ["🏸 Score", "📊 Stats", "🏆 Tournament", "📜 History"]
    if is_admin:
        nav_items.append("⚙️ Admin")

    for t in nav_items:
        active = st.session_state.active_tab == t
        if st.button(t, use_container_width=True, key=f"nav_{t}",
                     help=f"Go to {t}"):
            st.session_state.active_tab = t
            st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if st.session_state.match and st.session_state.setup_done:
        m = st.session_state.match
        st.markdown(f"""
        <div style='font-size:12px;opacity:0.6;line-height:1.8'>
            <b style='opacity:1;font-size:13px'>{m.teamA} vs {m.teamB}</b><br>
            Set {m.set_no}/3 &nbsp;·&nbsp; {m.setsA}–{m.setsB} sets<br>
            Score: {m.scoreA}–{m.scoreB}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if is_admin and st.button("🔄 New Match", use_container_width=True, key="new_match"):
        st.session_state.setup_done = False
        st.session_state.match = None
        st.session_state.active_tab = "🏸 Score"
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True, key="logout"):
        st.session_state.role = None
        st.session_state.active_tab = "🏸 Score"
        st.rerun()

active_tab = st.session_state.active_tab


# ═══════════════════════════════════════════════════════════
#  VIEWER — READ ONLY SCORE VIEW
# ═══════════════════════════════════════════════════════════
if not is_admin:
    st.markdown("## 🏸 Live Score — Viewer Mode")
    if not st.session_state.setup_done or not st.session_state.match:
        st.info("⏳ No match in progress. Check back soon!")
        st.stop()

    m = st.session_state.match
    if m.tournament_name:
        st.markdown(f"<div style='text-align:center;opacity:0.6;font-size:14px;margin-bottom:12px'>🏆 {m.tournament_name} {('· ' + m.round_name) if m.round_name else ''}</div>", unsafe_allow_html=True)

    if m.match_over:
        st.markdown(f"<div class='winner-wrap'>🏆 {m.teamA if m.winner=='A' else m.teamB} Wins!</div>", unsafe_allow_html=True)

    with st.container(border=True):
        lt = "B" if m.side_swapped else "A"
        rt = "A" if m.side_swapped else "B"
        tn = lambda t: m.teamA if t=="A" else m.teamB
        ts = lambda t: m.scoreA if t=="A" else m.scoreB
        ss = lambda t: m.setsA if t=="A" else m.setsB

        c1, c2, c3 = st.columns([1, 0.25, 1])
        with c1:
            sicon = "🟠 " if m.serving_team == lt else ""
            st.markdown(f"<div class='team-title'>{sicon}{tn(lt)}</div>", unsafe_allow_html=True)
            cls = "serving" if m.serving_team == lt else ""
            st.markdown(f"<div class='score-giant {cls}'>{ts(lt)}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='set-score'>Sets: {ss(lt)}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='height:55px'></div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;opacity:0.4;font-size:24px;font-weight:700'>vs</div>", unsafe_allow_html=True)
        with c3:
            sicon = "🟠 " if m.serving_team == rt else ""
            st.markdown(f"<div class='team-title'>{sicon}{tn(rt)}</div>", unsafe_allow_html=True)
            cls = "serving" if m.serving_team == rt else ""
            st.markdown(f"<div class='score-giant {cls}'>{ts(rt)}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='set-score'>Sets: {ss(rt)}</div>", unsafe_allow_html=True)

        st.markdown(f"<div style='text-align:center;opacity:0.4;font-size:12px;margin-top:10px'>Set {m.set_no}/3 · Target {SET_POINTS} · Court change at 9, 18, 27</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Current Server", (m.current_server_A if m.serving_team=="A" else m.current_server_B) or "-")
    with c2:
        st.metric("Serving Team", m.teamA if m.serving_team=="A" else m.teamB)

    if m.points_per_set_A:
        st.markdown("**Set History**")
        cols = st.columns(len(m.points_per_set_A))
        for i, (a, b) in enumerate(zip(m.points_per_set_A, m.points_per_set_B)):
            with cols[i]:
                st.markdown(f"<div class='stat-box'><div style='font-size:11px;opacity:0.5'>Set {i+1}</div><div style='font-size:22px;font-weight:700'>{a}–{b}</div></div>", unsafe_allow_html=True)

    st.markdown("**Live Events**")
    with st.container(border=True):
        for e in m.events[:15]:
            st.markdown(f"<div class='event-item'>{e}</div>", unsafe_allow_html=True)

    st.caption("🔄 Refresh the page to see latest score")
    st.stop()


# ═══════════════════════════════════════════════════════════
#  ADMIN — SETUP PAGE
# ═══════════════════════════════════════════════════════════
if not st.session_state.setup_done:
    st.markdown("# 🏸 Match Setup")
    setup = st.session_state.setup

    with st.expander("🏆 Tournament Details (Optional)"):
        t_name = st.text_input("Tournament Name", value=setup.get("tournament_name", ""))
        r_name = st.text_input("Round (e.g. Quarter Final, Final)", value=setup.get("round_name", ""))

    st.divider()
    c1, c2 = st.columns(2)
    with c1: teamA = st.text_input("Team A Name", value=setup.get("teamA", "Team A"))
    with c2: teamB = st.text_input("Team B Name", value=setup.get("teamB", "Team B"))

    st.markdown("### 👥 Players")
    colA, colB = st.columns(2)
    all_pA, all_pB = [], []
    with colA:
        st.markdown(f"**{teamA or 'Team A'}**")
        for i in range(TOTAL_PLAYERS):
            v = st.text_input(f"Player {i+1}", value=setup["all_playersA"][i], key=f"pA{i}")
            all_pA.append(safe_name(v, f"A{i+1}"))
    with colB:
        st.markdown(f"**{teamB or 'Team B'}**")
        for i in range(TOTAL_PLAYERS):
            v = st.text_input(f"Player {i+1}", value=setup["all_playersB"][i], key=f"pB{i}")
            all_pB.append(safe_name(v, f"B{i+1}"))

    st.markdown("### ⭐ Main 5 Players")
    c1, c2 = st.columns(2)
    with c1: mpA = st.multiselect(f"{teamA} – 5 players", all_pA, default=all_pA[:PLAYERS], max_selections=PLAYERS, key="mpA")
    with c2: mpB = st.multiselect(f"{teamB} – 5 players", all_pB, default=all_pB[:PLAYERS], max_selections=PLAYERS, key="mpB")

    if len(mpA) == PLAYERS and len(mpB) == PLAYERS:
        st.markdown("### 🔁 Service Order")
        c1, c2 = st.columns(2)
        oAi, oBi = [], []
        with c1:
            st.markdown(f"**{teamA}**")
            for k in range(PLAYERS):
                opts = [f"{i+1}. {mpA[i]}" for i in range(PLAYERS)]
                sel = st.selectbox(f"Order {k+1}", opts, index=clamp_idx(setup["orderA_idx"][k]-1, PLAYERS), key=f"oA{k}")
                oAi.append(int(sel.split(".")[0]))
        with c2:
            st.markdown(f"**{teamB}**")
            for k in range(PLAYERS):
                opts = [f"{i+1}. {mpB[i]}" for i in range(PLAYERS)]
                sel = st.selectbox(f"Order {k+1}", opts, index=clamp_idx(setup["orderB_idx"][k]-1, PLAYERS), key=f"oB{k}")
                oBi.append(int(sel.split(".")[0]))

        fs = st.radio("Who serves first?", [teamA, teamB], horizontal=True)
        fs_l = "A" if fs == teamA else "B"

        errs = []
        if not unique_ok(oAi): errs.append(f"❌ {teamA} service order must be unique")
        if not unique_ok(oBi): errs.append(f"❌ {teamB} service order must be unique")
        pA2 = [safe_name(x, f"A{i+1}") for i, x in enumerate(mpA)]
        pB2 = [safe_name(x, f"B{i+1}") for i, x in enumerate(mpB)]
        oA2 = build_order(pA2, oAi)
        oB2 = build_order(pB2, oBi)
        if not oA2 or not oB2: errs.append("❌ Invalid service order")
        for e in errs: st.error(e)

        if st.button("▶️ START MATCH", use_container_width=True, disabled=bool(errs)):
            st.session_state.setup.update({
                "teamA": teamA, "teamB": teamB,
                "all_playersA": all_pA, "all_playersB": all_pB,
                "main_playersA": mpA, "main_playersB": mpB,
                "orderA_idx": oAi, "orderB_idx": oBi,
                "firstServe": fs_l, "tournament_name": t_name, "round_name": r_name
            })
            new_otp = generate_otp()
            st.session_state.current_otp = new_otp
            st.session_state.match = init_match(
                safe_name(teamA, "Team A"), safe_name(teamB, "Team B"),
                all_pA, all_pB, pA2, pB2, oA2, oB2, fs_l,
                t_name or None, r_name or None
            )
            st.session_state.setup_done = True
            st.session_state.active_tab = "🏸 Score"
            save_data({
                "match_history": st.session_state.match_history,
                "tournament_bracket": st.session_state.tournament_bracket,
                "tournament_info": st.session_state.tournament_info,
                "current_otp": new_otp
            })
            st.success(f"✅ Match started! Viewer OTP: **{new_otp}**")
            st.rerun()
    else:
        st.warning("⚠️ Please select exactly 5 players per team")
    st.stop()


# ═══════════════════════════════════════════════════════════
#  MATCH ACTIONS (Admin only)
# ═══════════════════════════════════════════════════════════
def cur_server(m):
    return (m.current_server_A if m.serving_team=="A" else m.current_server_B) or "-"

def persist_match():
    save_data({
        "match_history": st.session_state.match_history,
        "tournament_bracket": st.session_state.tournament_bracket,
        "tournament_info": st.session_state.tournament_info,
        "current_otp": st.session_state.current_otp
    })

def add_point(winner):
    m = st.session_state.match
    if m.match_over: return
    m.history.append(snap(m))
    if len(m.history) > 300: m.history.pop(0)

    if winner == "A":
        m.scoreA += 1
        srv = m.current_server_A
        if srv: m.player_points_A[srv] = m.player_points_A.get(srv, 0) + 1
    else:
        m.scoreB += 1
        srv = m.current_server_B
        if srv: m.player_points_B[srv] = m.player_points_B.get(srv, 0) + 1

    if winner != m.serving_team:
        m.serving_team = winner
        if winner == "A":
            m.current_server_A = m.orderA[m.next_idx_A]
            m.next_idx_A = cyclic_next(m.next_idx_A, PLAYERS)
        else:
            m.current_server_B = m.orderB[m.next_idx_B]
            m.next_idx_B = cyclic_next(m.next_idx_B, PLAYERS)

    m.events.insert(0, f"Point → {m.teamA if winner=='A' else m.teamB}  |  {m.scoreA}–{m.scoreB}  |  Server: {cur_server(m)}")

    hit = milestone_hit(m.scoreA, m.scoreB, m.milestones_done)
    if hit:
        m.milestones_done[hit] = True
        st.toast(f"🔄 Court change at {hit}!", icon="🔄")

    if max(m.scoreA, m.scoreB) >= SET_POINTS and abs(m.scoreA - m.scoreB) >= 2:
        sw = "A" if m.scoreA > m.scoreB else "B"
        if sw == "A": m.setsA += 1
        else: m.setsB += 1
        m.points_per_set_A.append(m.scoreA)
        m.points_per_set_B.append(m.scoreB)
        m.events.insert(0, f"✅ Set {m.set_no} won by {m.teamA if sw=='A' else m.teamB} ({m.scoreA}–{m.scoreB})")

        if m.setsA == 2 or m.setsB == 2:
            m.match_over = True
            m.winner = "A" if m.setsA == 2 else "B"
            m.end_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            m.events.insert(0, f"🏆 Match won by {m.teamA if m.winner=='A' else m.teamB}")
            st.session_state.match_history.append({
                "match_id": m.match_id, "date": m.start_time,
                "teamA": m.teamA, "teamB": m.teamB,
                "setsA": m.setsA, "setsB": m.setsB,
                "sets_detail": list(zip(m.points_per_set_A, m.points_per_set_B)),
                "winner": m.teamA if m.winner=="A" else m.teamB,
                "tournament": m.tournament_name, "round": m.round_name,
                "duration": f"{m.start_time} – {m.end_time}",
                "player_points_A": dict(m.player_points_A),
                "player_points_B": dict(m.player_points_B),
            })
            st.session_state.match = m
            persist_match()
            return

        m.set_no += 1; m.scoreA = 0; m.scoreB = 0; m.side_swapped = False
        m.milestones_done = {9: False, 18: False, 27: False}
        m.subs_left_A = 3; m.subs_left_B = 3
        m.timeouts_left_A = 1; m.timeouts_left_B = 1
        m.events.insert(0, f"▶️ Starting Set {m.set_no}")

    st.session_state.match = m
    persist_match()
    st.rerun()

def do_undo():
    m = st.session_state.match
    if not m.history: return
    st.session_state.match = restore(m.history.pop())
    persist_match()

def do_toggle_hand():
    m = st.session_state.match
    m.hand = "L" if m.hand == "R" else "R"
    m.events.insert(0, f"Hand → {'Left' if m.hand=='L' else 'Right'}")
    st.session_state.match = m

def do_court_change():
    m = st.session_state.match
    m.side_swapped = not m.side_swapped
    m.events.insert(0, "🔄 Court sides swapped")
    st.session_state.match = m

def do_substitute(team, player_on, player_off):
    m = st.session_state.match
    if not player_on or not player_off: return
    if team == "A":
        if m.subs_left_A <= 0: st.warning("No subs left"); return
        if player_on in m.playersA: st.error("Already on court"); return
        idx = m.playersA.index(player_off)
        m.playersA[idx] = player_on
        m.player_points_A[player_on] = 0
        m.subs_left_A -= 1
        m.events.insert(0, f"🔄 Sub {m.teamA}: {player_off} → {player_on}")
    else:
        if m.subs_left_B <= 0: st.warning("No subs left"); return
        if player_on in m.playersB: st.error("Already on court"); return
        idx = m.playersB.index(player_off)
        m.playersB[idx] = player_on
        m.player_points_B[player_on] = 0
        m.subs_left_B -= 1
        m.events.insert(0, f"🔄 Sub {m.teamB}: {player_off} → {player_on}")
    st.session_state.match = m

def do_timeout(team):
    m = st.session_state.match
    if team == "A":
        if m.timeouts_left_A <= 0: return
        m.timeouts_left_A -= 1
        m.events.insert(0, f"⏱️ Timeout: {m.teamA}")
    else:
        if m.timeouts_left_B <= 0: return
        m.timeouts_left_B -= 1
        m.events.insert(0, f"⏱️ Timeout: {m.teamB}")
    st.session_state.match = m


match = st.session_state.match


# ═══════════════════════════════════════════════════════════
#  TAB: 🏸 SCORE
# ═══════════════════════════════════════════════════════════
if active_tab == "🏸 Score":
    m = match
    if m.match_over:
        st.markdown(f"<div class='winner-wrap'>🏆 {m.teamA if m.winner=='A' else m.teamB} Wins the Match!</div>", unsafe_allow_html=True)

    if m.tournament_name:
        st.markdown(f"<div style='text-align:center;opacity:0.5;font-size:13px;margin-bottom:12px'>🏆 {m.tournament_name} {('· ' + m.round_name) if m.round_name else ''}</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2.3, 1.1], gap="large")

    with left_col:
        # ── Scoreboard ──
        with st.container(border=True):
            lt = "B" if m.side_swapped else "A"
            rt = "A" if m.side_swapped else "B"
            tn = lambda t: m.teamA if t=="A" else m.teamB
            ts = lambda t: m.scoreA if t=="A" else m.scoreB
            ss = lambda t: m.setsA if t=="A" else m.setsB

            sb1, sb2, sb3 = st.columns([1, 0.22, 1])
            with sb1:
                sicon = "🟠 " if m.serving_team == lt else ""
                st.markdown(f"<div class='team-title'>{sicon}{tn(lt)} <span style='opacity:.4;font-size:13px'>(Left)</span></div>", unsafe_allow_html=True)
                cls = "serving" if m.serving_team == lt else ""
                st.markdown(f"<div class='score-giant {cls}'>{ts(lt)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='set-score'>Sets won: {ss(lt)}</div>", unsafe_allow_html=True)
            with sb2:
                st.markdown("<div style='height:56px'></div>", unsafe_allow_html=True)
                st.markdown("<div style='text-align:center;opacity:.35;font-size:20px;font-weight:700'>vs</div>", unsafe_allow_html=True)
            with sb3:
                sicon = "🟠 " if m.serving_team == rt else ""
                st.markdown(f"<div class='team-title'>{sicon}{tn(rt)} <span style='opacity:.4;font-size:13px'>(Right)</span></div>", unsafe_allow_html=True)
                cls = "serving" if m.serving_team == rt else ""
                st.markdown(f"<div class='score-giant {cls}'>{ts(rt)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='set-score'>Sets won: {ss(rt)}</div>", unsafe_allow_html=True)

            st.markdown(f"<div style='text-align:center;opacity:.35;font-size:11px;margin-top:10px;letter-spacing:1px'>SET {m.set_no} of 3 &nbsp;·&nbsp; TARGET {SET_POINTS} &nbsp;·&nbsp; COURT CHANGE: 9 · 18 · 27</div>", unsafe_allow_html=True)

        # ── Set history ──
        if m.points_per_set_A:
            cols = st.columns(len(m.points_per_set_A))
            for i, (a, b) in enumerate(zip(m.points_per_set_A, m.points_per_set_B)):
                with cols[i]:
                    wn = m.teamA if a > b else m.teamB
                    st.markdown(f"<div class='stat-box'><div style='font-size:10px;opacity:.5;margin-bottom:4px'>SET {i+1}</div><div style='font-size:22px;font-weight:700;font-family:Rajdhani'>{a}–{b}</div><div style='font-size:10px;color:var(--accent)'>{wn}</div></div>", unsafe_allow_html=True)

        # ── Serve info ──
        with st.container(border=True):
            st.markdown("<div style='font-size:13px;font-weight:600;margin-bottom:10px;opacity:.8'>🎾 SERVE INFO</div>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Serving Team", m.teamA if m.serving_team=="A" else m.teamB)
            with c2: st.metric("Current Server", cur_server(m))
            with c3: st.metric("Hand", "Right ✋" if m.hand=="R" else "Left 🤚")
            with c4:
                if st.button("🔁 Toggle Hand", use_container_width=True, key="tog_hand"):
                    do_toggle_hand(); st.rerun()
            c5, c6, c7 = st.columns(3)
            with c5:
                if st.button("🔄 Court Change", use_container_width=True, key="court_chg"):
                    do_court_change(); st.rerun()
            with c6:
                if st.button("↩️ Undo Last", use_container_width=True, key="undo_btn", disabled=not m.history):
                    do_undo(); st.rerun()
            with c7:
                ms = " · ".join([f"{p}{'✅' if m.milestones_done.get(p) else '⏳'}" for p in COURT_CHANGE_PTS])
                st.caption(ms)

        # ── Point buttons ──
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            if st.button(f"➕  +1  {m.teamA}", use_container_width=True, disabled=m.match_over, key="ptA"):
                add_point("A")
        with p2:
            if st.button(f"➕  +1  {m.teamB}", use_container_width=True, disabled=m.match_over, key="ptB"):
                add_point("B")

        # ── Subs & Timeouts ──
        with st.container(border=True):
            st.markdown("<div style='font-size:13px;font-weight:600;margin-bottom:10px;opacity:.8'>🔄 SUBSTITUTIONS & TIMEOUTS</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            for team, col in [("A", col1), ("B", col2)]:
                tname  = m.teamA if team=="A" else m.teamB
                subs   = m.subs_left_A if team=="A" else m.subs_left_B
                tos    = m.timeouts_left_A if team=="A" else m.timeouts_left_B
                p_on   = m.playersA if team=="A" else m.playersB
                all_p  = m.all_playersA if team=="A" else m.all_playersB
                with col:
                    sb_cls = "b-green" if subs > 0 else "b-red"
                    to_cls = "b-blue" if tos > 0 else "b-red"
                    st.markdown(f"**{tname}** &nbsp; <span class='badge {sb_cls}'>Subs {subs}</span> &nbsp; <span class='badge {to_cls}'>T/O {tos}</span>", unsafe_allow_html=True)
                    bench = [p for p in all_p if p not in p_on]
                    if subs > 0 and bench:
                        on  = st.selectbox("In ▲", bench, key=f"on{team}")
                        off = st.selectbox("Out ▼", p_on,  key=f"off{team}")
                        if st.button("Substitute", key=f"sub{team}", use_container_width=True):
                            do_substitute(team, on, off); st.rerun()
                    else:
                        st.caption("No substitutions available")
                    if tos > 0:
                        if st.button("⏱️ Call Timeout", key=f"to{team}_s{m.set_no}", use_container_width=True):
                            do_timeout(team); st.rerun()
                    else:
                        st.caption("No timeouts left")

    with right_col:
        # Service order
        st.markdown("<div style='font-size:13px;font-weight:600;margin-bottom:6px;opacity:.8'>🔁 SERVICE ORDER</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"**{m.teamA}**")
            for i, p in enumerate(m.orderA):
                active_s = m.serving_team=="A" and m.current_server_A==p
                st.markdown(f"{'🟠' if active_s else f'{i+1}.'} {p}", unsafe_allow_html=False)
        with st.container(border=True):
            st.markdown(f"**{m.teamB}**")
            for i, p in enumerate(m.orderB):
                active_s = m.serving_team=="B" and m.current_server_B==p
                st.markdown(f"{'🟠' if active_s else f'{i+1}.'} {p}", unsafe_allow_html=False)

        # On court
        st.markdown("<div style='font-size:13px;font-weight:600;margin:12px 0 6px;opacity:.8'>👥 ON COURT</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"**{m.teamA}**")
            st.caption(", ".join(m.playersA))
            st.markdown(f"**{m.teamB}**")
            st.caption(", ".join(m.playersB))

        # Events
        st.markdown("<div style='font-size:13px;font-weight:600;margin:12px 0 6px;opacity:.8'>🧾 LIVE EVENTS</div>", unsafe_allow_html=True)
        with st.container(border=True):
            for e in m.events[:18]:
                st.markdown(f"<div class='event-item'>{e}</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  TAB: 📊 STATS
# ═══════════════════════════════════════════════════════════
elif active_tab == "📊 Stats":
    st.markdown("# 📊 Match Statistics")
    m = match
    total_pts = m.scoreA + m.scoreB + sum(m.points_per_set_A) + sum(m.points_per_set_B)

    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [
        (c1, f"Set {m.set_no}", "Current Set"),
        (c2, f"{m.setsA}–{m.setsB}", "Sets"),
        (c3, f"{m.scoreA}–{m.scoreB}", "Set Score"),
        (c4, total_pts, "Total Points"),
    ]:
        with col:
            st.markdown(f"<div class='stat-box'><div class='stat-num'>{num}</div><div class='stat-lbl'>{lbl}</div></div>", unsafe_allow_html=True)

    if m.points_per_set_A:
        st.markdown("### 📈 Set Breakdown")
        hdr_cols = st.columns(len(m.points_per_set_A) + 1)
        with hdr_cols[0]:
            st.markdown("**Team**")
            st.markdown(m.teamA)
            st.markdown(m.teamB)
        for i, (a, b) in enumerate(zip(m.points_per_set_A, m.points_per_set_B)):
            with hdr_cols[i+1]:
                st.markdown(f"**Set {i+1}**")
                st.markdown(f"{'🏆 ' if a>b else ''}{a}")
                st.markdown(f"{'🏆 ' if b>a else ''}{b}")

    st.markdown("### 🏅 Player Points")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{m.teamA}**")
        for p, pts in sorted(m.player_points_A.items(), key=lambda x: -x[1]):
            bar = min(pts, 35)
            st.markdown(f"{p}: **{pts}**")
            st.progress(bar / 35)
    with c2:
        st.markdown(f"**{m.teamB}**")
        for p, pts in sorted(m.player_points_B.items(), key=lambda x: -x[1]):
            bar = min(pts, 35)
            st.markdown(f"{p}: **{pts}**")
            st.progress(bar / 35)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"{m.teamA} Subs Used", 3 - m.subs_left_A)
    with c2: st.metric(f"{m.teamB} Subs Used", 3 - m.subs_left_B)
    with c3: st.metric(f"{m.teamA} T/O Used", 1 - m.timeouts_left_A)
    with c4: st.metric(f"{m.teamB} T/O Used", 1 - m.timeouts_left_B)

    with st.expander("🧾 Full Event Log"):
        for e in m.events:
            st.markdown(f"- {e}")


# ═══════════════════════════════════════════════════════════
#  TAB: 🏆 TOURNAMENT
# ═══════════════════════════════════════════════════════════
elif active_tab == "🏆 Tournament":
    st.markdown("# 🏆 Tournament Manager")

    with st.container(border=True):
        st.markdown("### ➕ Create Tournament Bracket")
        t_name = st.text_input("Tournament Name", key="tnew")
        num_teams = st.selectbox("Number of Teams", [4, 8, 16], key="nteams")
        cols = st.columns(2)
        team_names = []
        for i in range(num_teams):
            with cols[i % 2]:
                t = st.text_input(f"Team {i+1}", value=f"Team {i+1}", key=f"tt{i}")
                team_names.append(t)

        if st.button("🏆 Generate Bracket", use_container_width=True):
            import random as rnd
            shuffled = team_names[:]
            rnd.shuffle(shuffled)
            bracket = [{"round": "Round 1", "teamA": shuffled[i], "teamB": shuffled[i+1], "winner": None}
                       for i in range(0, len(shuffled)-1, 2)]
            st.session_state.tournament_bracket = bracket
            st.session_state.tournament_info = {"name": t_name, "teams": team_names}
            persist_match()
            st.rerun()

    if st.session_state.tournament_bracket:
        tinfo = st.session_state.tournament_info
        st.markdown(f"### 🎯 {tinfo.get('name', 'Tournament')}")
        for i, mb in enumerate(st.session_state.tournament_bracket):
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 0.5, 2])
                with c1: st.markdown(f"**{mb['teamA']}**")
                with c2: st.markdown("<div style='text-align:center;opacity:.4'>vs</div>", unsafe_allow_html=True)
                with c3: st.markdown(f"**{mb['teamB']}**")
                if not mb["winner"]:
                    w = st.radio("Winner", [mb["teamA"], mb["teamB"]], key=f"bw{i}", horizontal=True)
                    if st.button("✅ Confirm", key=f"bc{i}"):
                        st.session_state.tournament_bracket[i]["winner"] = w
                        persist_match(); st.rerun()
                else:
                    st.markdown(f"<span class='badge b-gold'>🏆 {mb['winner']}</span>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  TAB: 📜 HISTORY
# ═══════════════════════════════════════════════════════════
elif active_tab == "📜 History":
    st.markdown("# 📜 Match History")
    history = st.session_state.match_history

    if not history:
        st.info("No completed matches yet.")
    else:
        st.markdown(f"**{len(history)} match(es) on record**")
        for h in reversed(history):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### {h['teamA']} vs {h['teamB']}")
                    if h.get("tournament"): st.caption(f"🏆 {h['tournament']} {h.get('round','')}")
                    st.caption(f"📅 {h['date']} · {h.get('duration','')}")
                    sets_str = " | ".join([f"Set {j+1}: {a}–{b}" for j,(a,b) in enumerate(h.get("sets_detail",[]))])
                    st.markdown(f"Sets: **{h['setsA']}–{h['setsB']}** &nbsp; · &nbsp; {sets_str}")
                with c2:
                    st.markdown(f"<div class='winner-wrap' style='font-size:16px;padding:14px'>🏆<br>{h['winner']}</div>", unsafe_allow_html=True)

        if st.button("🗑️ Clear All History", use_container_width=True):
            st.session_state.match_history = []
            persist_match(); st.rerun()


# ═══════════════════════════════════════════════════════════
#  TAB: ⚙️ ADMIN PANEL
# ═══════════════════════════════════════════════════════════
elif active_tab == "⚙️ Admin" and is_admin:
    st.markdown("# ⚙️ Admin Panel")

    with st.container(border=True):
        st.markdown("### 👁️ Viewer OTP")
        st.markdown("Share this OTP with viewers so they can watch the live score:")
        otp = st.session_state.current_otp
        if otp:
            st.markdown(f"<div class='otp-display'>{otp}</div>", unsafe_allow_html=True)
        else:
            st.info("OTP will be generated when you start a match.")
        if st.button("🔄 Generate New OTP", use_container_width=True):
            new_otp = generate_otp()
            st.session_state.current_otp = new_otp
            persist_match()
            st.success(f"New OTP: {new_otp}")
            st.rerun()

    with st.container(border=True):
        st.markdown("### 📥 Export Match Data")
        all_data = {
            "match_history": st.session_state.match_history,
            "tournament": st.session_state.tournament_info,
            "tournament_bracket": st.session_state.tournament_bracket,
        }
        st.download_button(
            "⬇️ Download Match Data (JSON)",
            data=json.dumps(all_data, indent=2),
            file_name=f"ballbadminton_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

    with st.container(border=True):
        st.markdown("### 🔧 Match Controls")
        if st.session_state.match and st.session_state.setup_done:
            m = st.session_state.match
            st.markdown(f"**Current Match:** {m.teamA} vs {m.teamB}  |  Set {m.set_no}  |  {m.scoreA}–{m.scoreB}")
            st.markdown(f"**Match started:** {m.start_time}")
        else:
            st.info("No active match.")

    with st.container(border=True):
        st.markdown("### ℹ️ App Info")
        st.markdown("""
        - **Admin Login:** Username & Password (set in app.py)
        - **Viewer Access:** OTP generated per match (shown above)
        - **Data saved:** `match_data.json` (persists across restarts)
        - **Undo:** Up to 300 moves per match
        """)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.caption("🏸 Ball Badminton Live Scoreboard · streamlit run app.py")
