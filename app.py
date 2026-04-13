# app.py - Ball Badminton Advanced Scoreboard
import streamlit as st
import json
import time
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime

# ===================== CONFIG =====================
SET_POINTS = 35
COURT_CHANGE_POINTS = [9, 18, 27]
PLAYERS = 5
TOTAL_PLAYERS = 10
ADMIN_USERNAME = "Ballbadminton"
ADMIN_PASSWORD = "partha"

# ===================== HELPERS =====================
def cyclic_next(i, n): return (i + 1) % n
def default_players(prefix): return [f"{prefix}{i+1}" for i in range(TOTAL_PLAYERS)]
def safe_name(s, fallback): s = (s or "").strip(); return s if s else fallback
def unique_ok(lst): return len(set(lst)) == len(lst)
def clamp_index(idx, n, default=0): return idx if n > 0 and 0 <= idx < n else default

def build_order(players_5, order_indices_1based):
    if len(players_5) != PLAYERS or len(order_indices_1based) != PLAYERS: return []
    out = []
    for idx in order_indices_1based:
        if idx < 1 or idx > PLAYERS: return []
        out.append(players_5[idx - 1])
    return out

def milestone_hit(scoreA, scoreB, done):
    for p in COURT_CHANGE_POINTS:
        if not done.get(p, False) and (scoreA == p or scoreB == p):
            return p
    return None

# ===================== MATCH STATE =====================
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
    # Advanced stats
    points_per_set_A: List[int]
    points_per_set_B: List[int]
    player_points_A: Dict[str, int]
    player_points_B: Dict[str, int]
    start_time: str
    end_time: Optional[str]
    match_id: str
    # Tournament
    tournament_name: Optional[str]
    round_name: Optional[str]

def init_match(teamA, teamB, all_pA, all_pB, pA, pB, oA, oB, first_serve,
               tournament_name=None, round_name=None):
    if len(oA) != PLAYERS: oA = pA[:]
    if len(oB) != PLAYERS: oB = pB[:]
    if first_serve == "A":
        cA, cB, nA, nB = oA[0], None, 1, 0
    else:
        cA, cB, nA, nB = None, oB[0], 0, 1
    return MatchState(
        teamA=teamA, teamB=teamB,
        all_playersA=all_pA, all_playersB=all_pB,
        playersA=pA, playersB=pB,
        orderA=oA, orderB=oB,
        set_no=1, setsA=0, setsB=0, scoreA=0, scoreB=0,
        serving_team=first_serve, hand="R", side_swapped=False,
        current_server_A=cA, current_server_B=cB,
        next_idx_A=nA, next_idx_B=nB,
        subs_left_A=3, subs_left_B=3,
        timeouts_left_A=1, timeouts_left_B=1,
        milestones_done={9: False, 18: False, 27: False},
        history=[], events=[f"Match started. First serve: Team {'A' if first_serve=='A' else 'B'}"],
        match_over=False, winner=None,
        points_per_set_A=[], points_per_set_B=[],
        player_points_A={p: 0 for p in pA},
        player_points_B={p: 0 for p in pB},
        start_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        end_time=None,
        match_id=datetime.now().strftime("%Y%m%d%H%M%S"),
        tournament_name=tournament_name,
        round_name=round_name
    )

