"""
Shared UI components for the IT Analytics Dashboard.
Extracts common patterns used across CR, SR, and Incident report pages.
"""

import json
from datetime import datetime, timedelta

from dash import html, dcc
import dash
import pandas as pd


# ── Color Constants ───────────────────────────────────────────────────────────
C_RED      = "#FF3B30"
C_ORANGE   = "#FF9500"
C_BLUE     = "var(--accent)"
C_GREEN    = "#34C759"
C_TEXT_P   = "var(--text-p)"
C_TEXT_MID = "var(--text-mid)"
C_TEXT_S   = "var(--text-s)"

# Max ticket cards rendered in a chart drill-down panel
MAX_DRILLDOWN_CARDS = 50


# ── Shared Date-Preset Resolver ───────────────────────────────────────────────
def resolve_date_preset(n_clicks_list, min_date, max_date):
    """Shared logic for the 7D/30D/90D/... preset buttons on report pages.
    Returns (start_iso, end_iso) or (no_update, no_update)."""
    ctx = dash.callback_context
    if not ctx.triggered or all(not n for n in n_clicks_list):
        return dash.no_update, dash.no_update

    trigger_id = json.loads(ctx.triggered[0]["prop_id"].rsplit(".", 1)[0])
    preset = trigger_id["index"]
    today = datetime.now().date()

    if preset == "7d":
        return (today - timedelta(days=7)).isoformat(), today.isoformat()
    elif preset == "30d":
        return (today - timedelta(days=30)).isoformat(), today.isoformat()
    elif preset == "90d":
        return (today - timedelta(days=90)).isoformat(), today.isoformat()
    elif preset == "this_month":
        return today.replace(day=1).isoformat(), today.isoformat()
    elif preset == "this_quarter":
        q_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=q_month, day=1).isoformat(), today.isoformat()
    elif preset == "all":
        return (min_date.isoformat() if hasattr(min_date, "isoformat") else str(min_date),
                max_date.isoformat() if hasattr(max_date, "isoformat") else str(max_date))
    return dash.no_update, dash.no_update


# ── Empty State ───────────────────────────────────────────────────────────────
import base64

def empty_state_illustration(message="No data available for this range"):
    return html.Div([
        html.Div("—", style={"fontSize": "24px", "color": "var(--text-s)", "fontWeight": "300", "marginBottom": "8px"}),
        html.Div(message, style={"fontSize": "13px", "color": "var(--text-s)", "fontWeight": "400"}),
    ], style={
        "display": "flex", "flexDirection": "column", "alignItems": "center",
        "justifyContent": "center", "padding": "40px 20px", "textAlign": "center",
    })

# ── KPI Card ──────────────────────────────────────────────────────────────────

def kpi_card(label, value, delta, sparkline_data=None, show_ring=False, ring_pct=0):
    progress_bar = None
    if show_ring:
        pct = max(0, min(100, ring_pct))
        progress_bar = html.Div(
            html.Div(style={"height": "100%", "width": f"{pct}%", "backgroundColor": "var(--text-p)"}),
            style={"height": "2px", "width": "100%", "backgroundColor": "var(--border-color)", "marginTop": "12px", "borderRadius": "1px"}
        )

    display_value = "—" if value is None or str(value).strip() == "" else value

    return html.Div([
        html.Div(label, style={
            "fontSize": "11px", "color": "var(--text-s)", "marginBottom": "6px",
            "fontWeight": "600", "letterSpacing": "0.05em", "textTransform": "uppercase",
        }),
        html.Div(display_value, style={
            "fontSize": "clamp(28px, 2.6vw, 42px)", "fontWeight": "700", "color": "var(--text-p)",
            "letterSpacing": "-1px", "lineHeight": "1.1", "marginBottom": "4px",
            "overflowWrap": "break-word",
        }),
        html.Div(delta, style={"fontSize": "12px", "color": "var(--text-s)"}),
        progress_bar,
    ], className="apple-card", style={"flex": "1", "display": "flex", "flexDirection": "column", "justifyContent": "center"})


