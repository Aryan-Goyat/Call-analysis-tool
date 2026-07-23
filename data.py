import os
from datetime import datetime, timedelta

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import ALL, Input, Output, State, callback, dcc, html
from dotenv import load_dotenv
from groq import Groq

from db import get_engine

load_dotenv()

client = Groq(api_key=os.getenv("API_KEY"))

dash.register_page(__name__, path="/cr")

# -----------------------------------------------------------------------------
# Status / color system
# -----------------------------------------------------------------------------
ACTIVE_STATUSES = ["In Progress"]
PENDING_STATUSES = [
    "Requested",
    "Approved",
    "Pre-Migration Approved",
    "Pre-Migration Approved 1",
    "Migration date finalized",
    "Pending Further Review",
    "UAT Approved",
    "Draft",
    "Approved by Owner",
]
CLOSED_STATUSES = ["Implementation Review Closed", "Closed", "Implemented"]

BG = "#fafafa"
SURFACE = "#ffffff"
SURFACE_SUBTLE = "#f8fafc"
BORDER = "#e5e7eb"
TEXT = "#111827"
TEXT_MID = "#4b5563"
TEXT_SOFT = "#6b7280"
ACCENT = "#111111"
ACCENT_SOFT = "#2563eb"
SUCCESS = "#16a34a"
WARNING = "#d97706"
DANGER = "#dc2626"
VIOLET = "#7c3aed"
SHADOW = "0 1px 2px rgba(16,24,40,.04), 0 12px 24px rgba(16,24,40,.06)"

# Minimal monochrome palette — dark ink for emphasis, greys for everything else
RISK_COLOR_MAP = {"High": "#111827", "Medium": "#9ca3af", "Low": "#e5e7eb"}
CATEGORY_COLOR_MAP = {
    "Enhancement": "#111827",
    "Infrastructure": "#374151",
    "Data Request": "#6b7280",
    "General/Other": "#e5e7eb",
    "System Bug": "#9ca3af",
    "Access/Security": "#d1d5db",
}

STATUS_COLOR_MAP = {
    "Approved": "#374151",
    "In Progress": "#111827",
    "Canceled": "#9ca3af",
    "Pending Further Review": "#6b7280",
    "UAT Approved": "#4b5563",
    "Implementation Review Closed": "#d1d5db",
    "Draft": "#e5e7eb",
}

PAGE_CSS = """
.cr-page {
  background: #fafafa;
  min-height: 100vh;
  padding: 32px 24px 48px;
  color: #111827;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.cr-shell {
  max-width: 1440px;
  margin: 0 auto;
}
.cr-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}
.cr-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
}
.cr-title {
  margin: 10px 0 8px;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #111827;
}
.cr-subtitle {
  margin: 0;
  max-width: 760px;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.7;
}
.cr-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 10px 14px;
  color: #4b5563;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.cr-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 12px 24px rgba(16,24,40,.06);
}
.cr-card-tight {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(16,24,40,.04), 0 10px 18px rgba(16,24,40,.05);
}
.cr-toolbar {
  position: sticky;
  top: 16px;
  z-index: 20;
  margin-bottom: 22px;
}
.cr-toolbar-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
}
.cr-toolbar-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.cr-field {
  min-width: 150px;
}
.cr-field-label {
  color: #6b7280;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.cr-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.cr-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
.cr-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.cr-section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #111827;
}
.cr-section-copy {
  color: #6b7280;
  font-size: 13px;
}
.cr-kpi-label {
  color: #6b7280;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.cr-kpi-clickable {
  transition: all .15s ease;
}
.cr-kpi-clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(16,24,40,.06), 0 16px 28px rgba(16,24,40,.09);
}
.cr-kpi-arrow {
  color: #9ca3af;
  font-size: 14px;
  font-weight: 700;
  opacity: 0;
  transition: opacity .15s ease;
}
.cr-kpi-clickable:hover .cr-kpi-arrow {
  opacity: 1;
}
.cr-kpi-value {
  margin: 10px 0 6px;
  font-size: 34px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #111827;
}
.cr-kpi-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 16px;
}
.cr-kpi-note {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}
.cr-kpi-chip {
  min-width: 58px;
  text-align: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #111827;
  font-size: 12px;
  font-weight: 700;
}
.cr-btn, .cr-btn-ghost {
  border-radius: 14px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all .15s ease;
}
.cr-btn {
  background: #111827;
  color: #ffffff;
  border: 1px solid #111827;
}
.cr-btn:hover { opacity: .92; transform: translateY(-1px); }
.cr-btn-ghost {
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
}
.cr-btn-ghost:hover { background: #f9fafb; }
.cr-quick-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.cr-quick-pills button {
  border-radius: 999px;
  background: #ffffff;
  color: #4b5563;
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
}
.cr-ai-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.cr-ai-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cr-note-box {
  padding: 14px 16px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  color: #4b5563;
  font-size: 13px;
  line-height: 1.6;
}
.cr-oldest-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.cr-list-card {
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #ffffff;
  padding: 16px;
}
.cr-list-title {
  margin: 0 0 10px;
  color: #111827;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.cr-ticket summary {
  list-style: none;
}
.cr-ticket summary::-webkit-details-marker {
  display: none;
}
.cr-ticket-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  background: #ffffff;
  cursor: pointer;
}
.cr-ticket-body {
  margin-top: -2px;
  border: 1px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 18px 18px;
  background: #fcfcfd;
  padding: 16px;
}
.cr-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid transparent;
}
.cr-muted {
  color: #6b7280;
}
.cr-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 14px 0;
}
.cr-side-empty {
  color: #6b7280;
  font-size: 14px;
}
.cr-side-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.cr-side-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.03em;
}
.cr-side-subtitle {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 13px;
}
.cr-offcanvas .offcanvas-header {
  border-bottom: 1px solid #e5e7eb;
  padding: 18px 20px;
}
.cr-offcanvas .offcanvas-body {
  padding: 20px;
  background: #fafafa;
}
.DateRangePickerInput,
.DateInput,
.DateInput_input,
.SingleDatePickerInput {
  border-radius: 14px !important;
}
.DateInput_input {
  border: 1px solid #e5e7eb !important;
  color: #111827 !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  padding: 10px 12px !important;
  background: #ffffff !important;
}
.Select-control, .Select-menu-outer {
  border-radius: 14px !important;
  border-color: #e5e7eb !important;
}
@media (max-width: 1080px) {
  .cr-chart-grid, .cr-oldest-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 768px) {
  .cr-page {
    padding: 20px 14px 28px;
  }
  .cr-hero {
    flex-direction: column;
  }
}
"""

