import dash
from dash import html, dcc, callback, Output, Input, State, MATCH
import time
from datetime import datetime
import pandas as pd
import logging
from sqlalchemy import text, bindparam
from db import get_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

dash.register_page(__name__, path="/notifications", name="Notifications")

# -----------------------------------------------------------------------------
# Minimal visual system
# -----------------------------------------------------------------------------
BG = "#fafafa"
SURFACE = "#ffffff"
SURFACE_SUBTLE = "#f8fafc"
BORDER = "#e5e7eb"
TEXT = "#111827"
TEXT_MID = "#4b5563"
TEXT_SOFT = "#6b7280"
INK = "#111111"
ACCENT = "#2563eb"
SUCCESS = "#16a34a"
WARNING = "#d97706"
DANGER = "#dc2626"
SHADOW = "0 1px 2px rgba(16,24,40,.04), 0 12px 24px rgba(16,24,40,.06)"



# Data extraction configurations
ALERT_CONFIGS = [
    {
        "source": "CR",
        "table": "cr_report",
        "wg_col": "`Owner Work Group Name`",
        "id_col": "Change Request Id",
        "title_col": "Description",
        "date_col": "Request Registration Time",
        "priority_col": "Risk",
        "date_fmt": None,
        "statuses": [
            "Requested", "Approved", "Pre-Migration Approved", "Pre-Migration Approved 1",
            "Migration date finalized", "Pending Further Review", "UAT Approved", "Draft", "Approved by Owner"
        ],
        "min_age": 14,
        "critical_age": 30,
        "prefix": "CR-"
    },
    {
        "source": "SR",
        "table": "sr_report",
        "wg_col": "`Workgroup`",
        "id_col": "Service Request ID",
        "title_col": "Subject",
        "date_col": "LogTime",
        "date_fmt": "%m/%d/%Y %H:%M",
        "statuses": ["In-Progress", "Pending", "Pending for Approval"],
        "min_age": 5,
        "critical_age": 10,
        "prefix": "SR-"
    },
    {
        "source": "Incident",
        "table": "incident_report",
        "wg_col": "`Workgroup`",
        "id_col": "Incident ID",
        "title_col": "Symptom",
        "date_col": "Log Time",
        "priority_col": "Priority",
        "date_fmt": "%d/%m/%Y %H:%M",
        "statuses": ["In-Progress", "Pending", "Open"],
        "min_age": 1,
        "critical_age": 7,
        "prefix": "INC-"
    }
]


def fetch_alerts():
    """Pull aged items from all three tables utilizing optimized SQL queries."""
    alerts = []
    error_occurred = False
    now = datetime.now()

    engine = get_engine()

    for config in ALERT_CONFIGS:
        try:
            pri_col_sql = f", `{config['priority_col']}` as `PriVal`" if "priority_col" in config else ", NULL as `PriVal`"
            query = text(f"""
                SELECT `{config['id_col']}`, `{config['title_col']}`, `Status`, `{config['date_col']}`{pri_col_sql}
                FROM {config['table']}
                WHERE {config['wg_col']} IN ('IT Support (ALC)', 'IT Support (EVSM)')
                  AND `Status` IN :statuses
            """).bindparams(bindparam("statuses", expanding=True))

            df = pd.read_sql(query, engine, params={"statuses": config["statuses"]})

            if not df.empty:
                if config["date_fmt"]:
                    df["_date"] = pd.to_datetime(df[config["date_col"]], format=config["date_fmt"], errors="coerce")
                else:
                    df["_date"] = pd.to_datetime(df[config["date_col"]], errors="coerce")

                df["_age"] = (now - df["_date"]).dt.days
                df_aged = df[df["_age"] >= config["min_age"]]

                for _, row in df_aged.iterrows():
                    age = int(row["_age"]) if pd.notna(row["_age"]) else 0
                    pri_val = str(row.get("PriVal", "")).lower()

                    if "critical" in pri_val or "high" in pri_val or "1" in pri_val:
                        level = "critical"
                    elif "medium" in pri_val or "2" in pri_val or "3" in pri_val:
                        level = "high"
                    elif "low" in pri_val or "4" in pri_val:
                        level = "medium"
                    else:
                        level = "critical" if age > config["critical_age"] else "warning"

                    alerts.append({
                        "id": f"{config['prefix']}{row.get(config['id_col'], '')}",
                        "source": config["source"],
                        "title": str(row.get(config['title_col'], ""))[:90],
                        "age": age,
                        "status": str(row.get("Status", "")),
                        "level": level,
                        "time": str(row["_date"].date()) if pd.notna(row["_date"]) else "",
                        "read": False,
                    })
        except Exception as e:
            logger.error(f"Error fetching {config['source']} alerts: {e}")
            error_occurred = True

    sorted_alerts = sorted(alerts, key=lambda x: x["age"], reverse=True)
    return sorted_alerts, error_occurred