def snapshot(s): return asdict(s)
def restore(d): return MatchState(**d)

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="Ball Badminton Live", page_icon="🏸", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Outfit:wght@700;800&display=swap');
html, body, .stApp { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #fff; font-family: 'Inter', sans-serif; }
.stApp .block-container { max-width: 1400px; padding: 1.5rem; }
.stSidebar { background: rgba(30,41,59,0.97) !important; border-right: 2px solid #3b82f6 !important; }
.stButton > button { background: linear-gradient(90deg,#3b82f6,#2563eb) !important; color:#fff !important; border:none !important; font-weight:800 !important; padding:12px 20px !important; border-radius:12px !important; box-shadow:0 4px 12px rgba(59,130,246,.35) !important; transition: transform .1s; }
.stButton > button:hover { transform: scale(1.03); }
[data-testid="stContainer"] { border:1px solid rgba(255,255,255,.10) !important; border-radius:14px !important; padding:16px !important; background:rgba(15,23,42,.55) !important; backdrop-filter:blur(10px); }
.score-big { font-size:88px; font-weight:1000; line-height:1; background: linear-gradient(135deg,#60a5fa,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.team-name { font-size:22px; font-weight:800; letter-spacing:-.5px; }
.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700; }
.badge-green { background:#16a34a; color:#fff; }
.badge-yellow { background:#d97706; color:#fff; }
.badge-red { background:#dc2626; color:#fff; }
.badge-blue { background:#2563eb; color:#fff; }
.serve-indicator { font-size:20px; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.stat-card { background:rgba(255,255,255,.06); border-radius:12px; padding:14px; text-align:center; border:1px solid rgba(255,255,255,.08); }
.stat-number { font-size:32px; font-weight:800; color:#60a5fa; }
.stat-label { font-size:11px; opacity:.6; text-transform:uppercase; letter-spacing:1px; }
.bracket-match { background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.15); border-radius:10px; padding:10px 14px; margin:4px 0; }
.winner-banner { background: linear-gradient(135deg,#f59e0b,#d97706); border-radius:16px; padding:20px; text-align:center; font-size:28px; font-weight:900; }
</style>
""", unsafe_allow_html=True)

# ===================== SESSION INIT =====================
for key, val in [
    ("authenticated", False), ("setup_done", False), ("active_tab", "🏸 Live Score"),
    ("match", None), ("match_history", []), ("tournament", None),
    ("setup", {
        "teamA": "Team A", "teamB": "Team B",
        "all_playersA": default_players("A"), "all_playersB": default_players("B"),
        "main_playersA": [f"A{i+1}" for i in range(PLAYERS)],
        "main_playersB": [f"B{i+1}" for i in range(PLAYERS)],
        "orderA_idx": [1,2,3,4,5], "orderB_idx": [1,2,3,4,5], "firstServe": "A",
        "tournament_name": "", "round_name": ""
    })
]:
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.setup_done and st.session_state.match is None:
    st.session_state.setup_done = False

# ===================== LOGIN =====================
if not st.session_state.authenticated:
    st.markdown("<div style='text-align:center;padding:40px 0 20px'><div style='font-size:64px'>🏸</div><h1 style='font-size:36px;font-weight:900'>Ball Badminton</h1><p style='opacity:.6'>Advanced Live Scoreboard</p></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### 🔐 Admin Login")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            if st.button("🔓 Login", use_container_width=True):
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
            st.caption("Username: Ballbadminton | Password: partha")
    st.stop()

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("## 🏸 Ball Badminton")
    st.markdown("---")
    tabs_list = ["🏸 Live Score", "📊 Statistics", "🏆 Tournament", "📜 Match History"]
    for t in tabs_list:
        if st.button(t, use_container_width=True, key=f"nav_{t}"):
            st.session_state.active_tab = t
            st.rerun()
    st.markdown("---")
    if st.session_state.setup_done and st.session_state.match:
        m = st.session_state.match
        st.markdown(f"**Match:** {m.teamA} vs {m.teamB}")
        st.markdown(f"**Set:** {m.set_no}/3")
        st.markdown(f"**Score:** {m.setsA} – {m.setsB} (sets)")
        if m.tournament_name:
            st.markdown(f"**Tournament:** {m.tournament_name}")
        st.markdown("---")
    if st.button("🔄 New Match", use_container_width=True, key="new_match_btn"):
        st.session_state.setup_done = False
        st.session_state.match = None
        st.session_state.active_tab = "🏸 Live Score"
        st.rerun()
    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        for k in ["authenticated", "setup_done", "match"]:
            st.session_state[k] = False if k == "authenticated" else (None if k == "match" else False)
        st.rerun()

active_tab = st.session_state.active_tab

# ===================== SETUP PAGE =====================
if not st.session_state.setup_done:
    st.markdown("# 🏸 Match Setup")
    setup = st.session_state.setup

    # Tournament info
    with st.expander("🏆 Tournament Details (Optional)", expanded=False):
        t_name = st.text_input("Tournament Name", value=setup.get("tournament_name", ""))
        r_name = st.text_input("Round (e.g. Semi Final, Final)", value=setup.get("round_name", ""))

    st.divider()
    c1, c2 = st.columns(2)
    with c1: teamA = st.text_input("Team A Name", value=setup.get("teamA", "Team A"))
    with c2: teamB = st.text_input("Team B Name", value=setup.get("teamB", "Team B"))

    st.markdown("## 👥 Enter All 10 Players")
    colA, colB = st.columns(2)
    all_playersA, all_playersB = [], []
    with colA:
        st.markdown(f"### {teamA or 'Team A'}")
        for i in range(TOTAL_PLAYERS):
            prev = setup.get("all_playersA", default_players("A"))[i]
            v = st.text_input(f"Player {i+1}", value=prev, key=f"pA{i}")
            all_playersA.append(safe_name(v, f"A{i+1}"))
    with colB:
        st.markdown(f"### {teamB or 'Team B'}")
        for i in range(TOTAL_PLAYERS):
            prev = setup.get("all_playersB", default_players("B"))[i]
            v = st.text_input(f"Player {i+1}", value=prev, key=f"pB{i}")
            all_playersB.append(safe_name(v, f"B{i+1}"))

    st.markdown("## ⭐ Select Main 5 Players")
    c1, c2 = st.columns(2)
    with c1:
        main_pA = st.multiselect(f"{teamA} – Choose 5", all_playersA, default=all_playersA[:PLAYERS], max_selections=PLAYERS, key="main_a")
    with c2:
        main_pB = st.multiselect(f"{teamB} – Choose 5", all_playersB, default=all_playersB[:PLAYERS], max_selections=PLAYERS, key="main_b")

    if len(main_pA) == PLAYERS and len(main_pB) == PLAYERS:
        st.markdown("## 🔁 Service Order")
        saved_oa = setup.get("orderA_idx", [1,2,3,4,5])
        saved_ob = setup.get("orderB_idx", [1,2,3,4,5])
        c1, c2 = st.columns(2)
        orderA_idx, orderB_idx = [], []
        with c1:
            st.markdown(f"### {teamA}")
            optsA = [f"{i+1}. {main_pA[i]}" for i in range(PLAYERS)]
            for k in range(PLAYERS):
                sel = st.selectbox(f"Order {k+1}", optsA, index=clamp_index(saved_oa[k]-1, len(optsA)), key=f"oaS{k}")
                orderA_idx.append(int(sel.split(".")[0]))
        with c2:
            st.markdown(f"### {teamB}")
            optsB = [f"{i+1}. {main_pB[i]}" for i in range(PLAYERS)]
            for k in range(PLAYERS):
                sel = st.selectbox(f"Order {k+1}", optsB, index=clamp_index(saved_ob[k]-1, len(optsB)), key=f"obS{k}")
                orderB_idx.append(int(sel.split(".")[0]))

        firstServe = st.radio("Who serves first?", [f"{teamA}", f"{teamB}"], horizontal=True)
        fs_letter = "A" if firstServe == teamA else "B"

        errors = []
        if not unique_ok(orderA_idx): errors.append(f"❌ {teamA} service order must be unique")
        if not unique_ok(orderB_idx): errors.append(f"❌ {teamB} service order must be unique")
        pA2 = [safe_name(x, f"A{i+1}") for i, x in enumerate(main_pA)]
        pB2 = [safe_name(x, f"B{i+1}") for i, x in enumerate(main_pB)]
        oA2 = build_order(pA2, orderA_idx)
        oB2 = build_order(pB2, orderB_idx)
        if not oA2 or not oB2: errors.append("❌ Invalid service order")
        for e in errors: st.error(e)

        if st.button("▶️ START MATCH", use_container_width=True, disabled=bool(errors)):
            st.session_state.setup.update({
                "teamA": teamA, "teamB": teamB,
                "all_playersA": all_playersA, "all_playersB": all_playersB,
                "main_playersA": main_pA, "main_playersB": main_pB,
                "orderA_idx": orderA_idx, "orderB_idx": orderB_idx, "firstServe": fs_letter,
                "tournament_name": t_name, "round_name": r_name
            })
            st.session_state.match = init_match(
                safe_name(teamA,"Team A"), safe_name(teamB,"Team B"),
                all_playersA, all_playersB, pA2, pB2, oA2, oB2, fs_letter,
                t_name or None, r_name or None
            )
            st.session_state.setup_done = True
            st.session_state.active_tab = "🏸 Live Score"
            st.rerun()
    else:
        st.warning("⚠️ Please select exactly 5 players per team")
    st.stop()

# ===================== MATCH ACTIONS =====================
match: MatchState = st.session_state.match

def current_server(m):
    return (m.current_server_A if m.serving_team == "A" else m.current_server_B) or "-"

def add_point(winner):
    m = st.session_state.match
    if m.match_over: return
    m.history.append(snapshot(m))
    if len(m.history) > 300: m.history.pop(0)
    if winner == "A":
        m.scoreA += 1
        srv = m.current_server_A
        if srv and srv in m.player_points_A: m.player_points_A[srv] = m.player_points_A.get(srv, 0) + 1
    else:
        m.scoreB += 1
        srv = m.current_server_B
        if srv and srv in m.player_points_B: m.player_points_B[srv] = m.player_points_B.get(srv, 0) + 1

    if winner != m.serving_team:
        m.serving_team = winner
        if winner == "A":
            m.current_server_A = m.orderA[m.next_idx_A]
            m.next_idx_A = cyclic_next(m.next_idx_A, PLAYERS)
        else:
            m.current_server_B = m.orderB[m.next_idx_B]
            m.next_idx_B = cyclic_next(m.next_idx_B, PLAYERS)

    m.events.insert(0, f"Point → {m.teamA if winner=='A' else m.teamB} | Server: {current_server(m)} | {m.scoreA}–{m.scoreB}")
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
        m.events.insert(0, f"✅ Set {m.set_no} → {m.teamA if sw=='A' else m.teamB} ({m.scoreA}–{m.scoreB})")
        if m.setsA == 2 or m.setsB == 2:
            m.match_over = True
            m.winner = "A" if m.setsA == 2 else "B"
            m.end_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            m.events.insert(0, f"🏆 Match → {m.teamA if m.winner=='A' else m.teamB}")
            # Save to history
            st.session_state.match_history.append({
                "match_id": m.match_id,
                "date": m.start_time,
                "teamA": m.teamA, "teamB": m.teamB,
                "setsA": m.setsA, "setsB": m.setsB,
                "sets_detail": list(zip(m.points_per_set_A, m.points_per_set_B)),
                "winner": m.teamA if m.winner=="A" else m.teamB,
                "tournament": m.tournament_name,
                "round": m.round_name,
                "duration": f"{m.start_time} – {m.end_time}"
            })
            st.session_state.match = m
            return
        m.set_no += 1; m.scoreA = 0; m.scoreB = 0; m.side_swapped = False
        m.milestones_done = {9: False, 18: False, 27: False}
        m.subs_left_A = 3; m.subs_left_B = 3
        m.timeouts_left_A = 1; m.timeouts_left_B = 1
        m.events.insert(0, f"▶️ Starting Set {m.set_no}")
    st.session_state.match = m
    st.rerun()

def undo():
    m = st.session_state.match
    if not m.history: return
    st.session_state.match = restore(m.history.pop())

def toggle_hand():
    m = st.session_state.match
    m.hand = "L" if m.hand == "R" else "R"
    m.events.insert(0, f"Hand → {'Left' if m.hand=='L' else 'Right'}")
    st.session_state.match = m

def court_change():
    m = st.session_state.match
    m.side_swapped = not m.side_swapped
    m.events.insert(0, "🔄 Court sides swapped")
    st.session_state.match = m

def substitute_player(team, player_on, player_off):
    m = st.session_state.match
    if not player_on or not player_off: st.error("Select both players"); return
    if team == "A":
        if m.subs_left_A <= 0: st.warning("No subs left"); return
        if player_on in m.playersA: st.error("Already on court"); return
        idx = m.playersA.index(player_off)
        m.playersA[idx] = player_on
        m.player_points_A[player_on] = 0
        m.subs_left_A -= 1
        m.events.insert(0, f"Sub {m.teamA}: {player_off} → {player_on}")
    else:
        if m.subs_left_B <= 0: st.warning("No subs left"); return
        if player_on in m.playersB: st.error("Already on court"); return
        idx = m.playersB.index(player_off)
        m.playersB[idx] = player_on
        m.player_points_B[player_on] = 0
        m.subs_left_B -= 1
        m.events.insert(0, f"Sub {m.teamB}: {player_off} → {player_on}")
    st.session_state.match = m

def take_timeout(team):
    m = st.session_state.match
    if team == "A":
        if m.timeouts_left_A <= 0: st.info("No timeouts left"); return
        m.timeouts_left_A -= 1
        m.events.insert(0, f"⏱️ Timeout: {m.teamA}")
    else:
        if m.timeouts_left_B <= 0: st.info("No timeouts left"); return
        m.timeouts_left_B -= 1
        m.events.insert(0, f"⏱️ Timeout: {m.teamB}")
    st.session_state.match = m

match = st.session_state.match

# ===================== LIVE SCORE TAB =====================
if active_tab == "🏸 Live Score":
    if match.match_over:
        st.markdown(f"<div class='winner-banner'>🏆 {match.teamA if match.winner=='A' else match.teamB} Wins the Match!</div>", unsafe_allow_html=True)
        st.write("")

    # Tournament header
    if match.tournament_name:
        st.markdown(f"<div style='text-align:center;opacity:.7;font-size:14px'>🏆 {match.tournament_name} {'| ' + match.round_name if match.round_name else ''}</div>", unsafe_allow_html=True)

    left, right = st.columns([2.2, 1.2], gap="large")

    with left:
        # Scoreboard
        with st.container(border=True):
            left_team = "B" if match.side_swapped else "A"
            right_team = "A" if match.side_swapped else "B"
            tn = lambda t: match.teamA if t=="A" else match.teamB
            ts = lambda t: match.scoreA if t=="A" else match.scoreB
            ss = lambda t: match.setsA if t=="A" else match.setsB

            sb1, sb2, sb3 = st.columns([1, 0.3, 1])
            with sb1:
                serve_icon = "🟡 " if match.serving_team == left_team else ""
                st.markdown(f"<div class='team-name'>{serve_icon}{tn(left_team)} <span style='opacity:.5;font-size:14px'>(Left)</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='score-big'>{ts(left_team)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px;margin-top:4px'>Sets: <b>{ss(left_team)}</b></div>", unsafe_allow_html=True)
            with sb2:
                st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
                st.markdown("<div style='text-align:center;font-size:22px;opacity:.5'>vs</div>", unsafe_allow_html=True)
            with sb3:
                serve_icon = "🟡 " if match.serving_team == right_team else ""
                st.markdown(f"<div class='team-name'>{serve_icon}{tn(right_team)} <span style='opacity:.5;font-size:14px'>(Right)</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='score-big'>{ts(right_team)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:16px;margin-top:4px'>Sets: <b>{ss(right_team)}</b></div>", unsafe_allow_html=True)

            st.markdown(f"<div style='text-align:center;opacity:.5;font-size:12px;margin-top:8px'>Set {match.set_no}/3 | Target: {SET_POINTS} | Court change: 9, 18, 27</div>", unsafe_allow_html=True)

        # Set scores history
        if match.points_per_set_A:
            st.markdown("**Set History:**")
            cols = st.columns(len(match.points_per_set_A))
            for i, (a, b) in enumerate(zip(match.points_per_set_A, match.points_per_set_B)):
                with cols[i]:
                    winner_set = match.teamA if a > b else match.teamB
                    st.markdown(f"<div class='stat-card'><div style='font-size:11px;opacity:.6'>Set {i+1}</div><div style='font-size:20px;font-weight:800'>{a}–{b}</div><div style='font-size:10px;color:#60a5fa'>{winner_set}</div></div>", unsafe_allow_html=True)

        # Serving info
        with st.container(border=True):
            st.markdown("#### 🎾 Serve Info")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Serving", match.teamA if match.serving_team=="A" else match.teamB)
            with c2: st.metric("Server", current_server(match))
            with c3: st.metric("Hand", "Right" if match.hand=="R" else "Left")
            with c4:
                if st.button("🖐️ Toggle Hand", use_container_width=True): toggle_hand(); st.rerun()
            c5, c6, c7 = st.columns(3)
            with c5:
                if st.button("🔄 Court Change", use_container_width=True): court_change(); st.rerun()
            with c6:
                if st.button("↩️ Undo", use_container_width=True, disabled=not match.history): undo(); st.rerun()
            with c7:
                milestone_status = " | ".join([f"{p}: {'✅' if match.milestones_done.get(p) else '⏳'}" for p in COURT_CHANGE_POINTS])
                st.caption(milestone_status)

        # Point buttons
        st.write("")
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f"<div style='text-align:center;margin-bottom:6px;font-size:13px;opacity:.7'>Score: {match.scoreA}</div>", unsafe_allow_html=True)
            if st.button(f"➕ Point for {match.teamA}", use_container_width=True, disabled=match.match_over): add_point("A")
        with p2:
            st.markdown(f"<div style='text-align:center;margin-bottom:6px;font-size:13px;opacity:.7'>Score: {match.scoreB}</div>", unsafe_allow_html=True)
            if st.button(f"➕ Point for {match.teamB}", use_container_width=True, disabled=match.match_over): add_point("B")

        # Substitutions & Timeouts
        with st.container(border=True):
            st.markdown("#### 🔄 Substitutions & Timeouts")
            col1, col2 = st.columns(2)
            for team, col in [("A", col1), ("B", col2)]:
                m = match
                tname = m.teamA if team=="A" else m.teamB
                subs = m.subs_left_A if team=="A" else m.subs_left_B
                tos = m.timeouts_left_A if team=="A" else m.timeouts_left_B
                players_on = m.playersA if team=="A" else m.playersB
                all_p = m.all_playersA if team=="A" else m.all_playersB
                with col:
                    st.markdown(f"**{tname}**")
                    c1s, c2s = st.columns(2)
                    with c1s: st.markdown(f"<span class='badge {'badge-green' if subs>0 else 'badge-red'}'>Subs: {subs}</span>", unsafe_allow_html=True)
                    with c2s: st.markdown(f"<span class='badge {'badge-blue' if tos>0 else 'badge-red'}'>T/O: {tos}</span>", unsafe_allow_html=True)
                    bench = [p for p in all_p if p not in players_on]
                    if subs > 0 and bench:
                        on = st.selectbox("In", bench, key=f"on{team}")
                        off = st.selectbox("Out", players_on, key=f"off{team}")
                        if st.button("Substitute", key=f"sub{team}", use_container_width=True):
                            substitute_player(team, on, off); st.rerun()
                    if tos > 0:
                        if st.button("⏱️ Timeout", key=f"to{team}_set{m.set_no}", use_container_width=True):
                            take_timeout(team); st.rerun()

    with right:
        st.markdown("### 🔁 Service Order")
        with st.container(border=True):
            st.markdown(f"**{match.teamA}**")
            for i, p in enumerate(match.orderA):
                icon = "🟡" if (match.serving_team=="A" and match.current_server_A==p) else f"{i+1}."
                st.markdown(f"{icon} {p}")
        with st.container(border=True):
            st.markdown(f"**{match.teamB}**")
            for i, p in enumerate(match.orderB):
                icon = "🟡" if (match.serving_team=="B" and match.current_server_B==p) else f"{i+1}."
                st.markdown(f"{icon} {p}")

        st.write("")
        st.markdown("### 👥 On Court")
        with st.container(border=True):
            st.markdown(f"**{match.teamA}**: {', '.join(match.playersA)}")
            st.markdown(f"**{match.teamB}**: {', '.join(match.playersB)}")

        st.write("")
        st.markdown("### 🧾 Live Events")
        with st.container(border=True):
            for e in match.events[:20]:
                st.markdown(f"<div style='font-size:12px;padding:3px 0;border-bottom:1px solid rgba(255,255,255,.06)'>{e}</div>", unsafe_allow_html=True)

# ===================== STATISTICS TAB =====================
elif active_tab == "📊 Statistics":
    st.markdown("# 📊 Match Statistics")
    m = match

    # Overview stats
    total_points = m.scoreA + m.scoreB + sum(m.points_per_set_A) + sum(m.points_per_set_B)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='stat-card'><div class='stat-number'>{m.set_no}</div><div class='stat-label'>Current Set</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='stat-card'><div class='stat-number'>{m.setsA}–{m.setsB}</div><div class='stat-label'>Sets</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='stat-card'><div class='stat-number'>{m.scoreA}–{m.scoreB}</div><div class='stat-label'>Current Set</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='stat-card'><div class='stat-number'>{total_points}</div><div class='stat-label'>Total Points</div></div>", unsafe_allow_html=True)

    st.write("")

    # Set by set breakdown
    if m.points_per_set_A:
        st.markdown("### 📈 Set-by-Set Breakdown")
        cols = st.columns(len(m.points_per_set_A) + 1)
        with cols[0]:
            st.markdown("**Team**")
            st.markdown(f"_{m.teamA}_")
            st.markdown(f"_{m.teamB}_")
        for i, (a, b) in enumerate(zip(m.points_per_set_A, m.points_per_set_B)):
            with cols[i+1]:
                st.markdown(f"**Set {i+1}**")
                st.markdown(f"{'🏆 ' if a>b else ''}{a}")
                st.markdown(f"{'🏆 ' if b>a else ''}{b}")

    st.write("")

    # Player points
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 🏅 {m.teamA} – Points by Player")
        sorted_A = sorted(m.player_points_A.items(), key=lambda x: x[1], reverse=True)
        for player, pts in sorted_A:
            bar = "█" * pts if pts < 30 else "█" * 30 + "+"
            st.markdown(f"**{player}**: {pts} pts `{bar}`")
    with col2:
        st.markdown(f"### 🏅 {m.teamB} – Points by Player")
        sorted_B = sorted(m.player_points_B.items(), key=lambda x: x[1], reverse=True)
        for player, pts in sorted_B:
            bar = "█" * pts if pts < 30 else "█" * 30 + "+"
            st.markdown(f"**{player}**: {pts} pts `{bar}`")

    st.write("")
    st.markdown("### 📋 Substitutions Used")
    c1, c2 = st.columns(2)
    with c1: st.metric(f"{m.teamA} Subs Used", 3 - m.subs_left_A)
    with c2: st.metric(f"{m.teamB} Subs Used", 3 - m.subs_left_B)

    st.markdown("### ⏱️ Timeouts Used")
    c1, c2 = st.columns(2)
    with c1: st.metric(f"{m.teamA} Timeouts Used", 1 - m.timeouts_left_A)
    with c2: st.metric(f"{m.teamB} Timeouts Used", 1 - m.timeouts_left_B)

    st.write("")
    st.markdown("### 🧾 Full Event Log")
    with st.expander("View all events"):
        for e in m.events:
            st.markdown(f"- {e}")

# ===================== TOURNAMENT TAB =====================
elif active_tab == "🏆 Tournament":
    st.markdown("# 🏆 Tournament Manager")

    if "tournament_bracket" not in st.session_state:
        st.session_state.tournament_bracket = []

    with st.container(border=True):
        st.markdown("### ➕ Create Tournament")
        t_name = st.text_input("Tournament Name", key="tnew")
        num_teams = st.selectbox("Number of Teams", [4, 8, 16], key="nteams")
        team_names = []
        cols = st.columns(2)
        for i in range(num_teams):
            with cols[i % 2]:
                t = st.text_input(f"Team {i+1}", key=f"tt{i}", value=f"Team {i+1}")
                team_names.append(t)

        if st.button("🏆 Generate Bracket", use_container_width=True):
            import random
            shuffled = team_names[:]
            random.shuffle(shuffled)
            matches = []
            for i in range(0, len(shuffled), 2):
                if i+1 < len(shuffled):
                    matches.append({"round": "Round 1", "teamA": shuffled[i], "teamB": shuffled[i+1], "winner": None})
            st.session_state.tournament_bracket = matches
            st.session_state.tournament = {"name": t_name, "teams": team_names}
            st.rerun()

    if st.session_state.tournament_bracket:
        st.write("")
        st.markdown(f"### 🎯 {st.session_state.tournament.get('name','Tournament')} Bracket")
        for i, match_b in enumerate(st.session_state.tournament_bracket):
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 2])
                with c1:
                    st.markdown(f"**{match_b['teamA']}**")
                with c2:
                    st.markdown("<div style='text-align:center;opacity:.5'>vs</div>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"**{match_b['teamB']}**")
                if not match_b["winner"]:
                    w = st.radio("Winner", [match_b["teamA"], match_b["teamB"]], key=f"bw{i}", horizontal=True)
                    if st.button("✅ Confirm", key=f"bc{i}"):
                        st.session_state.tournament_bracket[i]["winner"] = w
                        st.rerun()
                else:
                    st.markdown(f"<span class='badge badge-green'>🏆 {match_b['winner']}</span>", unsafe_allow_html=True)

# ===================== HISTORY TAB =====================
elif active_tab == "📜 Match History":
    st.markdown("# 📜 Match History")
    history = st.session_state.match_history

    if not history:
        st.info("No completed matches yet. Finish a match to see it here!")
    else:
        st.markdown(f"**{len(history)} match(es) recorded**")
        for i, h in enumerate(reversed(history)):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### {h['teamA']} vs {h['teamB']}")
                    if h.get("tournament"): st.caption(f"🏆 {h['tournament']} {h.get('round','')}")
                    st.caption(f"📅 {h['date']}")
                    sets_str = " | ".join([f"Set {j+1}: {a}–{b}" for j,(a,b) in enumerate(h.get('sets_detail',[]))])
                    st.markdown(f"Sets: {h['setsA']}–{h['setsB']}  ·  {sets_str}")
                with c2:
                    st.markdown(f"<div class='winner-banner' style='font-size:16px;padding:12px'>🏆<br>{h['winner']}</div>", unsafe_allow_html=True)

        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.match_history = []
            st.rerun()

st.caption("🏸 Ball Badminton Advanced Scoreboard | Run: streamlit run app.py")