CHART_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}


# -----------------------------------------------------------------------------
# Data helpers
# -----------------------------------------------------------------------------
def categorize_cr(desc):
    desc = str(desc).lower()
    if any(w in desc for w in ["bug", "error", "fix", "issue", "fail", "not working", "incorrect"]):
        return "System Bug"
    if any(w in desc for w in ["data", "report", "extract", "query", "download"]):
        return "Data Request"
    if any(w in desc for w in ["access", "permission", "role", "password", "unlock", "vpn"]):
        return "Access/Security"
    if any(w in desc for w in ["enhance", "new", "upgrade", "update", "modify", "logic", "requirement"]):
        return "Enhancement"
    if any(w in desc for w in ["server", "storage", "migration", "patch", "os", "network", "switch"]):
        return "Infrastructure"
    return "General/Other"


def fetch_filtered_cr_data(start_date=None, end_date=None):
    engine = get_engine()
    query = """
        SELECT `Change Request Id`, `Description`, `Status`, `Risk`,
               `Owner Work Group Name`, `Request Registration Time`
        FROM cr_report
        WHERE `Owner Work Group Name` IN ('IT Support (ALC)', 'IT Support (EVSM)')
    """
    df = pd.read_sql(query, engine)

    if df.empty:
        return df

    df["Request Registration Time"] = pd.to_datetime(df["Request Registration Time"], errors="coerce")
    df = df.dropna(subset=["Request Registration Time"]).copy()
    df["Category"] = df["Description"].apply(categorize_cr)
    df["Month_Value"] = df["Request Registration Time"].dt.to_period("M").astype(str)

    if start_date and end_date:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
        df = df[(df["Request Registration Time"] >= start_dt) & (df["Request Registration Time"] <= end_dt)].copy()

    return df


try:
    INIT_DF = fetch_filtered_cr_data()
    MIN_DATE = INIT_DF["Request Registration Time"].min().date() if not INIT_DF.empty else datetime.now().date()
    MAX_DATE = INIT_DF["Request Registration Time"].max().date() if not INIT_DF.empty else datetime.now().date()
except Exception:
    INIT_DF = pd.DataFrame()
    MIN_DATE = datetime.now().date()
    MAX_DATE = datetime.now().date()


# -----------------------------------------------------------------------------
# UI helpers
# -----------------------------------------------------------------------------
def section_card(title, subtitle, graph_id=None, children=None, min_height="380px"):
    content = children if children is not None else dcc.Graph(id=graph_id, config=CHART_CONFIG, style={"height": min_height})
    return html.Div(
        [
            html.Div(
                [
                    html.Div(title, className="cr-section-title"),
                    html.Div(subtitle, className="cr-section-copy"),
                ],
                className="cr-section-head",
            ),
            content,
        ],
        className="cr-card",
        style={"padding": "18px"},
    )


def metric_card(title, value, note, pct=None, clickable_id=None):
    chip = html.Div(f"{pct}%" if pct is not None else "—", className="cr-kpi-chip")
    wrapper_props = {
        "className": "cr-card-tight cr-kpi-clickable" if clickable_id else "cr-card-tight",
        "style": {"padding": "18px", "height": "100%", "cursor": "pointer" if clickable_id else "default"},
    }
    if clickable_id:
        wrapper_props["id"] = clickable_id
    return html.Div(
        [
            html.Div(
                [
                    html.Div(title, className="cr-kpi-label"),
                    html.Span("→", className="cr-kpi-arrow") if clickable_id else None,
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "gap": "8px"},
            ),
            html.Div(str(value), className="cr-kpi-value"),
            html.Div(
                [
                    html.Div(note, className="cr-kpi-note"),
                    chip,
                ],
                className="cr-kpi-meta",
            ),
        ],
        **wrapper_props,
    )


