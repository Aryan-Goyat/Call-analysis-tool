import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from components import page_header
import pandas as pd
from db import get_engine
from sqlalchemy import text
from datetime import datetime

CR_PENDING = [
    "Requested", "Approved", "Pre-Migration Approved",
    "Pre-Migration Approved 1", "Migration date finalized",
    "Pending Further Review", "UAT Approved", "Draft", "Approved by Owner"
]
SR_PENDING = ["In-Progress", "Pending", "Pending for Approval"]
INC_PENDING = ["New", "In Progress", "Pending"]

dash.register_page(__name__, path="/profile", name="Profile")

LABEL_STYLE = {
    "fontSize": "11px",
    "fontWeight": "600",
    "letterSpacing": "0.06em",
    "textTransform": "uppercase",
    "color": "var(--text-s)",
    "marginBottom": "6px",
    "display": "block",
}

INPUT_STYLE = {
    "width": "100%",
    "padding": "10px 12px",
    "fontSize": "13px",
    "color": "var(--text-p)",
    "background": "var(--bg-card)",
    "border": "1px solid var(--border-color)",
    "borderRadius": "8px",
    "boxSizing": "border-box",
    "outline": "none",
}

CARD_STYLE = {
    "background": "var(--bg-card)",
    "border": "1px solid var(--border-color)",
    "borderRadius": "12px",
    "padding": "20px",
    "boxShadow": "0 1px 2px rgba(15, 23, 42, 0.04)",
}

BUTTON_PRIMARY = {
    "padding": "10px 16px",
    "border": "none",
    "borderRadius": "8px",
    "background": "var(--text-p)",
    "color": "var(--bg-card)",
    "fontSize": "13px",
    "fontWeight": "600",
    "cursor": "pointer",
}

BUTTON_DANGER = {
    "padding": "10px 16px",
    "border": "1px solid #dc2626",
    "borderRadius": "8px",
    "background": "transparent",
    "color": "#dc2626",
    "fontSize": "13px",
    "fontWeight": "600",
    "cursor": "pointer",
}


def field(label, input_id, value="", placeholder="", input_type="text"):
    return html.Div([
        html.Label(label, style=LABEL_STYLE),
        dcc.Input(
            id=input_id,
            value=value,
            placeholder=placeholder,
            type=input_type,
            style=INPUT_STYLE,
            className="profile-input",
        ),
    ], style={"marginBottom": "16px"})



def section_title(text, description=None):
    children = [
        html.Div(text, style={
            "fontSize": "16px",
            "fontWeight": "700",
            "color": "var(--text-p)",
            "marginBottom": "4px",
        })
    ]
    if description:
        children.append(html.Div(description, style={
            "fontSize": "13px",
            "color": "var(--text-s)",
            "marginBottom": "18px",
            "lineHeight": "1.5",
        }))
    else:
        children.append(html.Div(style={"marginBottom": "18px"}))
    return html.Div(children)



def toggle(label, toggle_id, checked=True, sublabel=""):
    return html.Div([
        html.Div([
            html.Div([
                html.Div(label, style={
                    "fontSize": "14px",
                    "fontWeight": "500",
                    "color": "var(--text-p)",
                }),
                html.Div(sublabel, style={
                    "fontSize": "12px",
                    "color": "var(--text-s)",
                    "marginTop": "2px",
                }) if sublabel else None,
            ], style={"flex": "1"}),
            dbc.Switch(id=toggle_id, value=checked),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "gap": "12px",
        }),
    ], style={"padding": "12px 0", "borderBottom": "1px solid var(--border-color)"})



def stat_card(label, value):
    return html.Div([
        html.Div(label, style={
            "fontSize": "11px",
            "fontWeight": "600",
            "letterSpacing": "0.06em",
            "textTransform": "uppercase",
            "color": "var(--text-s)",
            "marginBottom": "8px",
        }),
        html.Div(str(value), style={
            "fontSize": "26px",
            "fontWeight": "700",
            "color": "var(--text-p)",
            "lineHeight": "1.1",
        }),
    ], style={
        "background": "var(--bg-card)",
        "border": "1px solid var(--border-color)",
        "borderRadius": "10px",
        "padding": "16px",
        "minWidth": "160px",
        "flex": "1",
    })



