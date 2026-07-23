import dash
import pandas as pd
from dash import html, dcc, callback, Output, Input, State, MATCH, ALL
import dash_bootstrap_components as dbc
import plotly.express as px
from db import get_engine
from datetime import datetime, timedelta
from groq import Groq
import os
from dotenv import load_dotenv
from utils import ttl_cache

from components import resolve_date_preset, MAX_DRILLDOWN_CARDS
from dashboard_shared import (
    section_card, metric_card, quick_range_button, badge, simple_error,
    render_ai_markdown, oldest_cards, base_figure, empty_figure,
    BG, SURFACE, BORDER, TEXT, TEXT_MID, TEXT_SOFT, ACCENT_SOFT, DANGER
)

load_dotenv()

dash.register_page(__name__, path="/incident")

client = Groq(api_key=os.getenv("API_KEY"))

PENDING_STATUSES = ["Pending"]
INCIDENT_CATEGORIES = [
    "System Bug",
    "Data Request",
    "Lack of Functional/Operational Knowledge",
    "Master Data Request",
]

@ttl_cache(seconds=120)
def _fetch_all_incident_data():
    engine = get_engine()
    query = """
        SELECT `Incident ID`, `Symptom`, `Status`, `Workgroup`, `Location`, `Classification`, `Priority`, `Log Time`
        FROM incident_report
        WHERE `Workgroup` IN ('IT Support (ALC)', 'IT Support (EVSM)')
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        df["date"] = pd.to_datetime(df["Log Time"], format="%d/%m/%Y %H:%M", errors="coerce")
        df["month_year"] = df["date"].dt.strftime("%Y-%m")
        df["month_year_label"] = df["date"].dt.strftime("%B %Y")
    return df

def fetch_filtered_incident_data(start_date=None, end_date=None):
    df = _fetch_all_incident_data()
    if not df.empty and start_date and end_date:
        start_dt = pd.to_datetime(start_date)
        end_dt   = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
        df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)].copy()
    return df

try:
    init_df = fetch_filtered_incident_data()
    MIN_DATE = init_df["date"].min().date() if not init_df.empty else datetime.now().date()
    MAX_DATE = init_df["date"].max().date() if not init_df.empty else datetime.now().date()
except Exception:
    MIN_DATE = datetime.now().date()
    MAX_DATE = datetime.now().date()

# ── Layout ────────────────────────────────────────────────────────────────────
def layout():
    return html.Div([
        dcc.Interval(id="inc-notif-interval", interval=10 * 60 * 1000, n_intervals=0),
        html.Div(id="inc-notif-trigger", style={"display": "none"}),
        dcc.Store(id="inc-aged-incidents-store"),
        
        html.Div([
            html.Div([
                html.Div([
                    html.Div("OPERATIONS / INCIDENT MANAGEMENT", className="cr-eyebrow"),
                    html.H1("Incident Report", className="cr-title"),
                    html.P("A cleaner operations dashboard with minimal surfaces, tighter hierarchy, and a product-style layout inspired by modern Next.js SaaS dashboards.", className="cr-subtitle"),
                ]),
                html.Div(id="inc-last-updated", className="cr-pill"),
            ], className="cr-hero"),
            
            html.Div(
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div("Start date", className="cr-field-label"),
                            dcc.DatePickerSingle(id="inc-start-date", min_date_allowed=MIN_DATE, max_date_allowed=MAX_DATE, date=MIN_DATE, display_format="DD MMM YYYY", className="cr-field"),
                        ]),
                        html.Div([
                            html.Div("End date", className="cr-field-label"),
                            dcc.DatePickerSingle(id="inc-end-date", min_date_allowed=MIN_DATE, max_date_allowed=MAX_DATE, date=MAX_DATE, display_format="DD MMM YYYY", className="cr-field"),
                        ]),
                        html.Div([
                            html.Div("Quick ranges", className="cr-field-label"),
                            html.Div([
                                quick_range_button("7d", "7D", "inc-date-preset"), quick_range_button("30d", "30D", "inc-date-preset"), quick_range_button("90d", "90D", "inc-date-preset"),
                                quick_range_button("this_month", "This Month", "inc-date-preset"), quick_range_button("this_quarter", "This Quarter", "inc-date-preset"), quick_range_button("all", "All Time", "inc-date-preset"),
                            ], className="cr-quick-pills"),
                        ], style={"flex": "1", "minWidth": "320px"}),
                    ], className="cr-toolbar-group"),
                    html.Div([
                        html.Button("Export CSV", id="inc-export-btn", className="cr-btn-ghost"),
                        dcc.Download(id="inc-download-csv"),
                    ], className="cr-toolbar-group"),
                ], className="cr-toolbar-inner cr-card"),
                className="cr-toolbar",
            ),
            
            html.Div(id="inc-kpi-row", className="cr-kpi-grid"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div("AI Insights", className="cr-section-title"),
                            html.Div("Recurring themes and suggested actions.", className="cr-section-copy"),
                        ]),
                        html.Div([
                            dcc.Dropdown(
                                id="inc-insights-range",
                                options=[
                                    {"label": "Last 1 week", "value": 1},
                                    {"label": "Last 4 weeks", "value": 4},
                                    {"label": "Last 12 weeks", "value": 12},
                                    {"label": "Selected range", "value": 9999},
                                ],
                                value=4, clearable=False,
                                style={"width": "180px"},
                            ),
                            html.Button("Generate", id="inc-generate-btn", className="cr-btn"),
                        ], className="cr-ai-controls"),
                    ], className="cr-ai-head"),
                    dcc.Loading(html.Div(id="inc-ai-insights-output"), type="circle", color=ACCENT_SOFT),
                ], className="cr-card", style={"padding": "18px", "marginBottom": "24px"})
            ]),
            
            html.Div([
                section_card("Monthly volume", "Track where demand is building month over month.", graph_id="inc-graph-month"),
                section_card("Location breakdown", "See the geographic distribution of incidents.", graph_id="inc-graph-location"),
                section_card("Status distribution", "Compare pipeline health across lifecycle states.", graph_id="inc-graph-status"),
                section_card("Classification distribution", "View incident concentration by classification.", graph_id="inc-graph-classification"),
                section_card("Workgroup distribution", "View incident concentration by owning workgroup.", graph_id="inc-graph-workgroup"),
            ], className="cr-chart-grid"),
            
            html.Div([
                html.Div([
                    html.Div("Oldest pending requests", className="cr-section-title"),
                    html.Div("Separate current range pressure from long-running backlog.", className="cr-section-copy"),
                ], className="cr-section-head"),
                dcc.Loading(html.Div(id="inc-oldest-incidents-panel"), type="circle", color=ACCENT_SOFT),
            ], className="cr-card", style={"padding": "18px", "marginTop": "24px"}),
            
        ], className="cr-shell"),
        
        dbc.Offcanvas(
            id="inc-side-panel-container",
            placement="end", is_open=False, className="cr-offcanvas", title="Request drill-down",
            children=[html.Div(id="inc-side-panel-content")],
            style={"width": "560px", "backgroundColor": BG, "borderLeft": f"1px solid {BORDER}"}
        ),
    ], className="cr-page")

@callback(
    Output("inc-kpi-row",              "children"),
    Output("inc-graph-month",          "figure"),
    Output("inc-graph-location",       "figure"),
    Output("inc-graph-status",         "figure"),
    Output("inc-graph-classification", "figure"),
    Output("inc-graph-workgroup",      "figure"),
    Output("inc-oldest-incidents-panel","children"),
    Output("inc-last-updated",         "children"),
    Input("inc-start-date",            "date"),
    Input("inc-end-date",              "date"),
)
def update_charts(start_date, end_date):
    all_data = fetch_filtered_incident_data()
    if not all_data.empty and start_date and end_date:
        start_dt = pd.to_datetime(start_date)
        end_dt   = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
        fdf = all_data[(all_data["date"] >= start_dt) & (all_data["date"] <= end_dt)].copy()
    else:
        fdf = all_data.copy()

    if not all_data.empty:
        pending_all = all_data[all_data["Status"].isin(PENDING_STATUSES)].copy()
        pending_all["age_days"] = (datetime.now() - pending_all["date"]).dt.days
        oldest_all  = pending_all.nlargest(3, "age_days")
    else:
        oldest_all = pd.DataFrame()

    if not fdf.empty:
        pending_sel = fdf[fdf["Status"].isin(PENDING_STATUSES)].copy()
        if not pending_sel.empty:
            pending_sel["age_days"] = (datetime.now() - pending_sel["date"]).dt.days
            oldest_sel = pending_sel.nlargest(3, "age_days")
        else:
            oldest_sel = pd.DataFrame()
    else:
        pending_sel = pd.DataFrame()
        oldest_sel = pd.DataFrame()

    combined_oldest = html.Div([
        html.Div([
            html.Div([html.Div("Selected range", className="cr-list-title"), oldest_cards(oldest_sel, "No pending items for this timeframe.", id_col="Incident ID", desc_col="Symptom", status_col="Status")], className="cr-list-card"),
            html.Div([html.Div("All time", className="cr-list-title"), oldest_cards(oldest_all, "No pending items overall.", id_col="Incident ID", desc_col="Symptom", status_col="Status")], className="cr-list-card"),
        ], className="cr-oldest-grid")
    ])

    last_updated_text = ["Updated ", datetime.now().strftime("%d %b %Y · %I:%M %p")]

    if fdf.empty:
        empty_fig = empty_figure("No data available")
        return (
            [
                metric_card("Active Incidents", 0, "Active in pipeline", 0, clickable_id="inc-kpi-active"),
                metric_card("Total Resolved", 0, "Closed successfully", 0, clickable_id="inc-kpi-resolved"),
                metric_card("Resolution rate", "0%", "Percentage of tickets successfully resolved", 0),
                metric_card("Cancelled", 0, "Total cancelled", 0, clickable_id="inc-kpi-cancelled"),
            ],
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, combined_oldest, last_updated_text
        )

    active = int(fdf["Status"].isin(PENDING_STATUSES).sum())
    res    = int(fdf["Status"].isin(["Resolved", "Closed"]).sum())
    rej    = int((fdf["Status"] == "Cancelled").sum())
    rate   = round(res / len(fdf) * 100, 1) if len(fdf) > 0 else 0

    active_pct = round(active / len(fdf) * 100) if len(fdf) > 0 else 0
    res_pct = round(res / len(fdf) * 100) if len(fdf) > 0 else 0
    rej_pct = round(rej / len(fdf) * 100) if len(fdf) > 0 else 0

    kpi_children = [
        metric_card("Active Incidents", active, "Active in pipeline", active_pct, clickable_id="inc-kpi-active"),
        metric_card("Total Resolved", res, "Closed successfully", res_pct, clickable_id="inc-kpi-resolved"),
        metric_card("Resolution rate", f"{rate}%", "Percentage of tickets successfully resolved", rate),
        metric_card("Cancelled", rej, "Total cancelled", rej_pct, clickable_id="inc-kpi-cancelled"),
    ]

    month_counts = fdf.groupby(["month_year", "month_year_label"]).size().reset_index(name="count").sort_values("month_year")
    fig_month = px.bar(month_counts, x="month_year_label", y="count", text="count")
    fig_month.update_traces(textposition="outside", marker_color="#111827", marker_line_width=0)
    fig_month = base_figure(fig_month)

    fig_location = px.bar(fdf["Location"].value_counts().reset_index(), x="Location", y="count", text="count")
    fig_location.update_traces(textposition="outside", marker_color="#111827", marker_line_width=0)
    fig_location = base_figure(fig_location)

    fig_classification = px.bar(fdf["Classification"].value_counts().reset_index(), x="Classification", y="count", text="count")
    fig_classification.update_traces(textposition="outside", marker_color="#111827", marker_line_width=0)
    fig_classification = base_figure(fig_classification)

    fig_status = px.bar(fdf["Status"].value_counts().reset_index(), x="Status", y="count", text="count")
    fig_status.update_traces(textposition="outside", marker_color="#111827", marker_line_width=0)
    fig_status = base_figure(fig_status)

    fig_workgroup = px.bar(fdf["Workgroup"].value_counts().reset_index(), x="count", y="Workgroup", orientation="h", text="count")
    fig_workgroup.update_traces(textposition="outside", marker_color="#111827", marker_line_width=0)
    fig_workgroup = base_figure(fig_workgroup)
    fig_workgroup.update_layout(yaxis={'categoryorder':'total ascending'})

    return kpi_children, fig_month, fig_location, fig_status, fig_classification, fig_workgroup, combined_oldest, last_updated_text

@callback(
    Output("inc-ai-insights-output", "children"),
    Input("inc-generate-btn",        "n_clicks"),
    State("inc-insights-range",      "value"),
    prevent_initial_call=True,
)
def update_insights(n_clicks, weeks):
    if not n_clicks: return dash.no_update
    df_cb = fetch_filtered_incident_data()
    if df_cb.empty: return simple_error("No incidents found.")

    now = df_cb["date"].max()
    if weeks == 9999:
        current  = df_cb.copy()
        previous = pd.DataFrame(columns=df_cb.columns)
    else:
        cutoff      = now - timedelta(weeks=weeks)
        current     = df_cb[df_cb["date"] >= cutoff].copy()
        prev_cutoff = cutoff - timedelta(weeks=4)
        previous    = df_cb[(df_cb["date"] >= prev_cutoff) & (df_cb["date"] < cutoff)].copy()

    if current.empty: return simple_error("No incidents found in the specified range.")

    def count_cat(frame, cat):
        if frame.empty: return 0
        return int(frame["Classification"].str.contains(cat, case=False, na=False).sum())

    cat_rows = []
    for cat in INCIDENT_CATEGORIES:
        curr_c = count_cat(current, cat)
        prev_c = count_cat(previous, cat)
        chg    = round((curr_c - prev_c) / prev_c * 100, 1) if prev_c > 0 else (100.0 if curr_c > 0 else 0.0)
        trend  = "↑" if chg > 0 else ("↓" if chg < 0 else "→")
        tc     = "#111827" if chg != 0 else TEXT_SOFT
        cat_rows.append(html.Div([
            html.Div(cat, style={"fontSize": "13px", "fontWeight": "600", "flex": "2", "color": TEXT}),
            html.Div(str(curr_c), style={"fontSize": "14px", "fontWeight": "700", "flex": "1", "textAlign": "center", "color": TEXT}),
            html.Div(f"{trend} {abs(chg)}%", style={"fontSize": "12px", "color": tc, "fontWeight": "600", "flex": "1", "textAlign": "right"}),
        ], style={"display": "flex", "alignItems": "center", "padding": "12px 0", "borderBottom": f"1px solid {BORDER}"}))

    category_panel = html.Div([
        html.Div([
            html.Div("CATEGORY", style={"fontSize": "11px", "color": TEXT_SOFT, "fontWeight": "600", "flex": "2"}),
            html.Div("COUNT", style={"fontSize": "11px", "color": TEXT_SOFT, "fontWeight": "600", "flex": "1", "textAlign": "center"}),
            html.Div("VS PREV 4W", style={"fontSize": "11px", "color": TEXT_SOFT, "fontWeight": "600", "flex": "1", "textAlign": "right"}),
        ], style={"display": "flex", "marginBottom": "4px"}),
        html.Div(cat_rows),
    ])

    open_inc = current[current["Status"].isin(PENDING_STATUSES)].copy()
    resolved_inc = df_cb[df_cb["Status"].isin(["Resolved", "Closed"])].copy()

    def find_similar(symptom, resolved_df, top_n=3):
        if pd.isna(symptom) or not str(symptom).strip() or resolved_df.empty: return []
        keywords = [w for w in str(symptom).lower().split() if len(w) > 3]
        if not keywords: return []
        mask = resolved_df["Symptom"].str.lower().apply(lambda s: any(k in str(s) for k in keywords))
        return resolved_df[mask].head(top_n)[["Symptom"]].to_dict("records")

    lines = []
    for _, row in open_inc.iterrows():
        similar = find_similar(row.get("Symptom"), resolved_inc)
        similar_text = (" | Past solutions: " + "; ".join([s.get("Symptom","") for s in similar if s.get("Symptom")])) if similar else ""
        lines.append(f"Classification: {row.get('Classification','')} | Priority: {row.get('Priority','')} | Symptom: {row.get('Symptom','')}{similar_text}")

    label = "all time" if weeks == 9999 else f"last {weeks} week(s)"
    prompt = f"""