def quick_range_button(key, label):
    return html.Button(label, id={"type": "cr-date-preset", "index": key}, className="cr-btn-ghost")


def badge(text, fg=TEXT, bg="#f3f4f6", border="#e5e7eb"):
    return html.Span(text, className="cr-badge", style={"color": fg, "background": bg, "borderColor": border})


def simple_error(message):
    return html.Div(str(message), className="cr-note-box", style={"color": DANGER, "background": "#fef2f2", "border": f"1px solid #fecaca"})


def render_ai_markdown(text):
    return html.Div(
        dcc.Markdown(text, link_target="_blank"),
        className="cr-note-box",
        style={"whiteSpace": "pre-wrap"},
    )


def oldest_cards(df, empty_message):
    if df.empty:
        return html.Div(empty_message, className="cr-note-box")

    cards = []
    for _, row in df.iterrows():
        age_days = int(row.get("age_days", 0))
        age_badge = badge(
            f"{age_days} days",
            fg="#111827" if age_days >= 30 else ("#4b5563" if age_days >= 14 else "#6b7280"),
            bg="#f3f4f6",
            border="#e5e7eb",
        )
        cards.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(f"#{row.get('Change Request Id')}", style={"fontWeight": "800", "fontSize": "14px", "color": TEXT}),
                            age_badge,
                        ],
                        style={"display": "flex", "justifyContent": "space-between", "gap": "12px", "marginBottom": "8px"},
                    ),
                    html.Div(row.get("Status", "N/A"), className="cr-muted", style={"fontSize": "12px", "marginBottom": "8px"}),
                    html.Div(str(row.get("Description", ""))[:180], style={"fontSize": "13px", "lineHeight": "1.6", "color": TEXT_MID}),
                ],
                className="cr-list-card",
            )
        )
    return html.Div(cards, style={"display": "grid", "gap": "12px"})


def base_figure(fig, height=330):
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", color=TEXT, size=12),
        margin=dict(l=12, r=12, t=18, b=12),
        height=height,
        hoverlabel=dict(bgcolor="#111827", font_color="#ffffff", bordercolor="#111827"),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#f1f5f9",
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=TEXT_SOFT),
        title_font=dict(color=TEXT_SOFT),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#f1f5f9",
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=TEXT_SOFT),
        title_font=dict(color=TEXT_SOFT),
    )
    return fig


def empty_figure(title="No data available"):
    fig = px.bar(title=title)
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        height=330,
        margin=dict(l=12, r=12, t=60, b=12),
        font=dict(family="Inter, ui-sans-serif, system-ui, sans-serif", color=TEXT),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------