def metric_card(label, value, note, chip_text=None, tone="default"):
    tone_map = {
        "default": {"value": TEXT, "chip_bg": "#f3f4f6", "chip_fg": TEXT},
        "critical": {"value": DANGER, "chip_bg": "#fef2f2", "chip_fg": DANGER},
        "accent": {"value": TEXT, "chip_bg": "#eff6ff", "chip_fg": ACCENT},
        "warning": {"value": WARNING, "chip_bg": "#fff7ed", "chip_fg": WARNING},
    }
    colors = tone_map.get(tone, tone_map["default"])

    chip = None
    if chip_text:
        chip = html.Div(
            chip_text,
            className="notif-kpi-chip",
            style={"background": colors["chip_bg"], "color": colors["chip_fg"]},
        )

    return html.Div(
        [
            html.Div(label, className="notif-kpi-label"),
            html.Div(str(value), className="notif-kpi-value", style={"color": colors["value"]}),
            html.Div(note, className="notif-kpi-note"),
            chip,
        ],
        className="notif-card notif-kpi",
    )


def source_badge_style(source):
    styles = {
        "CR": {"background": "#eff6ff", "color": "#1d4ed8", "border": "1px solid #bfdbfe"},
        "SR": {"background": "#ecfdf5", "color": "#047857", "border": "1px solid #a7f3d0"},
        "Incident": {"background": "#fff7ed", "color": "#c2410c", "border": "1px solid #fed7aa"},
    }
    return styles.get(source, {"background": "#f3f4f6", "color": TEXT_MID, "border": f"1px solid {BORDER}"})


def level_badge_style(level):
    styles = {
        "critical": {"background": "#fef2f2", "color": "#b91c1c", "border": "1px solid #fecaca"},
        "high": {"background": "#fff7ed", "color": "#b45309", "border": "1px solid #fed7aa"},
        "medium": {"background": "#fffbeb", "color": "#a16207", "border": "1px solid #fde68a"},
        "warning": {"background": "#f8fafc", "color": "#475569", "border": "1px solid #cbd5e1"},
        "low": {"background": "#f0fdf4", "color": "#15803d", "border": "1px solid #bbf7d0"},
    }
    return styles.get(level, styles["warning"])


def marker_color(level, is_read=False):
    if is_read:
        return "#d1d5db"
    return {
        "critical": DANGER,
        "high": WARNING,
        "medium": "#ca8a04",
        "warning": "#64748b",
        "low": SUCCESS,
    }.get(level, "#64748b")


def filter_button_style(active=False):
    if active:
        return {
            "background": INK,
            "color": "white",
            "border": f"1px solid {INK}",
            "padding": "9px 14px",
            "borderRadius": "999px",
            "cursor": "pointer",
            "fontWeight": "700",
            "fontSize": "12px",
            "transition": "all .15s ease",
        }
    return {
        "background": SURFACE,
        "color": TEXT_MID,
        "border": f"1px solid {BORDER}",
        "padding": "9px 14px",
        "borderRadius": "999px",
        "cursor": "pointer",
        "fontWeight": "700",
        "fontSize": "12px",
        "transition": "all .15s ease",
    }