def activity_item(title, time_text):
    return html.Div([
        html.Div(title, style={
            "fontSize": "13px",
            "fontWeight": "500",
            "color": "var(--text-p)",
        }),
        html.Div(time_text, style={
            "fontSize": "12px",
            "color": "var(--text-s)",
            "marginTop": "2px",
        }),
    ], style={
        "padding": "12px 0",
        "borderBottom": "1px solid var(--border-color)",
    })



def layout():
    assigned_cr = "--"
    assigned_sr = "--"
    open_inc = "--"
    active_alerts = "--"

    try:
        engine = get_engine()
    except Exception:
        engine = None

    if engine:
        try:
            cr_query = "SELECT COUNT(*) as c FROM cr_report WHERE `Owner Work Group Name` IN ('IT Support (ALC)', 'IT Support (EVSM)') AND `Status` IN :statuses"
            assigned_cr = pd.read_sql(text(cr_query), engine, params={"statuses": CR_PENDING}).iloc[0]["c"]
        except Exception as e:
            print(f"Error fetching CR stats: {e}")

        try:
            sr_query = "SELECT COUNT(*) as c FROM sr_report WHERE `Workgroup` IN ('IT Support (ALC)', 'IT Support (EVSM)') AND `Status` IN :statuses"
            assigned_sr = pd.read_sql(text(sr_query), engine, params={"statuses": SR_PENDING}).iloc[0]["c"]
        except Exception as e:
            print(f"Error fetching SR stats: {e}")

        try:
            inc_query = "SELECT COUNT(*) as c FROM incident_report WHERE `Workgroup` IN ('IT Support (ALC)', 'IT Support (EVSM)') AND `Status` IN :statuses"
            open_inc = pd.read_sql(text(inc_query), engine, params={"statuses": INC_PENDING}).iloc[0]["c"]
        except Exception as e:
            print(f"Error fetching Incident stats: {e}")

        try:
            alerts = 0
            now = datetime.now()

            df_cr = pd.read_sql(
                text("SELECT `Request Registration Time` as dt FROM cr_report WHERE `Owner Work Group Name` IN ('IT Support (ALC)', 'IT Support (EVSM)') AND `Status` IN :statuses"),
                engine,
                params={"statuses": CR_PENDING},
            )
            if not df_cr.empty:
                alerts += ((now - pd.to_datetime(df_cr["dt"], errors="coerce")).dt.days >= 14).sum()

            df_sr = pd.read_sql(
                text("SELECT `LogTime` as dt FROM sr_report WHERE `Workgroup` IN ('IT Support (ALC)', 'IT Support (EVSM)') AND `Status` IN :statuses"),
                engine,
                params={"statuses": SR_PENDING},
            )
            if not df_sr.empty:
                alerts += ((now - pd.to_datetime(df_sr["dt"], format="%m/%d/%Y %H:%M", errors="coerce")).dt.days >= 5).sum()

            df_inc = pd.read_sql(
                text("SELECT `Log Time` as dt FROM incident_report WHERE `Workgroup` IN ('IT Support (ALC)', 'IT Support (EVSM)') AND `Status` IN :statuses"),
                engine,
                params={"statuses": INC_PENDING},
            )
            if not df_inc.empty:
                alerts += ((now - pd.to_datetime(df_inc["dt"], format="%d/%m/%Y %H:%M", errors="coerce")).dt.days >= 1).sum()

            active_alerts = alerts
        except Exception as e:
            print(f"Error fetching Alert stats: {e}")

    return html.Div([
        html.Div([
            page_header("Profile"),
            html.Div(
                "Simple account settings, preferences, and notifications.",
                style={
                    "fontSize": "14px",
                    "color": "var(--text-s)",
                    "marginTop": "8px",
                    "marginBottom": "24px",
                    "paddingLeft": "24px",
                },
            ),
        ], style={"paddingTop": "24px", "maxWidth": "1040px", "margin": "0 auto"}),
        html.Div([
            html.Div([
                html.Div([
                    html.Div("AU", style={
                        "width": "56px",
                        "height": "56px",
                        "borderRadius": "50%",
                        "background": "var(--text-p)",
                        "color": "var(--bg-card)",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontSize": "18px",
                        "fontWeight": "700",
                        "flexShrink": "0",
                    }),
                    html.Div([
                        html.Div("Admin User", style={
                            "fontSize": "20px",
                            "fontWeight": "700",
                            "color": "var(--text-p)",
                        }),
                        html.Div("Lead Critical Analyst", style={
                            "fontSize": "13px",
                            "color": "var(--text-s)",
                            "marginTop": "4px",
                        }),
                        html.Div("IT Operations · IT Support (ALC), IT Support (EVSM)", style={
                            "fontSize": "12px",
                            "color": "var(--text-s)",
                            "marginTop": "8px",
                        }),
                    ], style={"flex": "1"}),
                    html.Div("Active", style={
                        "fontSize": "12px",
                        "fontWeight": "600",
                        "color": "#15803d",
                        "background": "#f0fdf4",
                        "border": "1px solid #bbf7d0",
                        "padding": "6px 10px",
                        "borderRadius": "999px",
                        "alignSelf": "flex-start",
                    }),
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "16px",
                    "flexWrap": "wrap",
                    "marginBottom": "20px",
                }),
                html.Div([
                    stat_card("Assigned CR", assigned_cr),
                    stat_card("Assigned SR", assigned_sr),
                    stat_card("Open Incidents", open_inc),
                    stat_card("Active Alerts", active_alerts),
                ], style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(160px, 1fr))",
                    "gap": "12px",
                }),
            ], style={**CARD_STYLE, "marginBottom": "20px"}),

            html.Div([
                html.Div([
                    html.Div([
                        section_title("User identity", "Basic account details."),
                        html.Div([
                            html.Div(field("First name", "inp-first", "Admin"), style={"flex": "1"}),
                            html.Div(field("Last name", "inp-last", "User"), style={"flex": "1"}),
                        ], style={
                            "display": "grid",
                            "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
                            "gap": "12px",
                        }),
                        field("Primary email", "inp-email", "admin@datadash.sys", input_type="email"),
                        field("Phone number", "inp-phone", "+91 9971891195"),
                        html.Button("Save changes", id="save-identity-btn", n_clicks=0, style=BUTTON_PRIMARY),
                        html.Div(id="save-identity-msg", style={"marginTop": "12px", "fontSize": "13px"}),
                    ], style=CARD_STYLE),

                    html.Div([
                        section_title("Security", "Update your password."),
                        field("Current password", "inp-curr-pass", input_type="password"),
                        field("New password", "inp-new-pass", input_type="password"),
                        field("Confirm password", "inp-conf-pass", input_type="password"),
                        html.Button("Update password", id="save-pass-btn", n_clicks=0, style=BUTTON_PRIMARY),
                        html.Div(id="save-pass-msg", style={"marginTop": "12px", "fontSize": "13px"}),
                    ], style={**CARD_STYLE, "marginTop": "20px"}),
                ], style={"flex": "1.4", "minWidth": "320px"}),

                html.Div([
                    html.Div([
                        section_title("Preferences", "Regional settings."),
                        html.Div([
                            html.Label("Timezone", style=LABEL_STYLE),
                            dcc.Dropdown(
                                id="inp-timezone",
                                options=[
                                    {"label": "UTC — Coordinated Universal Time", "value": "UTC"},
                                    {"label": "IST — India Standard Time (UTC+5:30)", "value": "IST"},
                                    {"label": "EST — Eastern Standard Time (UTC-5)", "value": "EST"},
                                    {"label": "PST — Pacific Standard Time (UTC-8)", "value": "PST"},
                                    {"label": "CET — Central European Time (UTC+1)", "value": "CET"},
                                ],
                                value="IST",
                                clearable=False,
                                className="profile-dropdown",
                                style={"fontSize": "13px", "marginBottom": "16px"},
                            ),
                            html.Label("Date format", style=LABEL_STYLE),
                            dcc.Dropdown(
                                id="inp-dateformat",
                                options=[
                                    {"label": "DD/MM/YYYY", "value": "dmy"},
                                    {"label": "MM/DD/YYYY", "value": "mdy"},
                                    {"label": "YYYY-MM-DD", "value": "ymd"},
                                ],
                                value="dmy",
                                clearable=False,
                                className="profile-dropdown",
                                style={"fontSize": "13px"},
                            ),
                        ]),
                    ], style=CARD_STYLE),

                    html.Div([
                        section_title("Notifications", "Choose the alerts you want to receive."),
                        toggle("CR alerts", "tog-cr", True, "Aged more than 14 days"),
                        toggle("SR alerts", "tog-sr", True, "Aged more than 5 days"),
                        toggle("Incident alerts", "tog-incident", True, "Aged more than 1 day"),
                        toggle("Browser notifications", "tog-browser", True, "Push updates every 10 minutes"),
                        html.Div(toggle("Weekly summary email", "tog-email", False, "Aggregated weekly report"), style={"borderBottom": "none"}),
                    ], style={**CARD_STYLE, "marginTop": "20px"}),

                    html.Div([
                        section_title("Recent activity"),
                        activity_item("Last login", "2 hours ago"),
                        activity_item("Profile updated", "Yesterday"),
                        activity_item("Password changed", "Last month"),
                        html.Div(activity_item("Notification preferences updated", "Last week"), style={"borderBottom": "none"}),
                    ], style={**CARD_STYLE, "marginTop": "20px"}),

                    html.Div([
                        section_title("Danger zone", "Permanent actions for this account."),
                        html.Button("Initiate account deletion", style=BUTTON_DANGER),
                    ], style={
                        **CARD_STYLE,
                        "marginTop": "20px",
                        "border": "1px solid rgba(220, 38, 38, 0.25)",
                        "background": "rgba(220, 38, 38, 0.02)",
                    }),
                ], style={"flex": "1", "minWidth": "300px"}),
            ], style={
                "display": "flex",
                "gap": "20px",
                "alignItems": "flex-start",
                "flexWrap": "wrap",
            }),
        ], style={
            "maxWidth": "1040px",
            "margin": "0 auto",
            "padding": "24px 32px 40px",
        }),

        html.Div(style={"display": "none"}, children=[
            dcc.Markdown(
                '''
                <style>
                .profile-input:focus {
                    border-color: var(--text-p) !important;
                    box-shadow: 0 0 0 2px rgba(15, 23, 42, 0.08) !important;
                }
                .profile-dropdown .Select-control,
                .profile-dropdown .select__control,
                .profile-dropdown .Select__control {
                    border-radius: 8px !important;
                    border: 1px solid var(--border-color) !important;
                    box-shadow: none !important;
                    min-height: 40px !important;
                    background: var(--bg-card) !important;
                }
                .profile-dropdown .Select-placeholder,
                .profile-dropdown .Select-value-label,
                .profile-dropdown .select__single-value,
                .profile-dropdown .Select__single-value {
                    color: var(--text-p) !important;
                }
                .profile-dropdown .is-focused:not(.is-open) > .Select-control,
                .profile-dropdown .select__control--is-focused,
                .profile-dropdown .Select__control--is-focused {
                    border-color: var(--text-p) !important;
                    box-shadow: 0 0 0 2px rgba(15, 23, 42, 0.08) !important;
                }
                </style>
                ''',
                dangerously_allow_html=True,
            )
        ]),
    ])


@callback(
    Output("save-identity-msg", "children"),
    Output("save-identity-msg", "style"),
    Input("save-identity-btn", "n_clicks"),
    prevent_initial_call=True,
)
def save_identity(n):
    return "✓ Changes saved successfully", {
        "marginTop": "12px",
        "fontSize": "13px",
        "color": "#15803d",
        "fontWeight": "500",
    }


@callback(
    Output("save-pass-msg", "children"),
    Output("save-pass-msg", "style"),
    Input("save-pass-btn", "n_clicks"),
    prevent_initial_call=True,
)
def save_password(n):
    return "✓ Password updated", {
        "marginTop": "12px",
        "fontSize": "13px",
        "color": "#15803d",
        "fontWeight": "500",
    }