def layout():
    return html.Div(
        [
            dcc.Interval(id="cr-auto-refresh-interval", interval=5 * 60 * 1000, n_intervals=0),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div("OPERATIONS / CHANGE MANAGEMENT", className="cr-eyebrow"),
                                    html.H1("Change Request Report", className="cr-title"),
                                    html.P(
                                        "A cleaner operations dashboard with minimal surfaces, tighter hierarchy, and a product-style layout inspired by modern Next.js SaaS dashboards.",
                                        className="cr-subtitle",
                                    ),
                                ]
                            ),
                            html.Div(id="cr-last-updated", className="cr-pill"),
                        ],
                        className="cr-hero",
                    ),
                    html.Div(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div("Start date", className="cr-field-label"),
                                                dcc.DatePickerSingle(
                                                    id="cr-start-date",
                                                    min_date_allowed=MIN_DATE,
                                                    max_date_allowed=MAX_DATE,
                                                    date=MIN_DATE,
                                                    display_format="DD MMM YYYY",
                                                    className="cr-field",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Div("End date", className="cr-field-label"),
                                                dcc.DatePickerSingle(
                                                    id="cr-end-date",
                                                    min_date_allowed=MIN_DATE,
                                                    max_date_allowed=MAX_DATE,
                                                    date=MAX_DATE,
                                                    display_format="DD MMM YYYY",
                                                    className="cr-field",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Div("Quick ranges", className="cr-field-label"),
                                                html.Div(
                                                    [
                                                        quick_range_button("7d", "7D"),
                                                        quick_range_button("30d", "30D"),
                                                        quick_range_button("90d", "90D"),
                                                        quick_range_button("this_month", "This Month"),
                                                        quick_range_button("this_quarter", "This Quarter"),
                                                        quick_range_button("all", "All Time"),
                                                    ],
                                                    className="cr-quick-pills",
                                                ),
                                            ],
                                            style={"flex": "1", "minWidth": "320px"},
                                        ),
                                    ],
                                    className="cr-toolbar-group",
                                ),
                                html.Div(
                                    [
                                        html.Button("Export CSV", id="cr-export-btn", className="cr-btn-ghost"),
                                        dcc.Download(id="cr-download-csv"),
                                    ],
                                    className="cr-toolbar-group",
                                ),
                            ],
                            className="cr-toolbar-inner cr-card",
                        ),
                        className="cr-toolbar",
                    ),
                    html.Div(id="cr-kpi-row", className="cr-kpi-grid"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div("AI Insights", className="cr-section-title"),
                                            html.Div("Recurring themes and suggested actions.", className="cr-section-copy"),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            dcc.Dropdown(
                                                id="cr-ai-months-dropdown",
                                                options=[
                                                    {"label": "Last 1 month", "value": 1},
                                                    {"label": "Last 3 months", "value": 3},
                                                    {"label": "Last 6 months", "value": 6},
                                                    {"label": "Last 12 months", "value": 12},
                                                    {"label": "Selected range", "value": 100},
                                                ],
                                                value=3,
                                                clearable=False,
                                                style={"width": "180px"},
                                            ),
                                            html.Button("Generate", id="cr-btn-generate-ai", className="cr-btn"),
                                        ],
                                        className="cr-ai-controls",
                                    ),
                                ],
                                className="cr-ai-head",
                            ),
                            dcc.Loading(html.Div(id="cr-ai-insights-output"), type="circle", color=ACCENT_SOFT),
                        ],
                        className="cr-card",
                        style={"padding": "18px", "marginBottom": "24px"},
                    ),
                    html.Div(
                        [
                            section_card("Monthly volume by category", "Track where demand is building month over month.", graph_id="cr-chart-month"),
                            section_card("Request categorization", "See the operational mix behind incoming change requests.", graph_id="cr-chart-category"),
                            section_card("Risk distribution", "Surface the proportion of low, medium, and high-risk requests.", graph_id="cr-chart-risk", min_height="320px"),
                            section_card("Status distribution", "Compare pipeline health across lifecycle states.", graph_id="cr-chart-status", min_height="320px"),
                            section_card("Workgroup distribution", "View request concentration by owning workgroup.", graph_id="cr-chart-workgroup"),
                            section_card("Pending aging", "Spot requests that are accumulating operational drag.", graph_id="cr-chart-aging"),
                        ],
                        className="cr-chart-grid",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div("Oldest pending requests", className="cr-section-title"),
                                    html.Div("Separate current range pressure from long-running backlog.", className="cr-section-copy"),
                                ],
                                className="cr-section-head",
                            ),
                            dcc.Loading(html.Div(id="cr-oldest-pending-output"), type="circle", color=ACCENT_SOFT),
                        ],
                        className="cr-card",
                        style={"padding": "18px", "marginTop": "24px"},
                    ),
                ],
                className="cr-shell",
            ),
            dbc.Offcanvas(
                id="cr-side-panel-container",
                placement="end",
                is_open=False,
                className="cr-offcanvas",
                title="Request drill-down",
                children=[html.Div(id="cr-side-panel-content")],
                style={"width": "560px", "backgroundColor": BG, "borderLeft": f"1px solid {BORDER}"},
            ),
        ],
        className="cr-page",
    )


