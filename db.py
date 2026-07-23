from dash import html, dcc
import plotly.express as px
import pandas as pd

BG = "#fafafa"
SURFACE = "#ffffff"
BORDER = "#e5e7eb"
TEXT = "#111827"
TEXT_MID = "#4b5563"
TEXT_SOFT = "#6b7280"
ACCENT_SOFT = "#2563eb"
DANGER = "#dc2626"

def section_card(title, subtitle, graph_id=None, children=None, min_height="380px"):
    body = dcc.Loading(dcc.Graph(id=graph_id, config={"displayModeBar": False, "responsive": True}), type="circle", color=ACCENT_SOFT) if graph_id else children
    return html.Div([
        html.Div([
            html.Div(title, className="cr-section-title"),
            html.Div(subtitle, className="cr-section-copy"),
        ], className="cr-section-head"),
        html.Div(body, style={"minHeight": min_height, "display": "flex", "flexDirection": "column", "justifyContent": "center"})
    ], className="cr-card", style={"padding": "18px"})

def metric_card(title, value, note, pct=None, clickable_id=None):
    chip = html.Div(f"{pct}%" if pct is not None else "—", className="cr-kpi-chip")
    wrapper_props = {
        "className": "cr-card-tight cr-kpi-clickable" if clickable_id else "cr-card-tight",
        "style": {"padding": "18px", "height": "100%", "cursor": "pointer" if clickable_id else "default"}
    }
    if clickable_id:
        wrapper_props["id"] = clickable_id
    return html.Div([
        html.Div([
            html.Div(title, className="cr-kpi-label"),
            html.Span("→", className="cr-kpi-arrow") if clickable_id else None,
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "gap": "8px"}),
        html.Div(str(value), className="cr-kpi-value"),
        html.Div([
            html.Div(note, className="cr-kpi-note"),
            chip,
        ], className="cr-kpi-meta"),
    ], **wrapper_props)

def quick_range_button(key, label, id_type="cr-date-preset"):
    return html.Button(label, id={"type": id_type, "index": key}, className="cr-btn-ghost")

def badge(text, fg=TEXT, bg="#f3f4f6", border="#e5e7eb"):
    return html.Span(text, className="cr-badge", style={"color": fg, "background": bg, "borderColor": border})

def simple_error(message):
    return html.Div(str(message), className="cr-note-box", style={"color": DANGER, "background": "#fef2f2", "border": "1px solid #fecaca"})

def render_ai_markdown(text):
    return html.Div(
        dcc.Markdown(text, link_target="_blank"),
        className="cr-note-box",
        style={"whiteSpace": "pre-wrap"},
    )

def oldest_cards(df, empty_message, id_col="Service Request ID", desc_col="Subject", status_col="Status"):
    if df.empty:
        return html.Div(empty_message, className="cr-note-box")

    cards = []
    for _, row in df.iterrows():
        raw_age = row.get("age_days", 0)
        age_days = int(raw_age) if pd.notna(raw_age) else 0
        age_badge = badge(
            f"{age_days} days",
            fg="#92400e" if age_days >= 30 else ("#1d4ed8" if age_days >= 14 else "#166534"),
            bg="#fff7ed" if age_days >= 30 else ("#eff6ff" if age_days >= 14 else "#f0fdf4"),
            border="#fed7aa" if age_days >= 30 else ("#bfdbfe" if age_days >= 14 else "#bbf7d0"),
        )
        cards.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(f"#{row.get(id_col)}", style={"fontWeight": "800", "fontSize": "14px", "color": TEXT}),
                            age_badge,
                        ],
                        style={"display": "flex", "justifyContent": "space-between", "gap": "12px", "marginBottom": "8px"},
                    ),
                    html.Div(row.get(status_col, "N/A"), className="cr-muted", style={"fontSize": "12px", "marginBottom": "8px"}),
                    html.Div(str(row.get(desc_col, ""))[:180], style={"fontSize": "13px", "lineHeight": "1.6", "color": TEXT_MID}),
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
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False, linecolor=BORDER, tickfont=dict(color=TEXT_SOFT), title_font=dict(color=TEXT_SOFT))
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False, linecolor=BORDER, tickfont=dict(color=TEXT_SOFT), title_font=dict(color=TEXT_SOFT))
    return fig

def empty_figure(title="No data available"):
    fig = px.bar(title=title)
    fig.update_layout(
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, height=330, margin=dict(l=12, r=12, t=60, b=12),
        font=dict(family="Inter, ui-sans-serif, system-ui, sans-serif", color=TEXT)
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig
