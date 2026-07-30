from pathlib import Path
from typing import Optional
import sys
import time
import tempfile
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import json

PROJ_ROOT = Path(__file__).resolve().parents[1]
if str(PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJ_ROOT))

try:
    from src.analysis.pipeline import run_full_analysis
    from src.analysis.minhash_similarity import compare_resumes
    from src.parsing.pdf_parser_improved import extract_text_from_pdf
    from src.parsing.docx_parser import extract_text_from_docx
    from src.database import AuthService, ResumeRepository, SkillRepository, init_supabase
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

UPLOADS_DIR = PROJ_ROOT / "app" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="AI Resume Analyzer Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Theme ---

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    :root {
        --bg-main: #f7efe6;
        --surface: rgba(255, 252, 247, 0.96);
        --surface-strong: #fffdf9;
        --border: rgba(31, 41, 55, 0.09);
        --border-strong: rgba(31, 41, 55, 0.14);
        --text-main: #1f2937;
        --text-soft: #4b5563;
        --text-faint: #6b7280;
        --brand: #ff7a18;
        --brand-deep: #de5f00;
        --accent: #2f8fd8;
        --danger: #e24d4d;
        --danger-soft: rgba(226, 77, 77, 0.10);
        --success: #1f9b7b;
        --success-soft: rgba(31, 155, 123, 0.10);
        --info: #3b82f6;
        --info-soft: rgba(59, 130, 246, 0.10);
        --warning: #f59e0b;
        --warning-soft: rgba(245, 158, 11, 0.10);
        --shadow-soft: 0 20px 45px rgba(15, 23, 42, 0.10);
        --shadow-card: 0 12px 24px rgba(15, 23, 42, 0.08);
    }

    * {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .stApp {
        color: var(--text-main);
        background: linear-gradient(135deg, #fff8ee 0%, #f4efe7 100%);
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background-image:
            linear-gradient(rgba(255, 122, 24, 0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(47, 143, 216, 0.06) 1px, transparent 1px);
        background-size: 40px 40px;
        mask-image: radial-gradient(circle at 20% 0%, rgba(0,0,0,0.35), transparent 60%);
        opacity: 1;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 1.5rem;
        position: relative;
        z-index: 1;
    }

    .page-shell {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 24px;
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(18px);
        border-top: 3px solid var(--brand);
    }

    .auth-stage {
        background: linear-gradient(180deg, #fffdf9 0%, #f8efe6 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 34px;
        min-height: 100%;
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow-card);
    }

    .auth-stage::before {
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 2px;
        background: repeating-linear-gradient(90deg, var(--brand) 0 18px, transparent 18px 26px);
    }

    .auth-stage::after {
        content: "";
        position: absolute;
        width: 1px;
        height: 100%;
        left: 48px;
        top: 0;
        background: var(--border);
    }

    .auth-stage-inner {
        position: relative;
        z-index: 1;
    }

    .auth-stage-kicker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 2px;
        background: rgba(242, 169, 60, 0.08);
        border: 1px solid rgba(242, 169, 60, 0.28);
        color: var(--brand);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 22px;
    }

    .auth-stage-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.85rem;
        line-height: 1.02;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.02em;
        max-width: 520px;
        margin-bottom: 18px;
    }

    .auth-stage-copy {
        max-width: 520px;
        color: var(--text-soft);
        font-size: 0.98rem;
        line-height: 1.8;
        margin-bottom: 28px;
    }

    .auth-highlight-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1px;
        margin-bottom: 28px;
        background: var(--border);
        border: 1px solid var(--border);
    }

    .auth-highlight-card {
        background: #0f1319;
        border: none;
        border-radius: 0;
        padding: 18px;
    }

    .auth-highlight-value {
        color: var(--brand);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.5rem;
        font-weight: 600;
        line-height: 1;
        margin-bottom: 8px;
    }

    .auth-highlight-label {
        color: var(--text-faint);
        font-size: 0.8rem;
        line-height: 1.5;
    }

    .auth-proof {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .auth-proof-chip {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 9px 12px;
        border-radius: 2px;
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border-strong);
        color: var(--text-soft);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .dashboard-shell {
        display: flex;
        flex-direction: column;
        gap: 26px;
    }

    .hero-grid {
        display: grid;
        grid-template-columns: 1.45fr 0.9fr;
        gap: 22px;
        align-items: stretch;
    }

    .hero-card {
        background: linear-gradient(160deg, #fffdf9 0%, #f8efe6 100%);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 32px;
        color: var(--text-main);
        min-height: 220px;
        box-shadow: var(--shadow-card);
        position: relative;
        overflow: hidden;
    }

    .hero-card::after {
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 3px;
        background: linear-gradient(90deg, var(--brand) 0%, var(--accent) 100%);
    }

    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 2px;
        background: rgba(242, 169, 60, 0.08);
        border: 1px solid rgba(242, 169, 60, 0.28);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 600;
        color: var(--brand);
        margin-bottom: 18px;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        line-height: 1.12;
        font-weight: 700;
        margin: 0 0 14px 0;
        max-width: 580px;
        color: var(--brand-deep);
    }

    .hero-copy {
        margin: 0;
        max-width: 560px;
        color: var(--text-soft);
        font-size: 0.98rem;
        line-height: 1.7;
    }

    .hero-side-card {
        background: linear-gradient(180deg, #fffdf9 0%, #f8efe6 100%);
        border-radius: 18px;
        border: 1px solid var(--border);
        padding: 26px 24px;
        box-shadow: var(--shadow-card);
        border-left: 3px solid var(--accent);
    }

    .hero-side-label {
        color: var(--text-faint);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        margin-bottom: 10px;
    }

    .hero-side-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.25rem;
        line-height: 1.3;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 10px;
    }

    .hero-side-copy {
        color: var(--text-soft);
        line-height: 1.65;
        font-size: 0.92rem;
        margin-bottom: 18px;
    }

    .mini-stat {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 12px 0;
        border-top: 1px dashed var(--border-strong);
        color: var(--text-soft);
        font-size: 0.88rem;
    }

    .mini-stat strong {
        color: var(--brand);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1rem;
    }

    .login-container {
        max-width: none;
        margin: 0;
        background: transparent;
        border-radius: 0;
        padding: 0;
        box-shadow: none;
        animation: none;
    }

    .login-header {
        margin-bottom: 26px;
        text-align: left;
    }

    .login-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--text-main);
        line-height: 1.05;
        letter-spacing: -0.02em;
        margin-bottom: 14px;
    }

    .login-subtitle {
        color: var(--text-soft);
        font-size: 1rem;
        line-height: 1.7;
        max-width: 520px;
    }

    .login-feature-list {
        display: grid;
        gap: 12px;
        margin-top: 22px;
    }

    .login-feature-item {
        display: flex;
        align-items: center;
        gap: 12px;
        color: var(--text-soft);
        font-size: 0.95rem;
    }

    .login-feature-dot {
        width: 8px;
        height: 8px;
        border-radius: 1px;
        background: var(--brand);
    }

    .login-form-shell,
    .content-card {
        background: rgba(255, 252, 247, 0.95);
        border-radius: 18px;
        padding: 24px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-card);
    }

    .login-form-shell {
        background: linear-gradient(180deg, #fffdf9 0%, #f8efe6 100%);
        padding: 30px;
        position: relative;
        overflow: hidden;
    }

    .login-form-shell::before {
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 2px;
        background: linear-gradient(90deg, var(--brand) 0%, var(--accent) 100%);
    }

    .auth-form-heading {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-main);
        letter-spacing: -0.01em;
        margin-bottom: 8px;
        text-align: center;
    }

    .auth-form-copy {
        color: var(--text-soft);
        line-height: 1.7;
        margin-bottom: 22px;
        text-align: center;
    }

    div[data-testid="stVerticalBlock"]:has(.auth-form-heading) [data-baseweb="tab-list"] {
        justify-content: center;
    }

    div[data-testid="stVerticalBlock"]:has(.auth-form-heading) [data-baseweb="tab"] {
        flex: 0 0 auto;
    }

    .dashboard-container {
        max-width: 100%;
        margin: 0 auto;
        padding: 0;
        background: transparent;
        border-radius: 0;
        box-shadow: none;
        margin-top: 0;
    }

    .stat-card {
        background: linear-gradient(180deg, #fffdf9 0%, #fdf6eb 100%);
        padding: 22px;
        border-radius: 16px;
        min-height: 168px;
        color: var(--text-main);
        box-shadow: var(--shadow-card);
        transition: border-color 0.2s ease, transform 0.2s ease;
        border: 1px solid var(--border);
        border-top: 3px solid var(--brand);
        position: relative;
        overflow: hidden;
    }

    .stat-card:hover {
        transform: translateY(-2px);
    }

    .stat-card:hover {
        border-color: var(--border-strong);
    }

    .stat-number {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2.2rem;
        font-weight: 600;
        margin: 14px 0 8px;
        line-height: 1;
        color: var(--text-main);
    }

    .stat-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: var(--brand);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 600;
    }

    .stat-copy {
        color: var(--text-soft);
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--brand);
        margin: 0 0 8px 0;
        letter-spacing: -0.01em;
        border: none;
        padding: 0;
    }

    .section-subtext {
        color: var(--text-soft);
        margin-bottom: 22px;
        line-height: 1.65;
    }

    .stButton > button {
        background: transparent;
        color: var(--brand);
        border: 1px solid var(--brand);
        border-radius: 999px;
        padding: 0.82rem 1.2rem;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 0.84rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
        box-shadow: none;
        min-height: 3rem;
        width: 100%;
    }

    .stButton > button:hover {
        background: var(--brand);
        color: #ffffff;
        transform: translateY(-1px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: transparent;
        padding: 0;
        border: none;
        border-bottom: 1px solid var(--border);
        border-radius: 0;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 48px;
        background: transparent;
        border-radius: 0;
        padding: 12px 20px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        font-size: 0.85rem;
        color: var(--text-soft);
        border: none;
        border-bottom: 2px solid transparent;
    }

    .stTabs [aria-selected="true"] {
        background: transparent;
        color: var(--brand);
        border-bottom: 2px solid var(--brand);
        box-shadow: none;
    }

    .stTextInput label, .stSelectbox label, .stFileUploader label {
        color: var(--text-soft) !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }

    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid var(--border-strong);
        background: var(--surface-strong);
        color: var(--text-main);
        padding: 14px 16px;
        font-size: 0.98rem;
        min-height: 48px;
        line-height: 1.4;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--brand);
        box-shadow: 0 0 0 3px rgba(255, 122, 24, 0.16);
    }

    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 1px solid var(--border-strong);
        background: var(--surface-strong);
        color: var(--text-main);
        padding: 14px 16px;
        font-size: 0.98rem;
        min-height: 140px;
        line-height: 1.5;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    .stTextArea > div > div > textarea:focus {
        border-color: var(--brand);
        box-shadow: 0 0 0 3px rgba(255, 122, 24, 0.16);
    }

    [data-testid="stTextInputInstructions"],
    [data-testid="stTextAreaInstructions"] {
        display: none !important;
    }

    .stSelectbox > div > div {
        border-radius: 12px;
        border: 1px solid var(--border-strong);
        background: var(--surface-strong);
        min-height: 48px;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: linear-gradient(135deg, #fffdf9 0%, #f8f0e6 100%);
        border: 1.5px dashed var(--border-strong);
        border-radius: 14px;
        padding: 22px;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--brand);
    }

    .skill-badge {
        display: inline-block;
        background: rgba(79, 209, 197, 0.08);
        color: var(--accent);
        padding: 6px 10px;
        border-radius: 2px;
        margin: 0 6px 6px 0;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        font-size: 0.78rem;
        border: 1px solid rgba(79, 209, 197, 0.28);
        box-shadow: none;
    }

    .skill-badge::before {
        content: "[ ";
    }

    .skill-badge::after {
        content: " ]";
    }

    .skill-badge-missing {
        color: var(--danger);
        background: rgba(239, 100, 97, 0.08);
        border-color: rgba(239, 100, 97, 0.28);
    }

    .success-box, .warning-box, .info-box {
        padding: 14px 16px;
        border-radius: 2px;
        margin: 14px 0;
        font-weight: 500;
        font-size: 0.92rem;
        border: 1px solid transparent;
        border-left-width: 3px;
        box-shadow: none;
    }

    .success-box {
        color: var(--success);
        background: var(--success-soft);
        border-left-color: var(--success);
    }

    .warning-box {
        color: var(--warning);
        background: var(--warning-soft);
        border-left-color: var(--warning);
    }

    .info-box {
        color: var(--info);
        background: var(--info-soft);
        border-left-color: var(--info);
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent) 0%, var(--brand) 100%);
    }

    .stProgress > div > div > div {
        background: rgba(255,255,255,0.06);
    }

    [data-testid="stExpander"] {
        border: 1px solid rgba(255, 122, 24, 0.18);
        border-radius: 14px;
        background: linear-gradient(180deg, #fffdf9 0%, #f8efe6 100%);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
        overflow: hidden;
    }

    .streamlit-expanderHeader {
        background: transparent;
        border-radius: 0;
        font-weight: 700;
        color: var(--brand-deep);
    }

    [data-testid="stMetric"] {
        background: #12161d;
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 12px 16px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-soft);
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.08em;
    }

    [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.7rem;
        font-weight: 600;
        color: var(--brand);
    }

    .sign-out-btn button {
        background: transparent !important;
        color: var(--text-soft) !important;
        border: 1px solid var(--border-strong) !important;
        padding: 0.82rem 1rem !important;
        font-size: 0.85rem !important;
        box-shadow: none !important;
    }

    .sign-out-btn button:hover {
        background: rgba(239, 100, 97, 0.08) !important;
        color: var(--danger) !important;
        border-color: var(--danger) !important;
    }

    .chart-card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 14px;
    }

    [data-testid="stDataFrame"] {
        background: #12161d;
        border: 1px solid var(--border);
        border-radius: 4px;
        overflow: hidden;
    }

    hr {
        border: none;
        height: 1px;
        background: repeating-linear-gradient(90deg, var(--border-strong) 0 8px, transparent 8px 14px);
        margin: 28px 0;
    }

    @media (max-width: 992px) {
        .hero-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 768px) {
        .page-shell, .login-form-shell, .content-card {
            padding: 18px;
            border-radius: 4px;
        }

        .auth-stage {
            padding: 24px;
        }

        .auth-stage-title {
            font-size: 2.1rem;
        }

        .hero-card {
            padding: 24px;
            min-height: unset;
        }

        .hero-title {
            font-size: 1.6rem;
        }
        .login-title {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'auth'
    if 'auth_service' not in st.session_state:
        try:
            init_supabase()
            st.session_state.auth_service = AuthService()
            st.session_state.resume_repo = ResumeRepository()
            st.session_state.skill_repo = SkillRepository()
        except Exception as e:
            st.error(f"Database connection error: {e}")
            st.stop()

# --- Authentication Page ---

def show_auth_page():
    _left, center, _right = st.columns([1, 1.05, 1], gap="large")

    with center:
        st.markdown("""
        <div class="auth-form-heading">Welcome to AI Resume Analyzer</div>
        <div class="auth-form-copy">Access your analysis workspace or create a new account to start building a more polished resume pipeline.</div>
        """, unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:
            with st.form("signin_form", clear_on_submit=False):
                email = st.text_input("Email Address", placeholder="your.email@example.com", key="signin_email")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="signin_password")
                submit = st.form_submit_button("Sign In", use_container_width=True)

                if submit:
                    if email and password:
                        with st.spinner("Signing in..."):
                            result = st.session_state.auth_service.sign_in(email, password)
                            if result['success']:
                                st.session_state.authenticated = True
                                st.session_state.user = result['user']
                                st.session_state.page = 'dashboard'
                                st.success("Success: " + result['message'])
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Sign in failed: " + result['message'])
                    else:
                        st.warning("Please fill in all fields")

        with tab2:
            with st.form("signup_form", clear_on_submit=False):
                full_name = st.text_input("Full Name", placeholder="Your name", key="signup_name")
                email = st.text_input("Email Address", placeholder="your.email@example.com", key="signup_email")
                password = st.text_input("Password", type="password", placeholder="Choose a strong password", key="signup_password")
                password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", key="signup_confirm")
                submit = st.form_submit_button("Create Account", use_container_width=True)

                if submit:
                    if all([full_name, email, password, password_confirm]):
                        if password == password_confirm:
                            if len(password) >= 6:
                                with st.spinner("Creating account..."):
                                    result = st.session_state.auth_service.sign_up(email, password, full_name)
                                    if result['success']:
                                        st.success("Success: " + result['message'])
                                        st.info("Next step: use the Sign In tab to access your account")
                                    else:
                                        st.error("Account creation failed: " + result['message'])
                            else:
                                st.error("Password must be at least 6 characters")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.warning("Please fill in all fields")

# --- Dashboard ---

def show_dashboard():
    """Show redesigned dashboard"""
    st.markdown('<div class="dashboard-container"><div class="page-shell dashboard-shell">', unsafe_allow_html=True)

    user_name = st.session_state.user.email.split('@')[0].title() if st.session_state.user else "User"
    stats = st.session_state.resume_repo.get_resume_statistics(st.session_state.user.id)

    hero_col, side_col = st.columns([1.55, 0.85], gap="large")
    with hero_col:
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-kicker">Professional Workspace</div>
            <div class="hero-title">Welcome back, {user_name}.</div>
            <p class="hero-copy">
                Review uploaded resumes, track match quality over time, and uncover the next skills that will improve alignment for your target roles.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with side_col:
        st.markdown(f"""
        <div class="hero-side-card">
            <div class="hero-side-label">Snapshot</div>
            <div class="hero-side-title">Your resume lab is active.</div>
            <div class="hero-side-copy">Everything below stays connected to the same upload, analytics, and history workflows you already have.</div>
            <div class="mini-stat"><span>Latest average match</span><strong>{stats['average_match_score']}%</strong></div>
            <div class="mini-stat"><span>Total analyses stored</span><strong>{stats['total_analyses']}</strong></div>
            <div class="mini-stat"><span>Distinct skills captured</span><strong>{stats['unique_skills']}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="sign-out-btn">', unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.auth_service.sign_out()
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.page = 'auth'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Resumes</div>
            <div class="stat-number">{stats['total_resumes']}</div>
            <div class="stat-copy">Stored resume submissions available for review and comparison.</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Analyses Done</div>
            <div class="stat-number">{stats['total_analyses']}</div>
            <div class="stat-copy">Completed role-fit evaluations captured in your workspace.</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Average Match</div>
            <div class="stat-number">{stats['average_match_score']}%</div>
            <div class="stat-copy">Current average fit score across your saved analyses.</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Unique Skills</div>
            <div class="stat-number">{stats['unique_skills']}</div>
            <div class="stat-copy">Distinct skill tags extracted from your uploaded resumes.</div>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Upload & Analyze", "My Resumes", "Analytics", "Compare Resumes"])

    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        show_upload_section()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        show_my_resumes()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        show_analytics()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        show_resume_comparison()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

def show_upload_section():
    """Upload and analyze resume section â€” NEW pipeline (Stages 3-16)"""
    st.markdown('<div class="section-header">Upload Your Resume</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtext">Upload a PDF or DOCX resume, choose a target role, and get an AI-powered match analysis.</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Choose your resume file",
        type=["pdf", "docx"],
        help="Upload your resume for AI-powered analysis"
    )

    # Hardcoded role list for now (Stage 5) â€” free-text input planned for later
    ROLE_OPTIONS = [
        "Web Developer",
        "Data Scientist",
        "Backend Developer",
        "Machine Learning Engineer",
        "IT Security Manager",
        "DevOps Engineer",
    ]

    if uploaded:
        ts = time.strftime("%Y%m%d-%H%M%S")
        safe_name = uploaded.name.replace(" ", "_")
        saved_path = UPLOADS_DIR / f"{ts}__{safe_name}"

        with saved_path.open("wb") as f:
            f.write(uploaded.getbuffer())

        st.markdown('<div class="success-box">Resume uploaded successfully.</div>', unsafe_allow_html=True)

        chosen = st.text_input("Enter Target Role", placeholder="e.g. Web Developer, Data Scientist, Doctor...")
        run_clicked = st.button("Analyze Resume")

        if run_clicked:
            with st.spinner("Analyzing Resume , please wait ...."):
                try:
                    result = run_full_analysis(str(saved_path), chosen)
                except Exception as e:
                    st.markdown(f'<div class="warning-box">Analysis failed: {str(e)}</div>', unsafe_allow_html=True)
                    if saved_path.exists():
                        saved_path.unlink()
                    return

                resume_record = st.session_state.resume_repo.save_resume(
                    user_id=st.session_state.user.id,
                    filename=uploaded.name,
                    file_type=uploaded.type.split('/')[-1],
                    raw_text=result["raw_text"],
                    parsed_data=result["resume_structured"],
                    file_size=uploaded.size
                )

                if resume_record:
                    st.session_state.resume_repo.save_full_analysis(
                        user_id=st.session_state.user.id,
                        resume_id=resume_record['id'],
                        target_role=chosen,
                        matched_skills=result["matched_skills"],
                        missing_skills=result["missing_skills"],
                        extra_skills=result["extra_skills"],
                        section_scores=result["section_scores"],
                        overall_score=result["overall_score"],
                        recommendations=result["recommendations"],
                    )

            st.session_state["last_result"] = result
            st.session_state["last_role"] = chosen

            if saved_path.exists():
                saved_path.unlink()

    # Display last result (persists across reruns within the session)
    result = st.session_state.get("last_result")
    if result:
        chosen = st.session_state.get("last_role", "")

        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown('<div class="section-header">Extracted Information</div>', unsafe_allow_html=True)

            skills = result["resume_structured"].get("skills", [])
            edu = result["resume_structured"].get("education", [])
            exp = result["resume_structured"].get("experience", [])

            st.markdown("**Skills Found**")
            if skills:
                skills_html = " ".join([f'<span class="skill-badge">{s}</span>' for s in skills[:20]])
                st.markdown(skills_html, unsafe_allow_html=True)
                if len(skills) > 20:
                    st.info(f"+ {len(skills) - 20} more skills")
            else:
                st.markdown('<div class="warning-box">No skills were detected in this resume.</div>', unsafe_allow_html=True)

            st.markdown("<br>**Education**", unsafe_allow_html=True)
            if edu:
                for e in edu[:3]:
                    st.write(f"- {e}")
            else:
                st.caption("No education details were extracted from this resume.")

            st.markdown("<br>**Experience**", unsafe_allow_html=True)
            if exp:
                for e in exp[:3]:
                    st.write(f"- {e}")
            else:
                st.caption("No experience details were extracted from this resume.")

        with col2:
            st.markdown('<div class="section-header">Role Analysis</div>', unsafe_allow_html=True)
            st.markdown(f"**Target Role:** {chosen}")

            overall_pct = result["overall_score"] * 100
            overall_progress = max(0, min(100, int(round(overall_pct))))

            st.markdown(f"<br>**Overall Match: {overall_pct:.1f}%**", unsafe_allow_html=True)
            st.progress(overall_progress)

            st.markdown("<br>**Section Breakdown**", unsafe_allow_html=True)
            for section, score in result["section_scores"].items():
                pct = score * 100
                progress_value = max(0, min(100, int(round(pct))))
                st.markdown(f"{section.title()}: {pct:.1f}%")
                st.progress(progress_value)

        st.markdown("---")

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown('<div class="section-header">Matched Skills</div>', unsafe_allow_html=True)
            matched = result["matched_skills"]
            if matched:
                matched_html = " ".join([f'<span class="skill-badge">{s}</span>' for s in matched])
                st.markdown(matched_html, unsafe_allow_html=True)
            else:
                st.caption("No exact skill matches found for the selected role.")

        with col2:
            st.markdown('<div class="section-header">Skills to Learn</div>', unsafe_allow_html=True)
            missing = result["missing_skills"]
            if missing:
                missing_html = " ".join([f'<span class="skill-badge skill-badge-missing">{s}</span>' for s in missing])
                st.markdown(missing_html, unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-box">Perfect match. No missing skills were identified.</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-header">Recommendations</div>', unsafe_allow_html=True)
        recommendations = result.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                st.write(f"- {rec}")
        else:
            st.caption("No recommendations to show â€” no missing skills were detected.")

def show_my_resumes():
    """Show user's uploaded resumes"""
    st.markdown('<div class="section-header">Your Resume History</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtext">Review previously uploaded resumes, inspect extracted skills, and remove outdated entries when needed.</div>', unsafe_allow_html=True)

    resumes = st.session_state.resume_repo.get_user_resumes(st.session_state.user.id)

    if not resumes:
        st.markdown('<div class="info-box">No resumes yet. Upload your first resume in the Upload & Analyze tab.</div>', unsafe_allow_html=True)
        return

    for resume in resumes:
        with st.expander(f"{resume['filename']} - {resume['upload_date'][:10]}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("File Size", f"{resume['file_size'] / 1024:.1f} KB")

            with col2:
                skills_count = len(json.loads(resume['parsed_skills'])) if isinstance(resume['parsed_skills'], str) else len(resume['parsed_skills'])
                st.metric("Skills", skills_count)

            with col3:
                st.metric("Type", resume['file_type'].upper())

            skills = json.loads(resume['parsed_skills']) if isinstance(resume['parsed_skills'], str) else resume['parsed_skills']
            if skills:
                st.markdown("<br>**Skills**", unsafe_allow_html=True)
                skills_html = " ".join([f'<span class="skill-badge">{skill}</span>' for skill in skills[:15]])
                st.markdown(skills_html, unsafe_allow_html=True)

            if st.button("Delete Resume", key=f"del_{resume['id']}", use_container_width=True):
                deleted = st.session_state.resume_repo.delete_resume(resume['id'], st.session_state.user.id)
                if deleted:
                    st.success("Resume deleted.")
                    st.rerun()
                else:
                    st.error("Could not delete this resume. Please try again.")

def show_analytics():
    """Show analytics and visualizations"""
    st.markdown('<div class="section-header">Your Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtext">Monitor match trends, see which roles you analyze most often, and surface your strongest results at a glance.</div>', unsafe_allow_html=True)

    analyses = st.session_state.resume_repo.get_user_analyses(st.session_state.user.id, limit=50)

    if not analyses:
        st.markdown('<div class="info-box">No analyses yet. Complete your first resume analysis to unlock analytics.</div>', unsafe_allow_html=True)
        return

    df = pd.DataFrame(analyses)
    df['analysis_date'] = pd.to_datetime(df['analysis_date'], errors='coerce')
    df['match_score'] = pd.to_numeric(df['match_score'], errors='coerce').fillna(0).clip(0, 100)
    df = df.dropna(subset=['analysis_date']).sort_values('analysis_date')

    if df.empty:
        st.markdown('<div class="info-box">No valid match-score history is available yet.</div>', unsafe_allow_html=True)
        return

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="chart-card-title">Match Score Progress</div>', unsafe_allow_html=True)
        fig = px.line(
            df,
            x='analysis_date',
            y='match_score',
            title='Your Improvement Over Time',
            markers=True,
            labels={'match_score': 'Match Score (%)', 'analysis_date': 'Date'}
        )
        fig.update_traces(line_color='#f2a93c', line_width=3, marker=dict(size=9, color='#4fd1c5'))
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="IBM Plex Sans", color="#eef1f4"),
            margin=dict(l=10, r=10, t=60, b=10),
            title_font=dict(size=18, family="Space Grotesk"),
            xaxis=dict(showgrid=False, color="#9aa4b2"),
            yaxis=dict(gridcolor='rgba(238, 241, 244, 0.08)', range=[0, 100], color="#9aa4b2")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="chart-card-title">Roles Analyzed</div>', unsafe_allow_html=True)
        role_counts = df['target_role'].value_counts()
        fig = px.pie(
            values=role_counts.values,
            names=role_counts.index,
            title='Distribution of Analyzed Roles'
        )
        fig.update_traces(marker=dict(colors=['#f2a93c', '#4fd1c5', '#6ea8d8', '#ef6461', '#9aa4b2', '#d6871f']))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="IBM Plex Sans", color="#eef1f4"),
            margin=dict(l=10, r=10, t=60, b=10),
            title_font=dict(size=18, family="Space Grotesk")
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="chart-card-title">Top Performing Analyses</div>', unsafe_allow_html=True)
    top_analyses = df.nlargest(5, 'match_score')[['target_role', 'match_score', 'analysis_date']]
    top_analyses['analysis_date'] = top_analyses['analysis_date'].dt.strftime('%Y-%m-%d')
    top_analyses.columns = ['Role', 'Match Score (%)', 'Date']
    st.dataframe(top_analyses, use_container_width=True, hide_index=True)

def _extract_text_from_upload(uploaded_file) -> Optional[str]:
    """
    Save an uploaded file (pdf/docx/txt) to a temp path and run it through
    the project's existing parsers, matching the same extraction logic
    used by the main Upload & Analyze pipeline.
    """
    if uploaded_file is None:
        return None

    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".txt":
        return uploaded_file.read().decode("utf-8", errors="ignore")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            return extract_text_from_pdf(tmp_path)
        elif suffix == ".docx":
            return extract_text_from_docx(tmp_path)
        else:
            return None
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _similarity_label(pct: float) -> tuple:
    """Map a similarity percentage to a plain-language label and color class."""
    if pct >= 70:
        return "Very High — likely templated or copied", "warning-box"
    elif pct >= 40:
        return "High — significant shared wording", "warning-box"
    elif pct >= 15:
        return "Moderate — some overlapping content", "info-box"
    else:
        return "Low — largely distinct resumes", "success-box"


def show_resume_comparison():
    """Compare two resumes for overlap/templating using hand-implemented MinHash / Jaccard similarity."""
    st.markdown('<div class="section-header">Compare Two Resumes</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtext">Check how similar or templated two resumes are — useful for spotting near-duplicate submissions or copied/boilerplate content.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("**Resume A**")
        file_a = st.file_uploader("Upload Resume A (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], key="cmp_file_a")
        text_a = st.text_area("...or paste Resume A text", height=220, key="cmp_text_a")

    with col2:
        st.markdown("**Resume B**")
        file_b = st.file_uploader("Upload Resume B (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], key="cmp_file_b")
        text_b = st.text_area("...or paste Resume B text", height=220, key="cmp_text_b")

    with st.expander("Advanced settings"):
        st.caption("Lower shingle size = catches shared vocabulary/topics. Higher = only flags exact shared phrasing.")
        num_perm = st.slider("Number of hash functions (permutations)", 16, 256, 128, step=16, key="cmp_num_perm")
        k = st.slider("Shingle size (word k-gram)", 1, 6, 1, key="cmp_k")

    if st.button("Compare Resumes", key="cmp_btn"):
        with st.spinner("Extracting text..."):
            extracted_a = _extract_text_from_upload(file_a)
            extracted_b = _extract_text_from_upload(file_b)

        resume_a = (extracted_a or text_a or "").strip()
        resume_b = (extracted_b or text_b or "").strip()

        if file_a is not None and not extracted_a:
            st.markdown('<div class="warning-box">Could not extract text from Resume A. The file may be scanned/image-based, corrupted, or password-protected.</div>', unsafe_allow_html=True)
            return

        if file_b is not None and not extracted_b:
            st.markdown('<div class="warning-box">Could not extract text from Resume B. The file may be scanned/image-based, corrupted, or password-protected.</div>', unsafe_allow_html=True)
            return

        if not resume_a or not resume_b:
            st.markdown('<div class="warning-box">Please provide both resumes (upload a .pdf/.docx/.txt file or paste text) before comparing.</div>', unsafe_allow_html=True)
            return

        result = compare_resumes(resume_a, resume_b, num_perm=num_perm, k=k)
        pct = result["estimated_jaccard"] * 100
        label, css_class = _similarity_label(pct)

        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("Resume Similarity", f"{pct:.1f}%")
        st.markdown(f'<div class="{css_class}">{label}</div>', unsafe_allow_html=True)

def show_footer():
    st.markdown("""
    <style>
        .footer {
            width: 100%;
            margin-top: 40px;
            padding: 24px 28px;
            background: linear-gradient(135deg, #fff8ed 0%, #f4ebdc 100%);
            border: 1px solid rgba(255, 122, 24, 0.16);
            border-radius: 16px 16px 0 0;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
            text-align: center;
        }

        .footer a {
            color: var(--brand-deep);
            text-decoration: none;
            font-weight: 600;
            margin: 0 10px;
        }

        .footer a:hover {
            color: var(--accent);
        }

        .footer p {
            margin: 6px 0;
            color: var(--text-soft);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.85rem;
        }
    </style>

    <div class="footer">
        <p><strong>Built by Abiral Chalise, Pucar Ojha and Suprim Ghimire</strong></p>
        <p>AI Resume Analyzer Pro</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application logic"""
    init_session_state()

    if not st.session_state.authenticated:
        show_auth_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()

show_footer()