# -----------------------------------------------------------------------------
# Main dashboard callback
# -----------------------------------------------------------------------------
@callback(
    Output("cr-kpi-row", "children"),
    Output("cr-chart-month", "figure"),
    Output("cr-chart-category", "figure"),
    Output("cr-chart-risk", "figure"),
    Output("cr-chart-status", "figure"),
    Output("cr-chart-workgroup", "figure"),
    Output("cr-chart-aging", "figure"),
    Output("cr-oldest-pending-output", "children"),
    Output("cr-last-updated", "children"),
    Input("cr-start-date", "date"),
    Input("cr-end-date", "date"),
    Input("cr-auto-refresh-interval", "n_intervals"),
)
def update_dashboard(start_date, end_date, _intervals):
    all_data = fetch_filtered_cr_data()

    if not all_data.empty and start_date and end_date:
        s = pd.to_datetime(start_date)
        e = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
        fdf = all_data[(all_data["Request Registration Time"] >= s) & (all_data["Request Registration Time"] <= e)].copy()
    else:
        fdf = all_data.copy()

    if not all_data.empty:
        pending_all = all_data[all_data["Status"].isin(PENDING_STATUSES)].copy()
        pending_all["age_days"] = (datetime.now() - pending_all["Request Registration Time"]).dt.days
        oldest_all = pending_all.nlargest(3, "age_days")
    else:
        oldest_all = pd.DataFrame()

    if not fdf.empty:
        pending_sel = fdf[fdf["Status"].isin(PENDING_STATUSES)].copy()
        if not pending_sel.empty:
            pending_sel["age_days"] = (datetime.now() - pending_sel["Request Registration Time"]).dt.days
            oldest_sel = pending_sel.nlargest(3, "age_days")
        else:
            oldest_sel = pd.DataFrame()
    else:
        pending_sel = pd.DataFrame()
        oldest_sel = pd.DataFrame()

    combined_oldest = html.Div(
        [
            html.Div(
                [
                    html.Div([html.Div("Selected range", className="cr-list-title"), oldest_cards(oldest_sel, "No pending items for this timeframe.")], className="cr-list-card"),
                    html.Div([html.Div("All time", className="cr-list-title"), oldest_cards(oldest_all, "No pending items overall.")], className="cr-list-card"),
                ],
                className="cr-oldest-grid",
            )
        ]
    )

    last_updated_text = ["Updated ", datetime.now().strftime("%d %b %Y · %I:%M %p")]

    if fdf.empty:
        empty_fig = empty_figure("No data available for this range")
        return (
            [
                metric_card("Active CRs", 0, "Currently in progress", 0, clickable_id="cr-kpi-active"),
                metric_card("Pending CRs", 0, "Awaiting action", 0, clickable_id="cr-kpi-pending"),
                metric_card("Resolved CRs", 0, "Successfully closed", 0, clickable_id="cr-kpi-resolved"),
                metric_card("Resolution rate", "0%", "Closed share of selected requests", 0),
                metric_card("Cancelled", 0, "Cancelled change requests", 0, clickable_id="cr-kpi-cancelled"),
            ],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            combined_oldest,
            last_updated_text,
        )

    active = int(fdf["Status"].isin(ACTIVE_STATUSES).sum())
    total_pending = int(fdf["Status"].isin(PENDING_STATUSES).sum())
    total_resolved = int(fdf["Status"].isin(CLOSED_STATUSES).sum())
    fulfilment_rate = int(total_resolved / len(fdf) * 100) if len(fdf) > 0 else 0
    cancelled = int((fdf["Status"] == "Canceled").sum())

    active_pct = round(active / len(fdf) * 100) if len(fdf) > 0 else 0
    pending_pct = round(total_pending / len(fdf) * 100) if len(fdf) > 0 else 0
    resolved_pct = round(total_resolved / len(fdf) * 100) if len(fdf) > 0 else 0
    cancelled_pct = round(cancelled / len(fdf) * 100) if len(fdf) > 0 else 0

    kpi_children = [
        metric_card("Active CRs", active, "Currently in progress", active_pct, clickable_id="cr-kpi-active"),
        metric_card("Pending CRs", total_pending, "Awaiting action", pending_pct, clickable_id="cr-kpi-pending"),
        metric_card("Resolved CRs", total_resolved, "Successfully closed", resolved_pct, clickable_id="cr-kpi-resolved"),
        metric_card("Resolution rate", f"{fulfilment_rate}%", "Closed share of selected requests", fulfilment_rate),
        metric_card("Cancelled", cancelled, "Cancelled change requests", cancelled_pct, clickable_id="cr-kpi-cancelled"),
    ]

    month_cat = fdf.groupby(["Month_Value", "Category"]).size().reset_index(name="count").sort_values("Month_Value")
    month_cat["Month_Label"] = pd.to_datetime(month_cat["Month_Value"]).dt.strftime("%b %y")
    ordered_months = month_cat["Month_Label"].unique().tolist()

    fig_month = px.bar(
        month_cat,
        x="Month_Label",
        y="count",
        color="Category",
        text="count",
        color_discrete_map=CATEGORY_COLOR_MAP,
        category_orders={"Month_Label": ordered_months},
    )
    fig_month.update_traces(textposition="outside", marker_line_width=0)
    fig_month.update_layout(
        xaxis_title="",
        yaxis_title="Volume",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        bargap=0.28,
    )
    fig_month = base_figure(fig_month)

    cat_counts = fdf["Category"].value_counts().sort_values(ascending=True).reset_index()
    cat_counts.columns = ["Category", "count"]
    fig_category = px.bar(
        cat_counts,
        y="Category",
        x="count",
        orientation="h",
        color="Category",
        color_discrete_map=CATEGORY_COLOR_MAP,
        text="count",
    )
    fig_category.update_traces(marker_line_width=0, textposition="outside")
    fig_category.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    fig_category = base_figure(fig_category)

    risk_counts = fdf["Risk"].dropna().value_counts().reset_index()
    risk_counts.columns = ["Risk", "count"]
    if risk_counts.empty:
        fig_risk = empty_figure("No risk data")
    else:
        fig_risk = px.pie(
            risk_counts,
            names="Risk",
            values="count",
            hole=0.72,
            color="Risk",
            color_discrete_map=RISK_COLOR_MAP,
        )
        fig_risk.update_traces(textinfo="percent", marker=dict(line=dict(color=SURFACE, width=3)))
        fig_risk.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5))
        fig_risk = base_figure(fig_risk, height=320)
        fig_risk.update_layout(margin_b=80)

    status_counts = fdf["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "count"]
    fig_status = px.pie(
        status_counts,
        names="Status",
        values="count",
        hole=0.72,
        color="Status",
        color_discrete_map=STATUS_COLOR_MAP,
    )
    fig_status.update_traces(textinfo="percent", marker=dict(line=dict(color=SURFACE, width=3)))
    # Use top yanchor to ensure multi-row legends grow downwards into the margin correctly
    fig_status.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5, font=dict(size=11)))
    fig_status = base_figure(fig_status, height=320)
    fig_status.update_layout(margin_b=100)

    wg_counts = fdf["Owner Work Group Name"].value_counts().sort_values(ascending=True).reset_index()
    wg_counts.columns = ["Owner Work Group Name", "count"]
    fig_workgroup = px.bar(
        wg_counts,
        y="Owner Work Group Name",
        x="count",
        orientation="h",
        text="count",
        color_discrete_sequence=["#111827"],
    )
    fig_workgroup.update_traces(marker_line_width=0, textposition="outside")
    fig_workgroup.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    fig_workgroup = base_figure(fig_workgroup)

    if not pending_sel.empty:
        bins = [0, 5, 10, 15, 30, float("inf")]
        labels = ["0-5", "6-10", "11-15", "16-30", ">30"]
        pending_sel["age_bucket"] = pd.cut(pending_sel["age_days"], bins=bins, labels=labels)
        aging_counts = pending_sel["age_bucket"].value_counts().sort_index().reset_index()
        aging_counts.columns = ["age_bucket", "count"]
        peak_bucket = aging_counts["count"].idxmax() if not aging_counts.empty else None
        bar_colors = ["#111827" if i == peak_bucket else "#e5e7eb" for i in range(len(aging_counts))]
        fig_aging = px.bar(aging_counts, x="age_bucket", y="count", text="count", category_orders={"age_bucket": labels})
        fig_aging.update_traces(marker_color=bar_colors, marker_line_width=0, textposition="outside")
        fig_aging.update_layout(xaxis_title="Days pending", yaxis_title="")
        fig_aging = base_figure(fig_aging)
    else:
        fig_aging = empty_figure("No pending CRs")

    return kpi_children, fig_month, fig_category, fig_risk, fig_status, fig_workgroup, fig_aging, combined_oldest, last_updated_text