def alert_card(alert):
    is_read = alert.get("read", False)
    source_style = source_badge_style(alert.get("source"))
    level_style = level_badge_style(alert.get("level", "warning"))

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        className="notif-marker",
                        style={"background": marker_color(alert.get("level", "warning"), is_read=is_read)},
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(alert["title"], className="notif-item-title"),
                                ],
                                className="notif-title-row",
                            ),
                            html.Div(alert["id"], className="notif-item-id"),
                            html.Div(
                                f"{alert.get('status', 'Open')} • Opened {alert.get('time', '')}",
                                className="notif-meta",
                            ),
                            html.Div(
                                [
                                    html.Span(alert.get("source", "Unknown"), className="notif-badge", style=source_style),
                                    html.Span(alert.get("level", "warning").title(), className="notif-badge", style=level_style),
                                ],
                                className="notif-badges",
                            ),
                        ],
                        className="notif-copy",
                    ),
                ],
                className="notif-main",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(str(alert["age"]), className="notif-age-value"),
                            html.Span("days", className="notif-age-label"),
                        ],
                        className="notif-age",
                    ),
                    html.Button(
                        "Snooze 7d",
                        id={"type": "snooze-btn", "index": alert["id"]},
                        n_clicks=0,
                        className="notif-snooze",
                    ),
                ],
                className="notif-side",
            ),
        ],
        className=f"notif-row{' is-read' if is_read else ''}",
    )