# ── Oldest Pending List ───────────────────────────────────────────────────────
def build_oldest_ui(oldest_df, empty_message, id_col="Change Request Id",
                    desc_col="Description", age_high=30, age_mid=14,
                    show_workgroup=True):
    """
    Renders a list of the oldest pending items.
    Configurable per report type (CR/SR/Incident).
    """
    items = []
    if oldest_df is not None and not oldest_df.empty:
        for _, row in oldest_df.iterrows():
            age   = int(row["age_days"]) if pd.notna(row["age_days"]) else 0
            color = C_RED if age > age_high else C_ORANGE if age > age_mid else "#86868B"
            desc  = str(row.get(desc_col, ""))
            short = desc[:45] + "..." if len(desc) > 45 else desc

            title_parts = [str(row.get(id_col, ""))]
            if show_workgroup and "Owner Work Group Name" in row.index:
                title_parts.append(str(row["Owner Work Group Name"]).split(" ")[-1])
            title_text = " - ".join(title_parts)

            item_children = [
                html.Div(title_text, style={
                    "fontWeight": "600", "fontSize": "14px", "color": "var(--text-p)",
                }),
                html.Div(short, style={
                    "fontSize": "12px", "color": "var(--text-s)", "marginTop": "2px",
                }),
            ]
            # Show status if present
            if "Status" in row.index:
                item_children.append(html.Div(str(row["Status"]), style={
                    "fontSize": "11px", "color": "var(--accent)", "marginTop": "2px",
                }))

            items.append(html.Div([
                html.Div(item_children),
                html.Div(f"{age}d", style={
                    "fontWeight": "500", "color": color, "fontSize": "13px",
                    "padding": "2px 8px", "borderRadius": "4px",
                    "border": f"1px solid {color}",
                }),
            ], style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "padding": "12px 0",
                "borderBottom": "1px solid var(--border-color)",
            }))

    if not items:
        items = [empty_state_illustration(empty_message)]
    return items


# ── Date Picker Bar ───────────────────────────────────────────────────────────
def date_picker_bar(start_id, end_id, min_date, max_date, export_button=None, preset_id=None):
    """Renders the FROM/TO date picker section with optional date range presets."""
    
    preset_row = None
    if preset_id:
        presets = [
            {"label": "7D", "value": "7d"},
            {"label": "30D", "value": "30d"},
            {"label": "90D", "value": "90d"},
            {"label": "This Month", "value": "this_month"},
            {"label": "This Quarter", "value": "this_quarter"},
            {"label": "All", "value": "all"},
        ]
        preset_row = html.Div([
            html.Button(p["label"], id={"type": preset_id, "index": p["value"]}, n_clicks=0,
                className="date-preset-pill",
                style={
                    "border": "1px solid var(--border-color)", "borderRadius": "980px",
                    "padding": "5px 14px", "fontSize": "12px", "fontWeight": "500",
                    "cursor": "pointer", "background": "var(--bg-card)",
                    "color": "var(--text-s)", "transition": "all 0.15s ease",
                },
            ) for p in presets
        ], style={"display": "flex", "gap": "6px", "flexWrap": "wrap", "marginBottom": "12px"})
    
    content = [
        html.Div([
            html.Div([
                html.Div("FROM", style={
                    "fontSize": "11px", "color": "var(--text-s)", "fontWeight": "600",
                    "marginBottom": "4px", "letterSpacing": "0.5px",
                }),
                dcc.DatePickerSingle(
                    id=start_id, date=min_date, display_format="MMM D, YYYY",
                ),
            ]),
            html.Div([
                html.Div("TO", style={
                    "fontSize": "11px", "color": "var(--text-s)", "fontWeight": "600",
                    "marginBottom": "4px", "letterSpacing": "0.5px",
                }),
                dcc.DatePickerSingle(
                    id=end_id, date=max_date, display_format="MMM D, YYYY",
                ),
            ]),
        ], className="responsive-flex-row", style={"display": "flex", "gap": "24px", "alignItems": "flex-end"}),
    ]
    
    if export_button:
        content.append(export_button)

    inner = []
    if preset_row:
        inner.append(preset_row)
    inner.append(html.Div(content, style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "flex-end",
        "width": "100%", "flexWrap": "wrap", "gap": "24px"
    }))

    return html.Div(inner, className="responsive-padding", style={
        "width": "100%",
        "padding": "20px 24px",
        "borderBottom": "none",
        "marginBottom": "20px",
    })