# -----------------------------------------------------------------------------
# AI insights
# -----------------------------------------------------------------------------
@callback(
    Output("cr-ai-insights-output", "children"),
    Input("cr-btn-generate-ai", "n_clicks"),
    State("cr-start-date", "date"),
    State("cr-end-date", "date"),
    State("cr-ai-months-dropdown", "value"),
    prevent_initial_call=True,
)
def update_ai_insights(n_clicks, start_date, end_date, ai_months):
    df_full = fetch_filtered_cr_data(start_date, end_date)
    if df_full.empty:
        return html.Div("No CRs found for this time frame.", className="cr-note-box")

    if start_date and end_date and ai_months != 100:
        end_dt = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
        start_dt = end_dt - pd.DateOffset(months=ai_months)
        df_cb = df_full[(df_full["Request Registration Time"] >= start_dt) & (df_full["Request Registration Time"] <= end_dt)].copy()
    else:
        df_cb = df_full

    cr_lines = [
        f"ID: {row['Change Request Id']} | Type: {row['Category']} | Status: {row['Status']} | Risk: {row['Risk']} | Desc: {row['Description']}"
        for _, row in df_cb.iterrows()
    ]

    prompt = f"""
You are an IT Operations Analyst. Analyze these Change Requests for the ALC and EVSM workgroups.
Find ALL unique patterns. Do not limit to 3.
Respond in EXACTLY this format:

PATTERN: [4-5 word title] | [High/Medium/Low]
[One sentence detail]
Suggested action: [One sentence]

REDUCTION TIPS (only 3 total for the entire analysis, not per pattern):
- [tip 1]
- [tip 2]
- [tip 3]

Change Requests:
{chr(10).join(cr_lines)}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content
        return render_ai_markdown(text)
    except Exception as e:
        return simple_error(e)


# -----------------------------------------------------------------------------
# Drill-down panel
# -----------------------------------------------------------------------------
@callback(
    Output("cr-side-panel-content", "children"),
    Output("cr-side-panel-container", "is_open"),
    Input("cr-chart-month", "clickData"),
    Input("cr-chart-category", "clickData"),
    Input("cr-chart-risk", "clickData"),
    Input("cr-chart-status", "clickData"),
    Input("cr-chart-workgroup", "clickData"),
    Input("cr-chart-aging", "clickData"),
    State("cr-start-date", "date"),
    State("cr-end-date", "date"),
    prevent_initial_call=True,
)
def update_drilldown_side_panel(c_month, c_cat, c_risk, c_stat, c_wg, c_aging, start_date, end_date):
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]["value"] is None:
        return dash.no_update, False

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    df = fetch_filtered_cr_data(start_date, end_date)
    if df.empty:
        return html.Div("No records found.", className="cr-side-empty"), True

    df["Month_Label"] = df["Request Registration Time"].dt.strftime("%b %y")
    pending_df = df[df["Status"].isin(PENDING_STATUSES)].copy()
    if not pending_df.empty:
        pending_df["age_days"] = (datetime.now() - pending_df["Request Registration Time"]).dt.days
        pending_df["age_bucket"] = pd.cut(
            pending_df["age_days"],
            bins=[0, 5, 10, 15, 30, float("inf")],
            labels=["0-5", "6-10", "11-15", "16-30", ">30"],
        )

    filtered_df = pd.DataFrame()
    filter_text = ""
    try:
        if triggered_id == "cr-chart-month" and c_month:
            filtered_df = df[df["Month_Label"] == c_month["points"][0]["x"]]
            filter_text = f"Month: {c_month['points'][0]['x']}"
        elif triggered_id == "cr-chart-category" and c_cat:
            filtered_df = df[df["Category"] == c_cat["points"][0]["y"]]
            filter_text = f"Category: {c_cat['points'][0]['y']}"
        elif triggered_id == "cr-chart-risk" and c_risk:
            filtered_df = df[df["Risk"] == c_risk["points"][0]["label"]]
            filter_text = f"Risk: {c_risk['points'][0]['label']}"
        elif triggered_id == "cr-chart-status" and c_stat:
            filtered_df = df[df["Status"] == c_stat["points"][0]["label"]]
            filter_text = f"Status: {c_stat['points'][0]['label']}"
        elif triggered_id == "cr-chart-workgroup" and c_wg:
            filtered_df = df[df["Owner Work Group Name"] == c_wg["points"][0]["y"]]
            filter_text = f"Workgroup: {c_wg['points'][0]['y']}"
        elif triggered_id == "cr-chart-aging" and c_aging:
            filtered_df = pending_df[pending_df["age_bucket"] == c_aging["points"][0]["x"]]
            filter_text = f"Aging: {c_aging['points'][0]['x']} days"
    except (KeyError, TypeError, IndexError):
        return simple_error("Could not process selection."), True

    if filtered_df.empty:
        return html.Div("No records found.", className="cr-side-empty"), True

    ai_summary = ""
    if len(filtered_df) > 1:
        try:
            sample_descs = filtered_df["Description"].head(10).tolist()
            wg_counts = filtered_df["Owner Work Group Name"].value_counts().to_dict()
            summary_prompt = (
                f"In ONE short sentence, identify a notable pattern in these {len(filtered_df)} change requests: "
                f"workgroups {wg_counts}, sample descriptions: {sample_descs}. Be specific and concise, max 25 words."
            )
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=60,
                messages=[{"role": "user", "content": summary_prompt}],
            )
            ai_summary = response.choices[0].message.content.strip()
        except Exception:
            ai_summary = ""

    cards = []
    for _, row in filtered_df.iterrows():
        ticket_id = str(row.get("Change Request Id"))
        desc = str(row.get("Description", ""))
        cat = row.get("Category", "General")
        status_val = row.get("Status", "N/A")
        payload_text = (
            f"Category: {cat} | Risk: {row.get('Risk')} | Workgroup: {row.get('Owner Work Group Name')} | Description: {desc}"
        )
        pill_color = STATUS_COLOR_MAP.get(status_val, TEXT_SOFT)
        # Light grey pills need dark text to stay readable
        pill_fg = "#111827" if pill_color in ("#d1d5db", "#e5e7eb", "#9ca3af") else "#ffffff"

        cards.append(
            html.Details(
                [
                    html.Summary(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(f"#{ticket_id}", style={"fontWeight": "800", "fontSize": "15px", "color": TEXT}),
                                        html.Div(desc[:80] + ("…" if len(desc) > 80 else ""), className="cr-muted", style={"fontSize": "12px", "marginTop": "4px"}),
                                    ]
                                ),
                                html.Div(
                                    [
                                        badge(status_val, fg=pill_fg, bg=pill_color, border=pill_color),
                                        badge(f"Risk: {row.get('Risk', 'N/A')}", fg="#4b5563", bg="#f3f4f6", border="#e5e7eb"),
                                    ],
                                    style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "justifyContent": "flex-end"},
                                ),
                            ],
                            className="cr-ticket-head",
                        )
                    ),
                    html.Div(
                        [
                            html.Div([html.Strong("Category: "), cat], style={"marginBottom": "8px", "fontSize": "13px"}),
                            html.Div([html.Strong("Owner: "), row.get("Owner Work Group Name", "N/A")], style={"marginBottom": "8px", "fontSize": "13px"}),
                            html.Div([html.Strong("Opened: "), row.get("Request Registration Time").strftime("%d %b %Y %I:%M %p") if pd.notnull(row.get("Request Registration Time")) else "N/A"], style={"marginBottom": "8px", "fontSize": "13px"}),
                            html.Div([html.Strong("Description:"), html.P(desc, style={"marginTop": "6px", "color": TEXT_MID, "fontSize": "13px", "lineHeight": "1.7"})]),
                            html.Div(payload_text, id={"type": "ticket-payload", "index": ticket_id}, style={"display": "none"}),
                            html.Button("Generate AI action plan", id={"type": "btn-ticket-ai", "index": ticket_id}, className="cr-btn", style={"width": "100%", "marginTop": "10px"}),
                            dcc.Loading(
                                html.Div(
                                    id={"type": "ticket-ai-output", "index": ticket_id},
                                    style={"marginTop": "14px", "display": "none"},
                                ),
                                type="circle",
                                color=ACCENT_SOFT,
                            ),
                        ],
                        className="cr-ticket-body",
                    ),
                ],
                className="cr-ticket",
                style={"marginBottom": "12px"},
            )
        )

    blocks = [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3("Request drill-down", className="cr-side-title"),
                                html.P(filter_text, className="cr-side-subtitle"),
                            ]
                        ),
                        badge(f"{len(filtered_df)} items", fg="#111827", bg="#f3f4f6", border="#e5e7eb"),
                    ],
                    className="cr-side-header",
                )
            ]
        )
    ]

    if ai_summary:
        blocks.append(
            html.Div(
                [
                    html.Div("AI insight", style={"fontSize": "11px", "fontWeight": "800", "letterSpacing": ".04em", "textTransform": "uppercase", "color": TEXT_SOFT, "marginBottom": "6px"}),
                    html.Div(ai_summary, style={"fontSize": "13px", "color": TEXT, "lineHeight": "1.6"}),
                ],
                className="cr-note-box",
                style={"marginBottom": "16px"},
            )
        )

    blocks.append(html.Div(cards))
    return html.Div(blocks), True


@callback(
    Output({"type": "ticket-ai-output", "index": dash.MATCH}, "children"),
    Output({"type": "ticket-ai-output", "index": dash.MATCH}, "style"),
    Input({"type": "btn-ticket-ai", "index": dash.MATCH}, "n_clicks"),
    State({"type": "ticket-payload", "index": dash.MATCH}, "children"),
    State({"type": "ticket-ai-output", "index": dash.MATCH}, "style"),
    prevent_initial_call=True,
)
def generate_single_ticket_insight(n_clicks, payload, current_style):
    if not n_clicks:
        return dash.no_update, dash.no_update

    prompt = f"""
