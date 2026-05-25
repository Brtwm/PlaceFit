"""Shared Streamlit styling."""

from __future__ import annotations

import streamlit as st


def apply_global_styles() -> None:
    """Apply dark dashboard CSS tokens for the MVP UI."""

    st.markdown(
        """
        <style>
        :root {
          --pf-bg: #080d14;
          --pf-panel: #101722;
          --pf-panel-2: #141d2a;
          --pf-panel-3: #1b2636;
          --pf-line: #283548;
          --pf-line-soft: #1d2939;
          --pf-text: #f8fafc;
          --pf-text-soft: #cbd5e1;
          --pf-muted: #94a3b8;
          --pf-accent: #ff5a5f;
          --pf-accent-soft: rgba(255, 90, 95, .16);
          --pf-teal: #2dd4bf;
          --pf-success: #22c55e;
          --pf-warning: #f59e0b;
          --pf-danger: #ef4444;
        }
        [data-testid="stSidebarNav"] {
          display: none;
        }
        .stApp {
          background:
            radial-gradient(
              circle at top left,
              rgba(45, 212, 191, .08),
              transparent 28rem
            ),
            linear-gradient(180deg, #080d14 0%, #0a1018 44%, #080d14 100%);
          color: var(--pf-text);
        }
        .block-container {
          max-width: 1480px;
          padding-top: 2.25rem;
          padding-bottom: 3rem;
        }
        h1, h2, h3, h4 {
          color: var(--pf-text);
          letter-spacing: 0;
        }
        p, li, label, span {
          color: inherit;
        }
        [data-testid="stSidebar"] {
          background: #111722;
          border-right: 1px solid var(--pf-line-soft);
        }
        .pf-sidebar-brand {
          padding: .45rem 0 .9rem;
        }
        .pf-sidebar-title {
          color: var(--pf-text);
          font-size: 1.45rem;
          font-weight: 800;
        }
        .pf-sidebar-subtitle,
        .pf-sidebar-note {
          color: var(--pf-muted);
          font-size: .86rem;
          line-height: 1.45;
        }
        .pf-page-header {
          margin-bottom: 1.15rem;
        }
        .pf-page-header h1 {
          margin: 0 0 .45rem;
          font-size: clamp(2rem, 3vw, 3rem);
          line-height: 1.05;
        }
        .pf-page-subtitle {
          color: var(--pf-muted);
          margin: 0;
          font-size: .98rem;
        }
        .pf-hero {
          background:
            linear-gradient(135deg, rgba(255, 90, 95, .24), transparent 44%),
            linear-gradient(100deg, #172033 0%, #111827 58%, #0e1622 100%);
          border: 1px solid #334155;
          border-left: 4px solid var(--pf-accent);
          border-radius: 8px;
          padding: 1.55rem 1.65rem;
          box-shadow: 0 18px 38px rgba(0, 0, 0, .22);
          margin-bottom: 1.25rem;
        }
        .pf-hero h1,
        .pf-hero h2 {
          color: var(--pf-text);
          margin: .35rem 0 .6rem;
          max-width: 980px;
        }
        .pf-hero p {
          color: var(--pf-text-soft);
          margin: 0;
          max-width: 980px;
          line-height: 1.55;
        }
        .pf-card {
          background: var(--pf-panel);
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          padding: 1.1rem 1.2rem;
          color: var(--pf-text);
          box-shadow: 0 14px 30px rgba(0, 0, 0, .18);
          margin-bottom: 1rem;
        }
        .pf-card strong {
          color: var(--pf-text);
        }
        .pf-card p,
        .pf-card .pf-muted {
          color: var(--pf-muted);
        }
        .pf-section {
          background: rgba(16, 23, 34, .72);
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          padding: 1.05rem 1rem .85rem;
          margin: 1rem 0;
        }
        .pf-section-title {
          color: var(--pf-text);
          font-size: 1.1rem;
          font-weight: 800;
          margin-bottom: .8rem;
        }
        .pf-muted {
          color: var(--pf-muted);
        }
        .pf-kicker {
          color: var(--pf-teal);
          font-size: .78rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: .08em;
        }
        .pf-metric-card {
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          padding: .95rem 1rem;
          background: linear-gradient(180deg, #151f2d 0%, #111827 100%);
          color: var(--pf-text);
          min-height: 104px;
          margin-bottom: .85rem;
        }
        .pf-metric-label {
          color: var(--pf-muted);
          font-size: .85rem;
          margin-bottom: .5rem;
        }
        .pf-metric-value {
          color: var(--pf-text);
          font-size: 1.35rem;
          font-weight: 700;
          line-height: 1.2;
          overflow-wrap: normal;
          word-break: normal;
        }
        .pf-metric-help {
          color: var(--pf-muted);
          font-size: .8rem;
          margin-top: .45rem;
        }
        .pf-row {
          padding: .72rem .85rem;
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          background: var(--pf-panel);
          color: var(--pf-text-soft);
          margin-bottom: .45rem;
        }
        .pf-badge {
          display: inline-block;
          padding: .28rem .6rem;
          border-radius: 999px;
          font-size: .78rem;
          font-weight: 700;
        }
        .pf-badge-muted {
          background: #263244;
          color: var(--pf-text-soft);
        }
        .pf-badge-good,
        .pf-status-ok {
          background: rgba(34, 197, 94, .15);
          color: #86efac;
          border: 1px solid rgba(34, 197, 94, .35);
        }
        .pf-status-error {
          background: rgba(239, 68, 68, .14);
          color: #fca5a5;
          border: 1px solid rgba(239, 68, 68, .35);
        }
        .pf-status-warning {
          background: rgba(245, 158, 11, .14);
          color: #fcd34d;
          border: 1px solid rgba(245, 158, 11, .35);
        }
        .pf-history-card {
          background: var(--pf-panel);
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          padding: 1rem;
          margin-bottom: .75rem;
          color: var(--pf-text);
        }
        .pf-history-title {
          color: var(--pf-text);
          font-weight: 800;
          margin-bottom: .35rem;
        }
        .pf-history-meta {
          color: var(--pf-muted);
          font-size: .86rem;
        }
        .pf-report {
          background: var(--pf-panel);
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          padding: 1rem 1.15rem;
          color: var(--pf-text-soft);
        }
        .pf-report h1,
        .pf-report h2,
        .pf-report h3 {
          color: var(--pf-text);
        }
        div[data-testid="stForm"] {
          background: rgba(16, 23, 34, .74);
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          padding: 1.1rem 1.15rem 1.2rem;
        }
        div[data-testid="stExpander"] {
          border-color: var(--pf-line);
          background: rgba(16, 23, 34, .58);
        }
        div[data-testid="stMetric"] {
          background: var(--pf-panel);
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          padding: .75rem .9rem;
          color: var(--pf-text);
        }
        div[data-testid="stMetricLabel"] {
          color: var(--pf-muted);
        }
        div[data-testid="stDataFrame"] {
          border: 1px solid var(--pf-line);
          border-radius: 8px;
          overflow: hidden;
        }
        .stTabs [data-baseweb="tab-list"] {
          gap: .35rem;
          border-bottom: 1px solid var(--pf-line);
        }
        .stTabs [data-baseweb="tab"] {
          color: var(--pf-text-soft);
          border-radius: 6px 6px 0 0;
        }
        .stTabs [aria-selected="true"] {
          color: var(--pf-text);
          background: var(--pf-accent-soft);
        }
        .stButton > button,
        .stFormSubmitButton > button {
          border-radius: 8px;
          font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