def layout():
    alerts, error = fetch_alerts()
    timestamp = datetime.now().strftime("%d %b %Y · %H:%M")

    return html.Div(
        className="notif-page",
        children=[
            dcc.Interval(id="notif-interval", interval=5 * 60 * 1000, n_intervals=0),
            html.Div(
                className="notif-shell",
                children=[
                    html.Div(
                        className="notif-hero",
                        children=[
                            html.Div(
                                [
                                    html.Div("Operations Inbox", className="notif-eyebrow"),
                                    html.H1("Notifications", className="notif-title"),
                                    html.P(
                                        "Monitor aging CR, SR, and Incident items in one clean queue. Prioritize the oldest risks, filter quickly, and keep the list intentionally lightweight.",
                                        className="notif-subtitle",
                                    ),
                                ]
                            ),
                            html.Div(
                                className="notif-meta-stack",
                                children=[
                                    html.Div(id="topbar-count", className="notif-pill"),
                                    html.Div("Auto refresh · every 5 min", className="notif-pill"),
                                    html.Div(id="notif-last-refresh", children=f"Last sync · {timestamp}", className="notif-pill"),
                                ],
                            ),
                        ],
                    ),
                    html.Div(id="error-banner", style={"display": "none"}),
                    html.Div(
                        className="notif-kpi-grid",
                        children=[
                            html.Div(id="kpi-card-total"),
                            html.Div(id="kpi-card-critical"),
                            html.Div(id="kpi-card-cr"),
                            html.Div(id="kpi-card-sr"),
                            html.Div(id="kpi-card-inc"),
                        ],
                    ),
                    html.Div(
                        className="notif-toolbar notif-card",
                        children=[
                            html.Div(
                                className="notif-toolbar-inner",
                                children=[
                                    html.Div(
                                        className="notif-toolbar-group",
                                        children=[
                                            html.Button("All", id="filter-all", n_clicks=0, style=filter_button_style(True)),
                                            html.Button("CR", id="filter-cr", n_clicks=0, style=filter_button_style(False)),
                                            html.Button("SR", id="filter-sr", n_clicks=0, style=filter_button_style(False)),
                                            html.Button("Incident", id="filter-incident", n_clicks=0, style=filter_button_style(False)),
                                        ],
                                    ),
                                    html.Div(
                                        className="notif-toolbar-group",
                                        children=[
                                            dcc.Input(
                                                id="notif-search",
                                                type="search",
                                                placeholder="Search ticket, status, title",
                                                className="notif-search-input",
                                            ),
                                            dcc.Dropdown(
                                                id="notif-sort",
                                                options=[
                                                    {"label": "Longest Open", "value": "age_desc"},
                                                    {"label": "Newest First", "value": "date_desc"},
                                                    {"label": "Oldest First", "value": "date_asc"},
                                                    {"label": "Highest Priority", "value": "priority"},
                                                ],
                                                value="age_desc",
                                                clearable=False,
                                                className="notif-select",
                                                style={"width": "170px", "fontSize": "13px"},
                                            ),
                                            html.Button(
                                                "Mark all read",
                                                id="mark-read-btn",
                                                n_clicks=0,
                                                style={
                                                    "background": SURFACE,
                                                    "color": TEXT,
                                                    "border": f"1px solid {BORDER}",
                                                    "borderRadius": "14px",
                                                    "padding": "10px 14px",
                                                    "fontSize": "13px",
                                                    "fontWeight": "700",
                                                    "cursor": "pointer",
                                                },
                                            ),
                                            html.Button(
                                                "Refresh",
                                                id="notif-refresh-btn",
                                                n_clicks=0,
                                                style={
                                                    "background": INK,
                                                    "color": "white",
                                                    "border": f"1px solid {INK}",
                                                    "borderRadius": "14px",
                                                    "padding": "10px 14px",
                                                    "fontSize": "13px",
                                                    "fontWeight": "700",
                                                    "cursor": "pointer",
                                                },
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),
                    html.Div(
                        className="notif-card notif-list-shell",
                        children=html.Div(id="notif-list", className="notif-list"),
                    ),
                ],
            ),
            dcc.Store(id="notif-filter", data="All"),
            dcc.Store(id="notif-page-store", data=alerts),
            dcc.Store(id="notif-error-store", data=error),
            dcc.Store(id="snoozed-alerts-store", storage_type="local", data={}),
        ],
    )


@callback(
    Output("notif-list", "children"),
    Output("topbar-count", "children"),
    Output("kpi-card-total", "children"),
    Output("kpi-card-critical", "children"),
    Output("kpi-card-cr", "children"),
    Output("kpi-card-sr", "children"),
    Output("kpi-card-inc", "children"),
    Output("error-banner", "style"),
    Output("error-banner", "children"),
    Output("global-notif-store", "data"),
    Output("notif-page-store", "data"),
    Output("filter-all", "children"),
    Output("filter-cr", "children"),
    Output("filter-sr", "children"),
    Output("filter-incident", "children"),
    Output("filter-all", "style"),
    Output("filter-cr", "style"),
    Output("filter-sr", "style"),
    Output("filter-incident", "style"),
    Output("notif-filter", "data"),
    Output("notif-last-refresh", "children"),
    Input("filter-all", "n_clicks"),
    Input("filter-cr", "n_clicks"),
    Input("filter-sr", "n_clicks"),
    Input("filter-incident", "n_clicks"),
    Input("notif-search", "value"),
    Input("notif-sort", "value"),
    Input("mark-read-btn", "n_clicks"),
    Input("notif-refresh-btn", "n_clicks"),
    Input("notif-interval", "n_intervals"),
    State("notif-page-store", "data"),
    State("notif-error-store", "data"),
    State("snoozed-alerts-store", "data"),
    State("notif-filter", "data"),
    prevent_initial_call=False,
)
def filter_notifications(
    btn_all,
    btn_cr,
    btn_sr,
    btn_inc,
    search_text,
    sort_val,
    mark_read,
    refresh,
    n_intervals,
    stored_alerts,
    stored_error,
    snoozed,
    current_filter,
):
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

    if triggered in ["notif-refresh-btn", "notif-interval"]:
        alerts, has_error = fetch_alerts()
    else:
        alerts = stored_alerts if stored_alerts is not None else []
        has_error = stored_error

    if triggered == "mark-read-btn":
        alerts = [{**a, "read": True} for a in alerts]

    source_filter = current_filter or "All"
    if triggered == "filter-all":
        source_filter = "All"
    elif triggered == "filter-cr":
        source_filter = "CR"
    elif triggered == "filter-sr":
        source_filter = "SR"
    elif triggered == "filter-incident":
        source_filter = "Incident"

    snoozed = snoozed or {}
    now = time.time()
    alerts = [a for a in alerts if not (a["id"] in snoozed and snoozed[a["id"]] > now)]

    total = len(alerts)
    critical = sum(1 for a in alerts if a["level"] == "critical")
    by_src = {
        "CR": sum(1 for a in alerts if a["source"] == "CR"),
        "SR": sum(1 for a in alerts if a["source"] == "SR"),
        "Incident": sum(1 for a in alerts if a["source"] == "Incident"),
    }

    filtered = alerts
    if search_text:
        st = search_text.lower().strip()
        filtered = [
            a for a in filtered
            if st in str(a.get("id", "")).lower()
            or st in str(a.get("title", "")).lower()
            or st in str(a.get("status", "")).lower()
            or st in str(a.get("source", "")).lower()
        ]

    if source_filter != "All":
        filtered = [a for a in filtered if a["source"] == source_filter]

    if sort_val == "age_desc":
        filtered = sorted(filtered, key=lambda x: x["age"], reverse=True)
    elif sort_val == "date_desc":
        filtered = sorted(filtered, key=lambda x: x["time"], reverse=True)
    elif sort_val == "date_asc":
        filtered = sorted(filtered, key=lambda x: x["time"])
    elif sort_val == "priority":
        level_score = {"critical": 4, "high": 3, "medium": 2, "warning": 1, "low": 0}
        filtered = sorted(
            filtered,
            key=lambda x: (level_score.get(x.get("level", "low"), 0), x["age"]),
            reverse=True,
        )

    if not filtered:
        cards = [
            html.Div(
                [
                    html.Div("✓", className="notif-empty-icon"),
                    html.Div("No notifications", className="notif-empty-title"),
                    html.Div("Everything in the queue looks under control right now.", className="notif-empty-copy"),
                ],
                className="notif-empty",
            )
        ]
    else:
        cards = [alert_card(a) for a in filtered]

    error_style = {"display": "none"}
    error_content = ""
    if has_error:
        error_style = {"display": "block"}
        error_content = html.Div(
            "Database connection failed or queries timed out. The queue may be incomplete or slightly outdated.",
            className="notif-banner",
        )

    pct_crit = int(critical / total * 100) if total > 0 else 0
    pct_cr = int(by_src["CR"] / total * 100) if total > 0 else 0
    pct_sr = int(by_src["SR"] / total * 100) if total > 0 else 0
    pct_inc = int(by_src["Incident"] / total * 100) if total > 0 else 0

    kpi_tot = metric_card("Total alerts", total, "Across all monitored systems", chip_text="Live queue", tone="default")
    kpi_cri = metric_card("Critical", critical, f"{pct_crit}% of active alerts", chip_text="Immediate attention", tone="critical")
    kpi_cr_card = metric_card("Change requests", by_src["CR"], f"{pct_cr}% of queue", chip_text="CR workload", tone="accent")
    kpi_sr_card = metric_card("Service requests", by_src["SR"], f"{pct_sr}% of queue", chip_text="SR workload", tone="default")
    kpi_inc_card = metric_card("Incidents", by_src["Incident"], f"{pct_inc}% of queue", chip_text="Incident workload", tone="warning")

    style_all = filter_button_style(source_filter == "All")
    style_cr = filter_button_style(source_filter == "CR")
    style_sr = filter_button_style(source_filter == "SR")
    style_inc = filter_button_style(source_filter == "Incident")
    timestamp = datetime.now().strftime("%d %b %Y · %H:%M")

    return (
        cards,
        f"{total} active alerts",
        kpi_tot,
        kpi_cri,
        kpi_cr_card,
        kpi_sr_card,
        kpi_inc_card,
        error_style,
        error_content,
        alerts,
        alerts,
        f"All · {total}",
        f"CR · {by_src['CR']}",
        f"SR · {by_src['SR']}",
        f"Incident · {by_src['Incident']}",
        style_all,
        style_cr,
        style_sr,
        style_inc,
        source_filter,
        f"Last sync · {timestamp}",
    )


@callback(
    Output("snoozed-alerts-store", "data"),
    Input({"type": "snooze-btn", "index": MATCH}, "n_clicks"),
    State("snoozed-alerts-store", "data"),
    prevent_initial_call=True,
)
def snooze_alert(n_clicks, snoozed):
    if not n_clicks:
        return dash.no_update
    alert_id = dash.ctx.triggered_id["index"]
    snoozed = snoozed or {}
    snoozed[alert_id] = time.time() + (7 * 24 * 3600)
    return snoozed