You are an IT Operations Expert. Review this Change Request and provide:
1. Root Cause Hypothesis: 1 sentence
2. Recommended SOP / Action: 1-2 sentences

Ticket: {payload}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        new_style = {
            **(current_style or {}),
            "display": "block",
        }
        return render_ai_markdown(response.choices[0].message.content), new_style
    except Exception as e:
        return simple_error(e), {**(current_style or {}), "display": "block"}


@callback(
    Output("cr-download-csv", "data"),
    Input("cr-export-btn", "n_clicks"),
    State("cr-start-date", "date"),
    State("cr-end-date", "date"),
    prevent_initial_call=True,
)
def export_cr_csv(n_clicks, start_date, end_date):
    df = fetch_filtered_cr_data(start_date, end_date)
    return dcc.send_data_frame(df.to_csv, "cr_report_export.csv", index=False)


@callback(
    Output("cr-start-date", "date", allow_duplicate=True),
    Output("cr-end-date", "date", allow_duplicate=True),
    Input({"type": "cr-date-preset", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def cr_date_preset(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered or all(n == 0 for n in n_clicks_list):
        return dash.no_update, dash.no_update

    import json

    trigger_id = json.loads(ctx.triggered[0]["prop_id"].rsplit(".", 1)[0])
    preset = trigger_id["index"]
    today = datetime.now().date()

    if preset == "7d":
        return (today - timedelta(days=7)).isoformat(), today.isoformat()
    if preset == "30d":
        return (today - timedelta(days=30)).isoformat(), today.isoformat()
    if preset == "90d":
        return (today - timedelta(days=90)).isoformat(), today.isoformat()
    if preset == "this_month":
        return today.replace(day=1).isoformat(), today.isoformat()
    if preset == "this_quarter":
        q_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=q_month, day=1).isoformat(), today.isoformat()
    if preset == "all":
        return MIN_DATE.isoformat() if hasattr(MIN_DATE, "isoformat") else str(MIN_DATE), MAX_DATE.isoformat() if hasattr(MAX_DATE, "isoformat") else str(MAX_DATE)

    return dash.no_update, dash.no_update


KPI_DRILLDOWN_CONFIG = {
    "cr-kpi-active": ("Active CRs", ACTIVE_STATUSES, "No active CRs."),
    "cr-kpi-pending": ("Pending CRs", PENDING_STATUSES, "No pending CRs."),
    "cr-kpi-resolved": ("Resolved CRs", CLOSED_STATUSES, "No resolved CRs."),
    "cr-kpi-cancelled": ("Cancelled CRs", ["Canceled"], "No cancelled CRs."),
}


@callback(
    Output("cr-side-panel-content", "children", allow_duplicate=True),
    Output("cr-side-panel-container", "is_open", allow_duplicate=True),
    Input("cr-kpi-active", "n_clicks"),
    Input("cr-kpi-pending", "n_clicks"),
    Input("cr-kpi-resolved", "n_clicks"),
    Input("cr-kpi-cancelled", "n_clicks"),
    State("cr-start-date", "date"),
    State("cr-end-date", "date"),
    prevent_initial_call=True,
)
def kpi_drilldown(n_active, n_pending, n_resolved, n_cancelled, start_date, end_date):
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]["value"] is None:
        return dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    config = KPI_DRILLDOWN_CONFIG.get(triggered_id)
    if config is None:
        return dash.no_update, dash.no_update
    title, statuses, empty_message = config

    df = fetch_filtered_cr_data(start_date, end_date)
    filtered_df = df[df["Status"].isin(statuses)] if not df.empty else pd.DataFrame()
    if filtered_df.empty:
        return html.Div(empty_message, className="cr-side-empty"), True

    cards = []
    for _, row in filtered_df.iterrows():
        cards.append(
            html.Div(
                [
                    html.Div(f"#{row.get('Change Request Id')}", style={"fontWeight": "800", "fontSize": "14px", "color": TEXT}),
                    html.Div(row.get("Status"), className="cr-muted", style={"fontSize": "12px", "marginTop": "4px"}),
                ],
                className="cr-list-card",
                style={"marginBottom": "10px"},
            )
        )

    return (
        html.Div(
            [
                html.Div(
                    [
                        html.H3(title, className="cr-side-title"),
                        html.P(f"{len(filtered_df)} requests in the selected range", className="cr-side-subtitle"),
                    ],
                    style={"marginBottom": "14px"},
                ),
                html.Div(cards),
            ]
        ),
        True,
    )