# ── Skeleton Loading Helpers ──────────────────────────────────────────────────
def skeleton_kpi_row(count=4):
    """Returns a row of skeleton KPI card placeholders."""
    return html.Div([
        html.Div([
            html.Div(className="skeleton-shimmer", style={"width": "60%", "height": "12px", "borderRadius": "6px", "marginBottom": "12px"}),
            html.Div(className="skeleton-shimmer", style={"width": "40%", "height": "32px", "borderRadius": "8px", "marginBottom": "8px"}),
            html.Div(className="skeleton-shimmer", style={"width": "50%", "height": "10px", "borderRadius": "6px"}),
        ], className="apple-card", style={
            "flex": "1", "minWidth": "180px", "padding": "16px", "borderRadius": "8px",
            "background": "var(--bg-card)", "border": "none",
        }) for _ in range(count)
    ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"})


def skeleton_chart():
    """Returns a skeleton chart placeholder."""
    return html.Div([
        html.Div(className="skeleton-shimmer", style={"width": "30%", "height": "14px", "borderRadius": "6px", "marginBottom": "20px"}),
        html.Div(className="skeleton-shimmer", style={"width": "100%", "height": "200px", "borderRadius": "12px"}),
    ], className="apple-card", style={
        "padding": "20px", "borderRadius": "8px",
        "background": "var(--bg-card)", "border": "none",
    })


# ── AI Insights Section ──────────────────────────────────────────────────────
def ai_insights_section(dropdown_id, button_id, output_id, dropdown_options=None):
    if dropdown_options is None:
        dropdown_options = [
            {"label": "Last 1 Month", "value": 1},
            {"label": "Last 2 Months", "value": 2},
            {"label": "Last 3 Months", "value": 3},
            {"label": "Last 6 Months", "value": 6},
            {"label": "Entire Selection", "value": 100},
        ]
    return html.Div([
        html.Div([
            html.Div([
                html.Span(html.I(className="bi bi-lightning-charge"), style={"fontSize": "16px", "color": "var(--text-p)", "marginRight": "8px"}),
                html.Span("AI Insights", style={"fontWeight": "600", "fontSize": "18px", "color": "var(--text-p)", "letterSpacing": "-0.3px"}),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Div([
                dcc.Dropdown(id=dropdown_id, options=dropdown_options, value=dropdown_options[0]["value"], clearable=False,
                    className="minimal-dropdown", style={"width": "160px", "fontSize": "13px"}),
                html.Button("Generate Insights", id=button_id, style={
                    "background": "var(--text-p)",
                    "color": "var(--bg-body)", "border": "none", "padding": "8px 18px",
                    "borderRadius": "980px", "cursor": "pointer", "fontWeight": "500",
                    "fontSize": "13px",
                }),
            ], style={"display": "flex", "gap": "16px", "alignItems": "center", "flexWrap": "wrap"}),
        ], className="responsive-flex-row", style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
        dcc.Loading(
            html.Div(id=output_id, children=[
                html.Div([
                    html.Div("—", style={"fontSize": "24px", "color": "var(--text-s)", "fontWeight": "300", "marginBottom": "8px"}),
                    html.Div("No insights yet", style={"fontWeight": "500", "fontSize": "14px", "color": "var(--text-p)", "marginBottom": "4px"}),
                    html.Div("Select a date range, choose a period, and click generate to reveal insights.", 
                             style={"color": "var(--text-s)", "fontSize": "13px", "fontWeight": "400"})
                ], style={
                    "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center",
                    "padding": "40px 20px", "borderTop": "1px solid var(--border-color)", "marginTop": "20px",
                    "textAlign": "center"
                })
            ]),
            type="circle", color="#007AFF", style={"marginTop": "16px"}
        ),
    ])


# ── Render AI Output ──────────────────────────────────────────────────────────
def render_ai_output(text):
    blocks = []
    current_card_children = []
    current_sev_color = C_TEXT_S
    tips = []
    in_tips = False

    def flush_card():
        if current_card_children:
            blocks.append(html.Div(current_card_children[:], className="ai-pattern-card", style={
                "background": "var(--bg-hover)", "borderRadius": "6px",
                "padding": "14px 16px", "marginTop": "10px",
                "borderLeft": f"2px solid {current_sev_color}",
            }))
            current_card_children.clear()

    in_pattern = False
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("PATTERN:"):
            flush_card()
            in_pattern = True
            in_tips = False
            parts = line.replace("PATTERN:", "").split("|")
            title = parts[0].strip()
            sev = parts[1].strip() if len(parts) > 1 else ""
            current_sev_color = C_RED if "High" in sev else C_ORANGE if "Medium" in sev else C_TEXT_S
            current_card_children.append(html.Div([
                html.Span(title, style={"fontWeight": "600", "fontSize": "14px", "color": "var(--text-p)"}),
                html.Span(sev, style={"fontSize": "11px", "color": current_sev_color, "fontWeight": "600",
                    "marginLeft": "12px", "padding": "3px 10px", "borderRadius": "4px",
                    "background": "transparent", "border": f"1px solid {current_sev_color}"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}))
        elif line.startswith("Suggested action:") or line.startswith("Suggested fix:"):
            current_card_children.append(html.Div(line, style={
                "fontSize": "12px", "color": "#007AFF", "marginTop": "6px", "fontStyle": "italic",
            }))
        elif line.startswith("REDUCTION TIPS"):
            flush_card()
            in_pattern = False
            in_tips = True
        elif line.startswith(("-", "•")):
            if in_tips:
                tips.append(line)
            else:
                blocks.append(html.Div(line, style={
                    "fontSize": "13px", "color": C_TEXT_P, "marginBottom": "6px",
                    "paddingLeft": "8px", "borderLeft": "2px solid #e2e8f0",
                }))
        elif in_pattern:
            current_card_children.append(html.Div(line, style={
                "fontSize": "13px", "color": C_TEXT_MID, "marginTop": "4px", "lineHeight": "1.4",
            }))
        else:
            if in_tips:
                tips.append(line)
            else:
                blocks.append(html.Div(line, style={"fontSize": "13px", "color": C_TEXT_MID, "marginBottom": "4px"}))

    flush_card()
    
    if tips:
        blocks.append(html.Div("REDUCTION TIPS", style={
            "fontSize": "11px", "fontWeight": "600", "color": C_TEXT_S,
            "letterSpacing": "0.5px", "marginTop": "24px", "marginBottom": "10px",
        }))
        for tip in tips[:3]:
            blocks.append(html.Div(tip, style={
                "fontSize": "13px", "color": C_TEXT_P, "marginBottom": "6px",
                "paddingLeft": "8px", "borderLeft": "2px solid #e2e8f0",
            }))

    return html.Div(blocks, style={
        "background": "var(--bg-card)", "borderRadius": "8px",
        "padding": "16px", "border": "none",
    })


# ── AI Error UI ───────────────────────────────────────────────────────────────
def ai_error_ui(error):
    """Renders a user-friendly error state when AI insights fail."""
    return html.Div([
        html.Div([
            html.I(className="bi bi-exclamation-circle", style={
                "fontSize": "18px", "color": C_RED, "marginRight": "8px",
            }),
            html.Span("Insights Unavailable", style={
                "fontWeight": "600", "fontSize": "14px", "color": C_RED,
            }),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px"}),
        html.Div(f"{type(error).__name__}: {str(error)[:120]}", style={
            "fontSize": "12px", "color": C_TEXT_S, "lineHeight": "1.4",
        }),
    ], style={
        "padding": "14px", "background": "var(--bg-card)",
        "borderRadius": "6px", "border": "none",
    })


# ── Page Header ───────────────────────────────────────────────────────────────
def page_header(title):
    """Renders the sticky glass header bar for a page."""

    return html.Div([
        # Top Row: Title + Theme Button
        html.Div([
            html.Span(title, style={
                "fontWeight": "700", "fontSize": "26px",
                "color": "var(--text-p)", "letterSpacing": "-0.5px",
            })
        ], className="header-top-row", style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "width": "100%"}),
        
        # Bottom Row: Today Badges Placeholder
        html.Div(id="today-summary-badges", style={
            "display": "flex", "gap": "10px", "flexWrap": "wrap"
        })
    ], className="apple-header page-header-wrapper", style={
        "display": "flex", "flexDirection": "column", "padding": "20px 24px 0 24px", "background": "transparent"
    })