You are an IT operations analyst. Analyze ALL these incidents from the {label}.
Categorize each into: System Bug / Data Request / Lack of Functional Knowledge / Master Data Request.
Find ALL unique patterns. Do not limit to 3.

Respond in EXACTLY this format:

PATTERN: [4-5 word title] | [High/Medium/Low]
[One sentence detail]
Suggested fix: [One sentence, use past solutions if available]

REDUCTION TIPS:
- [tip 1]
- [tip 2]
- [tip 3]

Incidents:
{chr(10).join(lines) if lines else "No open incidents — analyzing all current period incidents."}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        insights_text = response.choices[0].message.content
        ai_output = render_ai_markdown(insights_text)
    except Exception as e:
        ai_output = simple_error(e)

    return html.Div([
        html.Div([
            html.Div([
                html.Div("DETECTED PATTERNS", style={"fontSize": "11px", "color": TEXT_SOFT, "fontWeight": "600", "letterSpacing": "0.5px", "marginBottom": "12px"}),
                ai_output,
            ], style={"flex": "1.5", "paddingRight": "32px", "borderRight": f"1px solid {BORDER}"}),
            html.Div([
                html.Div("CATEGORY BREAKDOWN", style={"fontSize": "11px", "color": TEXT_SOFT, "fontWeight": "600", "letterSpacing": "0.5px", "marginBottom": "12px"}),
                category_panel,
            ], style={"flex": "1", "paddingLeft": "32px"}),
        ], style={"display": "flex", "flexWrap": "wrap"}),
    ])

@callback(
    Output("inc-aged-incidents-store", "data"),
    Input("inc-notif-interval",        "n_intervals"),
)
def check_aged_incidents(n):
    return []

@callback(
    Output("inc-side-panel-content",   "children"),
    Output("inc-side-panel-container", "is_open"),
    Input("inc-graph-month",           "clickData"),
    Input("inc-graph-location",        "clickData"),
    Input("inc-graph-status",          "clickData"),
    Input("inc-graph-classification",  "clickData"),
    Input("inc-graph-workgroup",       "clickData"),
    State("inc-start-date",            "date"),
    State("inc-end-date",              "date"),
    prevent_initial_call=True,
)
def inc_drilldown_panel(c_month, c_loc, c_stat, c_class, c_wg, start_date, end_date):
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]["value"] is None: return dash.no_update, False
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    df = fetch_filtered_incident_data(start_date, end_date)
    df["month_year_label"] = df["date"].dt.strftime("%B %Y")
    
    filtered_df, filter_text = pd.DataFrame(), ""
    try:
        if triggered_id == "inc-graph-month" and c_month: filtered_df = df[df["month_year_label"] == c_month["points"][0]["x"]]; filter_text = f"Month: {c_month['points'][0]['x']}"
        elif triggered_id == "inc-graph-location" and c_loc: filtered_df = df[df["Location"] == c_loc["points"][0]["x"]]; filter_text = f"Location: {c_loc['points'][0]['x']}"
        elif triggered_id == "inc-graph-classification" and c_class: filtered_df = df[df["Classification"] == c_class["points"][0]["x"]]; filter_text = f"Classification: {c_class['points'][0]['x']}"
        elif triggered_id == "inc-graph-status" and c_stat: filtered_df = df[df["Status"] == c_stat["points"][0]["x"]]; filter_text = f"Status: {c_stat['points'][0]['x']}"
        elif triggered_id == "inc-graph-workgroup" and c_wg: filtered_df = df[df["Workgroup"] == c_wg["points"][0]["y"]]; filter_text = f"Workgroup: {c_wg['points'][0]['y']}"
    except Exception: return simple_error("Could not process selection."), True

    if filtered_df.empty: return html.Div("No records found.", className="cr-note-box"), True

    cards = []
    for _, row in filtered_df.head(MAX_DRILLDOWN_CARDS).iterrows():
        tid, desc, status_val = str(row.get("Incident ID", "")), str(row.get("Symptom", "")), row.get("Status", "N/A")
        payload = f"Classification: {row.get('Classification')} | Location: {row.get('Location')} | Workgroup: {row.get('Workgroup')} | Symptom: {desc}"
        cards.append(html.Details([
            html.Summary([html.Div([
                html.Span(f"#{tid}", style={"fontWeight": "600", "fontSize": "15px", "color": TEXT}),
                badge(status_val)
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"})], className="cr-ticket-head"),
            html.Div([
                html.Div([html.B("Location: "), str(row.get("Location", "N/A"))], style={"marginBottom": "8px"}),
                html.Div([html.B("Classification: "), str(row.get("Classification", "N/A"))], style={"marginBottom": "8px"}),
                html.Div([html.B("Symptom:"), html.P(desc, style={"marginTop": "4px", "color": TEXT_MID, "fontSize": "13px"})]),
                html.Div(payload, id={"type": "inc-ticket-payload", "index": tid}, style={"display": "none"}),
                html.Button("Generate AI Action Plan", id={"type": "inc-btn-ticket-ai", "index": tid}, className="cr-btn", style={"marginTop": "12px", "width": "100%"}),
                dcc.Loading(html.Div(id={"type": "inc-ticket-ai-output", "index": tid}, style={"marginTop": "16px", "display": "none"}), type="circle", color=ACCENT_SOFT)
            ], className="cr-ticket-body"),
        ], className="cr-ticket", style={"marginBottom": "8px"}))

    return html.Div([
        html.Div(f"{len(filtered_df)} items for '{filter_text}' (showing first {MAX_DRILLDOWN_CARDS})" if len(filtered_df) > MAX_DRILLDOWN_CARDS else f"{len(filtered_df)} items for '{filter_text}'",
                 style={"fontWeight": "600", "marginBottom": "20px", "color": TEXT, "fontSize": "15px"}),
        html.Div(cards),
    ]), True

@callback(
    Output({"type": "inc-ticket-ai-output", "index": MATCH}, "children"),
    Output({"type": "inc-ticket-ai-output", "index": MATCH}, "style"),
    Input({"type": "inc-btn-ticket-ai", "index": MATCH}, "n_clicks"),
    State({"type": "inc-ticket-payload", "index": MATCH}, "children"),
    State({"type": "inc-ticket-ai-output", "index": MATCH}, "style"),
    prevent_initial_call=True,
)
def inc_ticket_insight(n_clicks, payload, current_style):
    if not n_clicks: return dash.no_update, dash.no_update
    prompt = f"You are an IT Operations Expert. Review this Incident and provide:\n**1. Root Cause Hypothesis:** (1 sentence)\n**2. Recommended SOP / Action:** (1-2 sentences)\n\nTicket: {payload}"
    try:
        response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        return render_ai_markdown(response.choices[0].message.content), {**current_style, "display": "block"}
    except Exception as e:
        return simple_error(e), {**current_style, "display": "block"}

@callback(
    Output("inc-download-csv", "data"), Input("inc-export-btn", "n_clicks"),
    State("inc-start-date", "date"), State("inc-end-date", "date"), prevent_initial_call=True,
)
def export_inc_csv(n_clicks, start_date, end_date):
    df = fetch_filtered_incident_data(start_date, end_date)
    return dcc.send_data_frame(df.to_csv, "incident_report_export.csv", index=False)

INC_KPI_DRILLDOWN_CONFIG = {
    "inc-kpi-active": ("Active Incidents", PENDING_STATUSES, "No active incidents."),
    "inc-kpi-resolved": ("Resolved Incidents", ["Resolved", "Closed"], "No resolved incidents."),
    "inc-kpi-cancelled": ("Cancelled Incidents", ["Cancelled"], "No cancelled incidents."),
}

@callback(
    Output("inc-side-panel-content", "children", allow_duplicate=True),
    Output("inc-side-panel-container", "is_open", allow_duplicate=True),
    Input("inc-kpi-active", "n_clicks"),
    Input("inc-kpi-resolved", "n_clicks"),
    Input("inc-kpi-cancelled", "n_clicks"),
    State("inc-start-date", "date"),
    State("inc-end-date", "date"),
    prevent_initial_call=True,
)
def inc_kpi_drilldown(n_active, n_resolved, n_cancelled, start_date, end_date):
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]["value"] is None:
        return dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    config = INC_KPI_DRILLDOWN_CONFIG.get(triggered_id)
    if config is None:
        return dash.no_update, dash.no_update
    title, statuses, empty_message = config

    df = fetch_filtered_incident_data(start_date, end_date)
    filtered_df = df[df["Status"].isin(statuses)] if not df.empty else pd.DataFrame()
    if filtered_df.empty:
        return html.Div(empty_message, className="cr-side-empty"), True

    cards = []
    for _, row in filtered_df.head(MAX_DRILLDOWN_CARDS).iterrows():
        cards.append(html.Div([
            html.Div(f"#{row.get('Incident ID')}", style={"fontWeight": "800", "fontSize": "14px", "color": TEXT}),
            html.Div(row.get("Status"), className="cr-muted", style={"fontSize": "12px", "marginTop": "4px"}),
            html.Div(str(row.get("Symptom", ""))[:120], style={"fontSize": "13px", "color": TEXT_MID, "marginTop": "6px"}),
        ], className="cr-list-card", style={"marginBottom": "10px"}))

    subtitle = f"{len(filtered_df)} incidents in the selected range"
    if len(filtered_df) > MAX_DRILLDOWN_CARDS:
        subtitle += f" (showing first {MAX_DRILLDOWN_CARDS})"

    return html.Div([
        html.Div([
            html.H3(title, className="cr-side-title"),
            html.P(subtitle, className="cr-side-subtitle"),
        ], style={"marginBottom": "14px"}),
        html.Div(cards),
    ]), True

@callback(
    Output("inc-start-date", "date", allow_duplicate=True),
    Output("inc-end-date", "date", allow_duplicate=True),
    Input({"type": "inc-date-preset", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def inc_date_preset(n_clicks_list):
    return resolve_date_preset(n_clicks_list, MIN_DATE, MAX_DATE)
