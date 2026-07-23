import dash
import os
import pandas as pd
from groq import Groq
from db import get_engine
from dotenv import load_dotenv
from auth_db import check_credentials, user_exists, create_reset_token, validate_reset_token, update_password
from email_service import send_reset_email
from dash import html, dcc, Input, Output, State, callback
from flask import request, session, redirect, render_template_string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import dash_bootstrap_components as dbc

load_dotenv()
client = Groq(api_key=os.getenv("API_KEY"))

app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder=os.path.dirname(os.path.abspath(__file__)),
    suppress_callback_exceptions=True,
    title="IT Analytics Dashboard",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
)


# ── Authentication & Flask Routes ─────────────────────────────────────────────
server = app.server
server.secret_key = os.getenv("SECRET_KEY", "fallback-secret-for-dev")

limiter = Limiter(
    get_remote_address,
    app=server,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

@server.before_request
def check_login():
    if request.path in ['/login', '/logout', '/forgot-password', '/reset-password', '/_favicon.ico']:
        return
    if request.path.startswith('/assets/') or request.path.startswith('/_dash'):
        return
    if not session.get("logged_in"):
        return redirect('/login')

@server.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if check_credentials(username, password):
            session['logged_in'] = True
            return redirect('/')
        else:
            error = "Invalid credentials. Please try again."
            
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Sign In | Honda IT Analytics</title>
        <style>
            :root {
                --honda-red: #E60012;
                --honda-red-dark: #A50000;
                --ink: #1A1A1A;
                --grey: #595959;             /* AA on white for 12px+ labels */
                --line: #D9D9D9;
                --error-red: #B42318;        /* AA on white & on #FDECEC */
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                background: #FFFFFF;
                color: var(--ink);
            }
            /* ── Left brand panel ──
               Intentional diagonal sweep: pure black anchors the top-left,
               Honda red owns the bottom-right corner. Hard-ish stops keep it
               reading as a designed diagonal, not a blur. A red keyline seals
               the panel edge against the form side. */
            .brand-panel {
                flex: 1.1;
                background: linear-gradient(135deg,
                    #000000 0%,
                    #141414 42%,
                    #4A0000 74%,
                    var(--honda-red) 118%);
                border-right: 4px solid var(--honda-red);
                color: #FFFFFF;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 48px 56px;
                position: relative;
                overflow: hidden;
            }
            /* Speed-line motif: three thin parallel diagonals echoing the
               gradient angle — automotive motion cue, deliberately grouped
               on the right third of the panel */
            .brand-panel::after {
                content: "";
                position: absolute;
                top: -12%;
                right: 10%;
                width: 130px;
                height: 124%;
                background: repeating-linear-gradient(
                    90deg,
                    rgba(255, 255, 255, 0.09) 0px,
                    rgba(255, 255, 255, 0.09) 1px,
                    transparent 1px,
                    transparent 44px
                );
                transform: rotate(24deg);
                pointer-events: none;
            }
            .brand-mark {
                display: flex;
                align-items: center;
                gap: 14px;
                position: relative;
                z-index: 1;
            }
            /* Honda wing mark — height keyed to the wordmark's cap height,
               vertically centered by the flex row */
            .brand-wing {
                height: 32px;
                width: auto;
                display: block;
            }
            .brand-word {
                font-size: 26px;
                font-weight: 800;
                letter-spacing: 0.35em;
                color: var(--honda-red);
            }
            .brand-tagline {
                position: relative;
                z-index: 1;
            }
            .brand-tagline h2 {
                font-size: 34px;
                font-weight: 700;
                line-height: 1.25;
                margin: 0 0 14px;
                letter-spacing: -0.01em;
            }
            /* #FFB3B3 holds ≥3:1 (AA large-text) against every gradient stop,
               including the saturated #E60012 corner */
            .brand-tagline h2 span { color: #FFB3B3; }
            .brand-tagline p {
                font-size: 15px;
                color: rgba(255,255,255,0.78);
                margin: 0;
                max-width: 400px;
                line-height: 1.6;
            }
            .brand-foot {
                font-size: 12px;
                color: rgba(255,255,255,0.66);
                letter-spacing: 0.08em;
                position: relative;
                z-index: 1;
            }
            /* ── Right form panel ── */
            .form-panel {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px;
            }
            .login-card {
                width: 100%;
                max-width: 380px;
            }
            .red-rule {
                width: 44px;
                height: 4px;
                background: var(--honda-red);
                border-radius: 2px;
                margin-bottom: 24px;
            }
            .title {
                font-size: 26px;
                font-weight: 700;
                margin-bottom: 6px;
                letter-spacing: -0.01em;
            }
            .subtitle {
                font-size: 14px;
                color: var(--grey);
                margin-bottom: 32px;
            }
            .input-group { margin-bottom: 18px; }
            .input-group label {
                display: block;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: var(--grey);
                margin-bottom: 8px;
            }
            /* font: inherit + fixed height + line-height keep the password
               dots vertically centered and metrically identical to the
               Associate ID field across browsers */
            .input-group input {
                width: 100%;
                height: 48px;
                padding: 0 16px;
                font: inherit;
                font-size: 15px;
                line-height: 48px;
                border-radius: 6px;
                border: 1px solid var(--line);
                background: #FAFAFA;
                color: var(--ink);
                outline: none;
                transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
            }
            .input-group input::placeholder { color: #8C8C8C; }
            .input-group input:focus {
                background: #FFFFFF;
                border-color: var(--honda-red);
                box-shadow: 0 0 0 3px rgba(204, 0, 0, 0.14);
            }
            /* Invalid-credentials state: red border + inline message,
               with a one-shot horizontal shake on page render */
            @keyframes field-shake {
                0%, 100% { transform: translateX(0); }
                20% { transform: translateX(-6px); }
                40% { transform: translateX(6px); }
                60% { transform: translateX(-4px); }
                80% { transform: translateX(4px); }
            }
            .input-group input.input-error {
                border-color: var(--error-red);
                background: #FFFBFB;
                animation: field-shake 0.35s ease;
            }
            @media (prefers-reduced-motion: reduce) {
                .input-group input.input-error { animation: none; }
            }
            .input-group input.input-error:focus {
                border-color: var(--error-red);
                box-shadow: 0 0 0 3px rgba(180, 35, 24, 0.14);
            }
            .field-error {
                font-size: 12px;
                font-weight: 600;
                color: var(--error-red);
                margin-top: 6px;
            }
            .forgot-row {
                text-align: right;
                margin: -8px 0 4px;
            }
            .forgot-row a {
                font-size: 13px;
                font-weight: 600;
                color: var(--honda-red);
                text-decoration: none;
            }
            .forgot-row a:hover { text-decoration: underline; }
            .forgot-row a:focus-visible {
                outline: 2px solid var(--honda-red);
                outline-offset: 2px;
                border-radius: 2px;
            }
            .submit-btn {
                width: 100%;
                height: 48px;
                border-radius: 6px;
                background: var(--honda-red);
                color: #FFFFFF;
                border: none;
                font: inherit;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.04em;
                cursor: pointer;
                margin-top: 10px;
                transition: background 0.15s ease, transform 0.1s ease;
            }
            .submit-btn:hover { background: var(--honda-red-dark); }
            .submit-btn:active { transform: scale(0.99); }
            .submit-btn:focus-visible {
                outline: 2px solid var(--ink);
                outline-offset: 2px;
            }

            .error {
                background: #FDECEC;
                border: 1px solid #F5C2C2;
                color: var(--error-red);
                font-size: 13px;
                font-weight: 600;
                padding: 10px 14px;
                border-radius: 6px;
                margin-bottom: 20px;
            }
            .card-foot {
                margin-top: 28px;
                font-size: 12px;
                color: var(--grey);
                text-align: center;
            }
            /* ── Responsive: panels stack; brand becomes a compact banner ── */
            @media (max-width: 860px) {
                body { flex-direction: column; }
                .brand-panel {
                    flex: none;
                    flex-direction: row;
                    align-items: center;
                    justify-content: space-between;
                    padding: 20px 24px;
                    border-right: none;
                    border-bottom: 4px solid var(--honda-red);
                }
                .brand-tagline, .brand-foot { display: none; }
                .brand-panel::after { display: none; }
                .brand-wing { height: 24px; }
                .brand-word { font-size: 20px; }
                .form-panel { padding: 32px 24px; }
            }
        </style>
    </head>
    <body>
        <div class="brand-panel">
            <div class="brand-mark">
                <img src="/assets/honda-wing.png" alt="Honda wing logo" class="brand-wing">
                <div class="brand-word">HONDA</div>
            </div>
            <div class="brand-tagline">
                <h2>The Power of Dreams — <span>How we move you</span></h2>
                <p>IT Analytics Dashboard — internal service desk intelligence for Change Requests, Service Requests and Incidents.</p>
            </div>
            <div class="brand-foot">HONDA · INTERNAL USE ONLY</div>
        </div>
        <div class="form-panel">
            <div class="login-card">
                <div class="red-rule"></div>
                <div class="title">Sign in</div>
                <div class="subtitle">Use your Honda associate credentials to access the IT Analytics Dashboard.</div>
                {% if error %}
                <div class="error" role="alert">{{ error }}</div>
                {% endif %}
                <form method="POST" autocomplete="off">
                    <div class="input-group">
                        <label for="username">Associate ID</label>
                        <input type="text" id="username" name="username" value=""
                               placeholder="Enter your Associate ID" required autofocus
                               autocomplete="off" class="{{ 'input-error' if error }}">
                    </div>
                    <div class="input-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password"
                               placeholder="Enter your password" required
                               autocomplete="off" class="{{ 'input-error' if error }}">
                        {% if error %}
                        <div class="field-error">Invalid Associate ID or password.</div>
                        {% endif %}
                    </div>
                    <div class="forgot-row">
                        <a href="/forgot-password">Forgot password?</a>
                    </div>
                    <button type="submit" class="submit-btn">SIGN IN</button>
                </form>

                <div class="card-foot">Authorized personnel only · Honda IT Service Desk</div>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, error=error)

@server.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@server.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def forgot_password():
    submitted = False
    associate_id = ""
    error = None
    if request.method == 'POST':
        associate_id = (request.form.get('username') or "").strip()
        submitted = True
        
        # Always show success, but only do DB/Email work if user exists
        if user_exists(associate_id):
            raw_token = create_reset_token(associate_id)
            reset_url = request.url_root.rstrip('/') + f'/reset-password?token={raw_token}'
            # For simplicity, we assume username/associate_id is their email or they have a known email
            # We'll use a dummy email address for demonstration if it's just '123'
            # In a real app we'd fetch their actual email address from the DB
            to_email = f"{associate_id}@honda.com"
            send_reset_email(to_email, reset_url)

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Reset Password | Honda IT Analytics</title>
        <style>
            :root {
                --honda-red: #E60012;
                --honda-red-dark: #A50000;
                --ink: #1A1A1A;
                --grey: #595959;             /* AA on white for 12px+ labels */
                --line: #D9D9D9;
                --error-red: #B42318;        /* AA on white & on #FDECEC */
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                background: #FFFFFF;
                color: var(--ink);
            }
            .brand-panel {
                flex: 1.1;
                background: linear-gradient(135deg,
                    #000000 0%,
                    #141414 42%,
                    #4A0000 74%,
                    var(--honda-red) 118%);
                border-right: 4px solid var(--honda-red);
                color: #FFFFFF;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 48px 56px;
                position: relative;
                overflow: hidden;
            }
            .brand-panel::after {
                content: "";
                position: absolute;
                top: -12%;
                right: 10%;
                width: 130px;
                height: 124%;
                background: repeating-linear-gradient(
                    90deg,
                    rgba(255, 255, 255, 0.09) 0px,
                    rgba(255, 255, 255, 0.09) 1px,
                    transparent 1px,
                    transparent 44px
                );
                transform: rotate(24deg);
                pointer-events: none;
            }
            .brand-mark {
                display: flex;
                align-items: center;
                gap: 14px;
                position: relative;
                z-index: 1;
            }
            .brand-wing {
                height: 32px;
                width: auto;
                display: block;
            }
            .brand-word {
                font-size: 26px;
                font-weight: 800;
                letter-spacing: 0.35em;
                color: var(--honda-red);
            }
            .brand-tagline {
                position: relative;
                z-index: 1;
            }
            .brand-tagline h2 {
                font-size: 34px;
                font-weight: 700;
                line-height: 1.25;
                margin: 0 0 14px;
                letter-spacing: -0.01em;
            }
            .brand-tagline h2 span { color: #FFB3B3; }
            .brand-tagline p {
                font-size: 15px;
                color: rgba(255,255,255,0.78);
                margin: 0;
                max-width: 400px;
                line-height: 1.6;
            }
            .brand-foot {
                font-size: 12px;
                color: rgba(255,255,255,0.66);
                letter-spacing: 0.08em;
                position: relative;
                z-index: 1;
            }
            .form-panel {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px;
            }
            .login-card {
                width: 100%;
                max-width: 380px;
            }
            .red-rule {
                width: 44px;
                height: 4px;
                background: var(--honda-red);
                border-radius: 2px;
                margin-bottom: 24px;
            }
            .title { font-size: 26px; font-weight: 700; margin-bottom: 6px; letter-spacing: -0.01em; }
            .subtitle { font-size: 14px; color: var(--grey); margin-bottom: 32px; line-height: 1.6;}
            .input-group { margin-bottom: 18px; }
            .input-group label {
                display: block; font-size: 12px; font-weight: 700; letter-spacing: 0.06em;
                text-transform: uppercase; color: var(--grey); margin-bottom: 8px;
            }
            .input-group input {
                width: 100%; height: 48px; padding: 0 16px; font: inherit; font-size: 15px;
                line-height: 48px; border-radius: 6px; border: 1px solid var(--line);
                background: #FAFAFA; color: var(--ink); outline: none;
                transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
            }
            .input-group input::placeholder { color: #8C8C8C; }
            .input-group input:focus {
                background: #FFFFFF; border-color: var(--honda-red);
                box-shadow: 0 0 0 3px rgba(204, 0, 0, 0.14);
            }
            .submit-btn {
                width: 100%; height: 48px; border-radius: 6px; background: var(--honda-red);
                color: #FFFFFF; border: none; font: inherit; font-size: 15px; font-weight: 700;
                letter-spacing: 0.04em; cursor: pointer; margin-top: 6px;
                transition: background 0.15s ease, transform 0.1s ease;
            }
            .submit-btn:hover { background: var(--honda-red-dark); }
            .submit-btn:active { transform: scale(0.99); }
            .submit-btn:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
            
            .confirm-box {
                background: #F0F9F1;
                border: 1px solid #B7E0BC;
                border-radius: 6px;
                padding: 18px;
                margin-bottom: 24px;
            }
            .confirm-title { font-size: 15px; font-weight: 700; color: #1E7A2E; margin-bottom: 6px; }
            .confirm-text { font-size: 13px; color: var(--ink); line-height: 1.6; }
            .back-row { margin-top: 24px; text-align: center; }
            .back-row a {
                font-size: 13px; font-weight: 600; color: var(--honda-red); text-decoration: none;
            }
            .back-row a:hover { text-decoration: underline; }
            .card-foot { margin-top: 28px; font-size: 12px; color: var(--grey); text-align: center; }
            
            @media (max-width: 860px) {
                body { flex-direction: column; }
                .brand-panel {
                    flex: none; flex-direction: row; align-items: center; justify-content: space-between;
                    padding: 20px 24px; border-right: none; border-bottom: 4px solid var(--honda-red);
                }
                .brand-tagline, .brand-foot { display: none; }
                .brand-panel::after { display: none; }
                .brand-wing { height: 24px; }
                .brand-word { font-size: 20px; }
                .form-panel { padding: 32px 24px; }
            }
        </style>
    </head>
    <body>
        <div class="brand-panel">
            <div class="brand-mark">
                <img src="/assets/honda-wing.png" alt="Honda wing logo" class="brand-wing">
                <div class="brand-word">HONDA</div>
            </div>
            <div class="brand-tagline">
                <h2>The Power of Dreams — <span>How we move you</span></h2>
                <p>IT Analytics Dashboard — internal service desk intelligence for Change Requests, Service Requests and Incidents.</p>
            </div>
            <div class="brand-foot">HONDA · INTERNAL USE ONLY</div>
        </div>
        <div class="form-panel">
            <div class="login-card">
                <div class="red-rule"></div>
                {% if submitted %}
                <div class="title">Request received</div>
                <div class="subtitle">Your password reset request has been logged.</div>
                <div class="confirm-box" role="status">
                    <div class="confirm-title">&#10003; Reset email sent</div>
                    <div class="confirm-text">
                        If <b>{{ associate_id }}</b> is a registered Associate ID, an email has been sent with a link to reset your password. The link will expire in 30 minutes.
                    </div>
                </div>
                {% else %}
                <div class="title">Reset your password</div>
                <div class="subtitle">Enter your Associate ID and we&#8217;ll send you a secure link to reset your password.</div>
                <form method="POST" autocomplete="off">
                    <div class="input-group">
                        <label for="username">Associate ID</label>
                        <input type="text" id="username" name="username"
                               placeholder="Enter your Associate ID" required autofocus autocomplete="off">
                    </div>
                    <button type="submit" class="submit-btn">REQUEST RESET</button>
                </form>
                {% endif %}
                <div class="back-row"><a href="/login">&#8592; Back to sign in</a></div>
                <div class="card-foot">Authorized personnel only &#183; Honda IT Service Desk</div>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, submitted=submitted, associate_id=associate_id, error=error)

@server.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    error = None
    success = False
    
    if not token:
        error = "No reset token provided. Please request a new password reset."
        associate_id = None
    else:
        associate_id = validate_reset_token(token)
        if not associate_id:
            error = "Invalid or expired reset token. Please request a new password reset."
            
    if request.method == 'POST' and associate_id:
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            error = "Passwords do not match."
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters long."
        else:
            update_password(associate_id, new_password, token)
            success = True

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Set New Password | Honda IT Analytics</title>
        <style>
            :root {
                --honda-red: #E60012;
                --honda-red-dark: #A50000;
                --ink: #1A1A1A;
                --grey: #595959;
                --line: #D9D9D9;
                --error-red: #B42318;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                background: #FFFFFF;
                color: var(--ink);
            }
            .brand-panel {
                flex: 1.1;
                background: linear-gradient(135deg,
                    #000000 0%, #141414 42%, #4A0000 74%, var(--honda-red) 118%);
                border-right: 4px solid var(--honda-red);
                color: #FFFFFF; display: flex; flex-direction: column;
                justify-content: space-between; padding: 48px 56px;
                position: relative; overflow: hidden;
            }
            .brand-panel::after {
                content: ""; position: absolute; top: -12%; right: 10%; width: 130px; height: 124%;
                background: repeating-linear-gradient(90deg, rgba(255,255,255,0.09) 0px, rgba(255,255,255,0.09) 1px, transparent 1px, transparent 44px);
                transform: rotate(24deg); pointer-events: none;
            }
            .brand-mark { display: flex; align-items: center; gap: 14px; position: relative; z-index: 1; }
            .brand-wing { height: 32px; width: auto; display: block; }
            .brand-word { font-size: 26px; font-weight: 800; letter-spacing: 0.35em; color: var(--honda-red); }
            .brand-tagline { position: relative; z-index: 1; }
            .brand-tagline h2 { font-size: 34px; font-weight: 700; line-height: 1.25; margin: 0 0 14px; letter-spacing: -0.01em; }
            .brand-tagline h2 span { color: #FFB3B3; }
            .brand-tagline p { font-size: 15px; color: rgba(255,255,255,0.78); margin: 0; max-width: 400px; line-height: 1.6; }
            .brand-foot { font-size: 12px; color: rgba(255,255,255,0.66); letter-spacing: 0.08em; position: relative; z-index: 1; }
            
            .form-panel { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px; }
            .login-card { width: 100%; max-width: 380px; }
            .red-rule { width: 44px; height: 4px; background: var(--honda-red); border-radius: 2px; margin-bottom: 24px; }
            .title { font-size: 26px; font-weight: 700; margin-bottom: 6px; letter-spacing: -0.01em; }
            .subtitle { font-size: 14px; color: var(--grey); margin-bottom: 32px; line-height: 1.6;}
            .input-group { margin-bottom: 18px; }
            .input-group label { display: block; font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--grey); margin-bottom: 8px; }
            .input-group input { width: 100%; height: 48px; padding: 0 16px; font: inherit; font-size: 15px; line-height: 48px; border-radius: 6px; border: 1px solid var(--line); background: #FAFAFA; color: var(--ink); outline: none; transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease; }
            .input-group input::placeholder { color: #8C8C8C; }
            .input-group input:focus { background: #FFFFFF; border-color: var(--honda-red); box-shadow: 0 0 0 3px rgba(204, 0, 0, 0.14); }
            
            .error { background: #FDECEC; border: 1px solid #F5C2C2; color: var(--error-red); font-size: 13px; font-weight: 600; padding: 10px 14px; border-radius: 6px; margin-bottom: 20px; }
            .confirm-box { background: #F0F9F1; border: 1px solid #B7E0BC; border-radius: 6px; padding: 18px; margin-bottom: 24px; }
            .confirm-title { font-size: 15px; font-weight: 700; color: #1E7A2E; margin-bottom: 6px; }
            .confirm-text { font-size: 13px; color: var(--ink); line-height: 1.6; }
            
            .submit-btn { width: 100%; height: 48px; border-radius: 6px; background: var(--honda-red); color: #FFFFFF; border: none; font: inherit; font-size: 15px; font-weight: 700; letter-spacing: 0.04em; cursor: pointer; margin-top: 10px; transition: background 0.15s ease, transform 0.1s ease; }
            .submit-btn:hover { background: var(--honda-red-dark); }
            .submit-btn:active { transform: scale(0.99); }
            .submit-btn:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
            
            .back-row { margin-top: 24px; text-align: center; }
            .back-row a { font-size: 13px; font-weight: 600; color: var(--honda-red); text-decoration: none; }
            .back-row a:hover { text-decoration: underline; }
            .card-foot { margin-top: 28px; font-size: 12px; color: var(--grey); text-align: center; }
            
            @media (max-width: 860px) {
                body { flex-direction: column; }
                .brand-panel { flex: none; flex-direction: row; align-items: center; justify-content: space-between; padding: 20px 24px; border-right: none; border-bottom: 4px solid var(--honda-red); }
                .brand-tagline, .brand-foot { display: none; }
                .brand-panel::after { display: none; }
                .brand-wing { height: 24px; }
                .brand-word { font-size: 20px; }
                .form-panel { padding: 32px 24px; }
            }
        </style>
    </head>
    <body>
        <div class="brand-panel">
            <div class="brand-mark">
                <img src="/assets/honda-wing.png" alt="Honda wing logo" class="brand-wing">
                <div class="brand-word">HONDA</div>
            </div>
            <div class="brand-tagline">
                <h2>The Power of Dreams — <span>How we move you</span></h2>
                <p>IT Analytics Dashboard — internal service desk intelligence for Change Requests, Service Requests and Incidents.</p>
            </div>
            <div class="brand-foot">HONDA · INTERNAL USE ONLY</div>
        </div>
        <div class="form-panel">
            <div class="login-card">
                <div class="red-rule"></div>
                {% if success %}
                <div class="title">Password reset!</div>
                <div class="subtitle">Your password has been successfully updated.</div>
                <div class="confirm-box" role="status">
                    <div class="confirm-title">&#10003; Success</div>
                    <div class="confirm-text">You can now sign in with your new password.</div>
                </div>
                <a href="/login"><button type="button" class="submit-btn">SIGN IN</button></a>
                {% else %}
                <div class="title">Set new password</div>
                <div class="subtitle">Enter your new password below.</div>
                
                {% if error %}
                <div class="error" role="alert">{{ error }}</div>
                {% endif %}
                
                {% if associate_id %}
                <form method="POST" autocomplete="off">
                    <div class="input-group">
                        <label for="password">New Password</label>
                        <input type="password" id="password" name="password"
                               placeholder="Min 6 characters" required autofocus autocomplete="off">
                    </div>
                    <div class="input-group">
                        <label for="confirm_password">Confirm Password</label>
                        <input type="password" id="confirm_password" name="confirm_password"
                               placeholder="Re-enter password" required autocomplete="off">
                    </div>
                    <button type="submit" class="submit-btn">UPDATE PASSWORD</button>
                </form>
                {% else %}
                <div class="back-row" style="margin-top: 10px;"><a href="/forgot-password">Request new reset link</a></div>
                {% endif %}
                
                {% endif %}
                
                {% if not success %}
                <div class="back-row"><a href="/login">&#8592; Back to sign in</a></div>
                {% endif %}
                <div class="card-foot">Authorized personnel only &#183; Honda IT Service Desk</div>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, success=success, error=error, associate_id=associate_id)

# ── CSS Variables ─────────────────────────────────────────────────────────────
SIDEBAR_BG   = "var(--bg-sidebar)"
SIDEBAR_BORD = "var(--border-color)"
TEXT_DARK    = "var(--text-p)"
TEXT_MID     = "var(--text-mid)"
TEXT_MUTED   = "var(--text-s)"
ACCENT       = "var(--accent)"

NAV_ITEMS = [
    {"label": "Change Requests", "href": "/cr", "icon": "bi bi-check-circle"},
    {"label": "Service Requests", "href": "/sr", "icon": "bi bi-file-earmark-text"},
    {"label": "Incidents", "href": "/incident", "icon": "bi bi-exclamation-triangle"},
    {"label": "Notifications", "href": "/notifications", "icon": "bi bi-bell"},
]


def nav_link(label, href, icon):
    return dcc.Link(
        html.Div([
            html.Div(id={"type": "nav-indicator", "index": href}, style={
                "position": "absolute", "left": "0", "top": "50%", "transform": "translateY(-50%)",
                "width": "2px", "height": "0px", "background": "var(--text-p)", "borderRadius": "1px",
                "transition": "height 0.15s ease",
            }),
            html.I(className=icon, style={"marginRight": "10px", "fontSize": "15px", "color": "inherit"}),
            html.Span(label, style={"fontSize": "14px", "fontWeight": "500"}),
        ], id={"type": "nav-item", "index": href}, className="nav-item", style={
            "padding":       "10px 14px",
            "cursor":        "pointer",
            "borderRadius":  "6px",
            "display":       "flex",
            "alignItems":    "center",
            "marginBottom":  "2px",
            "transition":    "color 0.15s ease",
            "position":      "relative",
            "overflow":      "visible"
        }),
        href=href,
        style={"textDecoration": "none"},
        className="nav-link-custom"
    )


app.layout = html.Div([
    dcc.Location(id="url"),

    # Global store for notifications
    dcc.Store(id="global-notif-store", storage_type="session", data=[]),

    # ── Sidebar ───────────────────────────────────────────────────────────────
    html.Div([
        # Brand
        html.Div([
            html.Div("Workspace", style={
                "fontWeight": "600", "fontSize": "15px", "color": TEXT_DARK, "letterSpacing": "-0.3px",
            }),
            html.Div("IT Analytics", style={"fontSize": "12px", "color": TEXT_MUTED, "marginTop": "2px", "fontWeight": "400"}),
        ], style={"padding": "24px 20px 20px"}),

        # Nav links
        html.Div([nav_link(i["label"], i["href"], i["icon"]) for i in NAV_ITEMS],
                 className="sidebar-nav-container", style={"padding": "0 8px"}),

        # Bottom — profile & theme toggle
        html.Div([
            dcc.Link(
                html.Div([
                    html.Div("AU", style={
                        "width":          "30px",
                        "height":         "30px",
                        "borderRadius":   "50%",
                        "border":         "1px solid var(--border-color)",
                        "background":     "transparent",
                        "color":          "var(--text-p)",
                        "display":        "flex",
                        "alignItems":     "center",
                        "justifyContent": "center",
                        "fontWeight":     "500",
                        "fontSize":       "12px",
                        "marginRight":    "10px"
                    }),
                    html.Div([
                        html.Div("Admin User", style={"fontSize": "13px", "fontWeight": "500", "color": TEXT_DARK}),
                        html.Div("View Profile", style={"fontSize": "11px", "color": TEXT_MUTED}),
                    ], style={"marginLeft": "10px", "flex": "1"}),
                ], className="nav-item", style={
                    "display": "flex", "alignItems": "center", "padding": "10px 14px",
                    "borderRadius": "6px", "cursor": "pointer", "transition": "background-color 0.15s ease"
                }),
                href="/profile",
                style={"textDecoration": "none"}
            ),
        ], style={
            "position": "absolute", "bottom": "0", "left": "0", "right": "0",
            "padding": "16px", "borderTop": "1px solid var(--border-color)",
            "background": "var(--bg-sidebar)",
            "display": "flex", "flexDirection": "column", "gap": "4px"
        })
    ], className="sidebar-container", style={
        "width":        "240px",
        "minWidth":     "240px",
        "height":       "100vh",
        "background":   SIDEBAR_BG,
        "borderRight":  "none",
        "position":     "fixed",
        "top":          "0",
        "left":         "0",
        "zIndex":       100,
        "fontFamily":   "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif",
    }),

    html.Div(id="cmdk-overlay", style={
        "position": "fixed", "top": "0", "left": "0", "right": "0", "bottom": "0",
        "background": "var(--bg-overlay)",
        "zIndex": "999999", "display": "none",
        "alignItems": "flex-start", "justifyContent": "center", "paddingTop": "120px",
    }, children=[
        html.Div([
            dcc.Input(id="cmdk-input", type="text", placeholder="Search pages, tickets, workgroups...",
                style={
                    "width": "100%", "border": "none", "outline": "none",
                    "fontSize": "15px", "padding": "16px 20px", "borderRadius": "8px 8px 0 0",
                    "background": "var(--bg-card)", "color": "var(--text-p)",
                    "fontFamily": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif",
                }),
            html.Div(id="cmdk-results", style={"maxHeight": "400px", "overflowY": "auto", "padding": "4px", "background": "var(--bg-card)"}),
        ], style={
            "width": "520px", "background": "var(--bg-card)", "borderRadius": "18px",
            "border": "1px solid var(--border-light)",
            "boxShadow": "0 24px 64px rgba(0,0,0,0.2)", "overflow": "hidden",
        }),
    ]),
    dcc.Store(id="toast-store", data=""),

    # Theme toggle moved to components.py page_header

    html.Div(id="page-loading-bar", style={
        "position": "fixed", "top": "0", "left": "0", "height": "2px",
        "background": "var(--accent)",
        "width": "0%", "zIndex": "9999999", "transition": "width 0.3s ease, opacity 0.3s ease",
    }),

    # ── Page content ──────────────────────────────────────────────────────────
    # Today Strip moved to components.py page_header (today-summary-badges)
    dcc.Interval(id="today-strip-interval", interval=5*60*1000, n_intervals=0),

    html.Div([
    dash.page_container,
], className="page-container", style={"marginLeft": "240px", "minHeight": "100vh", "overflowX": "hidden", "fontFamily": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif"}),

    dcc.Store(id="legend-hint-shown", storage_type="local", data=False),

    # Dynamic Island Container (Initially hidden via CSS)
    html.Div(id="dynamic-island-container", className="dynamic-island"),

    html.Button(html.I(className="bi bi-chat-dots"), id="global-chat-toggle-btn", n_clicks=0, style={
        "position": "fixed", "bottom": "24px", "right": "24px",
        "width": "48px", "height": "48px", "borderRadius": "50%",
        "background": "var(--accent)",
        "border": "none", "cursor": "pointer", "fontSize": "20px", "color": "var(--accent-fg)",
        "display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "0",
        "zIndex": "99998",
    }),

    # Floating Chat Panel
    html.Div(id="global-chat-panel", style={
        "position": "fixed", "bottom": "84px", "right": "24px",
        "width": "380px", "height": "520px",
        "background": "var(--bg-panel)",
        "borderRadius": "8px",
        "border": "none",
        "boxShadow": "none",
        "zIndex": "99999",
        "display": "flex", "flexDirection": "column",
        "transform": "translateY(10px)",
        "opacity": "0", "pointerEvents": "none",
        "transition": "all 0.2s ease",
    }, children=[
        html.Div([
            html.Div([
                html.Div("⚡", style={
                    "fontSize": "16px", "marginRight": "8px",
                }),
                html.Div([
                    html.Div("IT Analytics Assistant", style={"fontWeight": "600", "fontSize": "14px", "color": "var(--text-p)"}),
                    html.Div("Online · Groq", style={"fontSize": "11px", "color": "var(--text-s)", "fontWeight": "400"}),
                ]),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Button(html.I(className="bi bi-x-lg"), id="global-chat-close-btn", style={
                "background": "transparent", "border": "1px solid var(--border-color)", "borderRadius": "4px",
                "width": "28px", "height": "28px", "cursor": "pointer", "fontSize": "12px",
                "color": "var(--text-s)", "display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "0",
            }),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                  "padding": "14px 16px", "borderBottom": "1px solid var(--border-color)"}),

        html.Div([
            dcc.Loading(
                html.Div(id="global-chat-messages", children=[
                    html.Div("Hi! Ask me anything about CR, SR, or Incident data.", style={
                        "background": "var(--bg-hover)", "color": "var(--text-p)",
                        "padding": "10px 14px", "borderRadius": "18px",
                        "fontSize": "13px", "maxWidth": "80%",
                    }),
                ], style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "10px",
                }),
                type="circle", color="var(--text-p)"
            )
        ], id="global-chat-messages-container", style={
            "flex": "1",
            "overflowY": "auto",
            "padding": "16px 20px",
            "minHeight": "0",
            "display": "flex",
            "flexDirection": "column",
        }),

        html.Div([
            dcc.Input(id="global-chat-input", type="text", placeholder="Ask anything...",
                n_submit=0, style={
                    "flex": "1",
                    "border": "1px solid var(--border-color)",
                    "borderRadius": "980px",
                    "padding": "10px 16px",
                    "fontSize": "13px",
                    "color": "var(--text-p)",
                    "background": "var(--bg-input)",
                    "outline": "none",
                }),
            html.Button("→", id="global-chat-send-btn", n_clicks=0, style={
                "width": "34px", "height": "34px", "borderRadius": "50%",
                "background": "var(--accent)", "color": "var(--accent-fg)", "border": "none",
                "cursor": "pointer", "marginLeft": "8px", "fontSize": "14px",
            }),
        ], style={
            "display": "flex", "alignItems": "center", "padding": "16px 20px",
            "borderTop": "1px solid var(--border-color)", "flexShrink": "0",
        }),

        dcc.Store(id="global-chat-history", data=[], storage_type="session"),
    ]),

    # ── Toast Notification Container ──────────────────────────────────────────
    html.Div(id="toast-container", style={
        "position": "fixed", "top": "24px", "right": "24px", "zIndex": "99999",
        "display": "flex", "flexDirection": "column", "gap": "12px",
        "pointerEvents": "none",
    }),

    # ── Keyboard Shortcuts Modal ──────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div([
                html.Span("Keyboard Shortcuts", style={
                    "fontWeight": "700", "fontSize": "16px", "color": "var(--text-p)",
                }),
                html.Button("×", id="shortcuts-close-btn", n_clicks=0, style={
                    "background": "none", "border": "none", "fontSize": "20px",
                    "cursor": "pointer", "color": "var(--text-s)", "padding": "0",
                }),
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px"}),
            html.Div([
                html.Div([
                    html.Kbd("Ctrl + K", style={
                        "background": "var(--bg-hover)", "borderRadius": "6px", "padding": "4px 10px",
                        "fontSize": "12px", "fontWeight": "600", "color": "var(--text-p)",
                        "border": "1px solid var(--border-color)", "fontFamily": "monospace",
                    }),
                    html.Span("Command Palette", style={"color": "var(--text-s)", "fontSize": "13px"}),
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "10px 0", "borderBottom": "1px solid var(--border-color)"}),
                html.Div([
                    html.Kbd("?", style={
                        "background": "var(--bg-hover)", "borderRadius": "6px", "padding": "4px 10px",
                        "fontSize": "12px", "fontWeight": "600", "color": "var(--text-p)",
                        "border": "1px solid var(--border-color)", "fontFamily": "monospace",
                    }),
                    html.Span("Keyboard Shortcuts", style={"color": "var(--text-s)", "fontSize": "13px"}),
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "10px 0", "borderBottom": "1px solid var(--border-color)"}),
                html.Div([
                    html.Kbd("Esc", style={
                        "background": "var(--bg-hover)", "borderRadius": "6px", "padding": "4px 10px",
                        "fontSize": "12px", "fontWeight": "600", "color": "var(--text-p)",
                        "border": "1px solid var(--border-color)", "fontFamily": "monospace",
                    }),
                    html.Span("Close Modal / Panel", style={"color": "var(--text-s)", "fontSize": "13px"}),
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "10px 0"}),
            ]),
        ], style={
            "background": "var(--bg-card)", "borderRadius": "8px", "padding": "20px",
            "width": "380px", "maxWidth": "90vw", "border": "1px solid var(--border-color)",
            "boxShadow": "0 8px 30px rgba(0,0,0,0.12)",
        }),
    ], id="shortcuts-modal", style={
        "position": "fixed", "top": "0", "left": "0", "width": "100vw", "height": "100vh",
        "display": "none", "alignItems": "center", "justifyContent": "center",
        "zIndex": "99998", "background": "var(--bg-overlay, rgba(0,0,0,0.5))",
    }),
])


@callback(
    Output({"type": "nav-item", "index": dash.dependencies.ALL}, "style"),
    Output({"type": "nav-indicator", "index": dash.dependencies.ALL}, "style"),
    Input("url", "pathname"),
    State({"type": "nav-item", "index": dash.dependencies.ALL}, "id")
)
def highlight_active_nav(pathname, item_ids):
    """Updates sidebar nav link styles based on current URL."""
    # Redirect root to /cr
    if pathname == "/":
        pathname = "/cr"
        
    styles = []
    indicator_styles = []
    for item_id in item_ids:
        is_active = pathname == item_id["index"]
        
        base_style = {
            "padding":       "10px 14px",
            "cursor":        "pointer",
            "borderRadius":  "6px",
            "display":       "flex",
            "alignItems":    "center",
            "marginBottom":  "2px",
            "transition":    "background-color 0.15s ease, color 0.15s ease",
            "position":      "relative",
            "overflow":      "hidden"
        }
        
        if is_active:
            styles.append({
                **base_style,
                "backgroundColor": "var(--bg-active)",
                "color": "var(--text-p)",
                "fontWeight": "600",
            })
            indicator_styles.append({"height": "20px"})
        else:
            styles.append({
                **base_style,
                "backgroundColor": "transparent",
                "color": TEXT_MID,
            })
            indicator_styles.append({"height": "0px"})
            
    return styles, indicator_styles


# Redirect root to /cr natively in index string logic below
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <!-- Apple System Fonts — SF Pro via -apple-system (no webfont needed) -->

        <!-- Feather Icons CDN -->
        <script src="https://unpkg.com/feather-icons"></script>

        <!-- Bootstrap Icons CDN -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">

        <!-- Root Redirect Script -->
        <script>
            if (window.location.pathname === '/') {
                window.location.replace('/cr');
            }
        </script>

        <style>
            /* ══════════════════════════════════════════════════════════════
               APPLE MINIMALIST DESIGN SYSTEM
               SF typography · #F5F5F7 canvas · frosted glass · soft shadows
               ══════════════════════════════════════════════════════════════ */

            /* ── Light Theme (Default) ── */
            :root {
                --bg-body:      #F5F5F7;
                --bg-sidebar:   rgba(255, 255, 255, 0.72);
                --bg-card:      #FFFFFF;
                --bg-hover:     #F5F5F7;
                --bg-glass:     rgba(255, 255, 255, 0.72);
                --bg-active:    #E8E8ED;
                --bg-panel:     rgba(255, 255, 255, 0.92);
                --bg-input:     #FFFFFF;
                --bg-overlay:   rgba(245, 245, 247, 0.8);
                --bg-solid:     #FFFFFF;

                --border-color: rgba(0, 0, 0, 0.08);
                --border-light: rgba(0, 0, 0, 0.05);
                --border-strong:rgba(0, 0, 0, 0.12);
                --border-hover: rgba(0, 0, 0, 0.15);

                --text-p:       #1D1D1F;
                --text-mid:     #494949;
                --text-s:       #86868B;

                --accent:       #0071E3;
                --accent-fg:    #FFFFFF;
                --shadow-diffused: none;

                --radius-card:  18px;
                --radius-btn:   980px;
                --font-apple:   -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }

            /* ── Global Typography & Background ──────────────────────── */
            body {
                font-family: var(--font-apple) !important;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                background: var(--bg-body) !important;
                background-size: unset !important;
                animation: none !important;
                color: var(--text-p);
                letter-spacing: -0.01em;
                margin: 0;
                min-height: 100vh;
                overflow-x: hidden;
                transition: background-color 0.25s ease, color 0.25s ease;
            }

            /* ── Chat Panel ──────────────────────────────────────────── */
            #global-chat-panel {
                max-height: 70vh !important;
                border-radius: var(--radius-card) !important;
                border: 1px solid var(--border-color) !important;
                box-shadow: 0 20px 60px rgba(0,0,0,0.15) !important;
                backdrop-filter: saturate(180%) blur(20px);
                -webkit-backdrop-filter: saturate(180%) blur(20px);
            }
            #global-chat-messages-container::-webkit-scrollbar {
                width: 4px;
            }
            #global-chat-messages-container::-webkit-scrollbar-thumb {
                background: var(--text-s);
                border-radius: 2px;
            }
            #global-chat-input {
                border-radius: var(--radius-btn) !important;
            }
            #global-chat-input:focus {
                border-color: var(--accent) !important;
                box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.18) !important;
            }
            #global-chat-send-btn {
                background: var(--accent) !important;
                color: var(--accent-fg) !important;
                border-radius: 50% !important;
                transition: opacity 0.15s ease, transform 0.15s ease;
            }
            #global-chat-send-btn:hover {
                opacity: 0.85;
            }
            #global-chat-toggle-btn {
                background: var(--accent) !important;
                color: var(--accent-fg) !important;
                box-shadow: 0 8px 24px rgba(0, 113, 227, 0.35) !important;
                transition: transform 0.2s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.2s ease !important;
            }
            #global-chat-toggle-btn:hover {
                transform: scale(1.06);
            }

            /* ── Sidebar (minimalist flat) ─────────────────────────────── */
            .sidebar-container {
                border-right: 1px solid var(--border-color) !important;
            }
            .nav-link-custom .nav-item {
                transition: background-color 0.15s ease, color 0.15s ease;
            }
            .nav-link-custom .nav-item:hover {
                color: var(--text-p) !important;
                transform: none;
            }
            .nav-link-custom .nav-item:active {
                opacity: 0.7;
                transform: none;
            }
            .nav-link-custom .nav-item:hover i {
                color: var(--text-p) !important;
            }

            /* ── Page Fade-in (subtle) ───────────────────────────────── */
            @keyframes fadeInUp {
                0%   { opacity: 0; transform: translateY(6px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .page-container {
                animation: fadeInUp 0.35s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
            }

            /* ── Splash Loading Screen ───────────────────────────────── */
            #apple-splash {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: var(--bg-body);
                display: flex; flex-direction: column; justify-content: center; align-items: center;
                z-index: 999999;
                animation: fadeOut 0.4s ease 0.8s forwards;
                pointer-events: none;
            }
            @keyframes fadeOut {
                to { opacity: 0; visibility: hidden; }
            }
            .apple-spinner {
                width: 24px; height: 24px;
                border: 2px solid rgba(0,0,0,0.1);
                border-top-color: var(--text-p);
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            @keyframes spin { to { transform: rotate(360deg); } }

            /* ── Loading States ───────────────────────────────────────── */
            [data-dash-is-loading="true"] {
                position: relative;
                pointer-events: none;
            }
            [data-dash-is-loading="true"] > * {
                visibility: hidden;
            }
            [data-dash-is-loading="true"]::after {
                content: "";
                position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                background: linear-gradient(90deg, var(--bg-card) 0%, var(--bg-hover) 50%, var(--bg-card) 100%);
                background-size: 200% 100%;
                animation: skeleton-shimmer 1.5s infinite;
                border-radius: var(--radius-card);
                z-index: 10;
            }
            @keyframes skeleton-shimmer {
                0%   { background-position: -200% 0; }
                100% { background-position: 200% 0; }
            }

            /* ── Card Styling (Apple Minimal) ────────────────────────────────── */
            .apple-card {
                background: var(--bg-body);
                border-radius: 0;
                padding: 24px;
                box-shadow: none;
                border: none;
            }
            .apple-card:hover {
                transform: none;
                box-shadow: none;
                border: none;
            }
/* ── Header (minimalist) ────────────────────────────── */
            .apple-header {
                background: var(--bg-body);
                border-bottom: 1px solid var(--border-color);
                position: sticky;
                top: 0;
                z-index: 10;
            }

            /* ── Dynamic Island Toast ────────────────────────────────── */
            .dynamic-island {
                position: fixed;
                top: 16px;
                left: 50%;
                transform: translate(-50%, -100%);
                background: var(--bg-panel);
                backdrop-filter: saturate(180%) blur(20px);
                -webkit-backdrop-filter: saturate(180%) blur(20px);
                border: 1px solid var(--border-light);
                border-radius: 980px;
                padding: 10px 22px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.14);
                z-index: 99999;
                display: flex;
                align-items: center;
                gap: 10px;
                opacity: 0;
                transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.25s ease;
                min-width: 280px;
                pointer-events: none;
            }
            .dynamic-island.show-island {
                transform: translate(-50%, 0);
                opacity: 1;
                pointer-events: auto;
            }

            .responsive-flex-row {
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 20px !important;
                width: 100%;
            }
            .apple-card { min-width: 0; }

            /* Chart cards: two per row on desktop, stack when narrow */
            .responsive-flex-row > .apple-card {
                flex: 1 1 380px !important;
                min-width: min(100%, 320px) !important;
            }
            /* KPI rows: five compact cards in one row at 100% zoom, wrap gracefully */
            #cr-kpi-row > div, #sr-kpi-row > div, #inc-kpi-row > div,
            #cr-kpi-row > .apple-card, #sr-kpi-row > .apple-card, #inc-kpi-row > .apple-card {
                flex: 1 1 180px !important;
                min-width: min(100%, 170px) !important;
            }
            /* Plotly must fill its card and never overflow it */
            .dash-graph, .js-plotly-plot, .js-plotly-plot .plot-container {
                width: 100% !important;
                max-width: 100% !important;
            }
            /* Fixed chart height — Plotly.Plots.resize() drops the figure's own
               height and reads the container instead, so the container must own it */
            .dash-graph {
                height: 320px !important;
            }
            .dash-graph .js-plotly-plot,
            .dash-graph .js-plotly-plot .plot-container {
                height: 100% !important;
            }

            .pulse-dot { animation: none; }
            .filter-btn-active {
                background: transparent !important;
                color: var(--text-p) !important;
                border-color: transparent !important;
                border-bottom: 2px solid var(--text-p) !important;
                border-radius: 0 !important;
            }

            #global-chat-send-btn:disabled {
                opacity: 0.3;
                cursor: wait;
            }
            #global-chat-input:disabled {
                opacity: 0.5;
                cursor: wait;
            }

            /* ── Date Picker Override (Apple minimal) ────────────────── */
            .SingleDatePickerInput__withBorder {
                background: transparent !important;
                border: none !important;
                border-radius: 0 !important;
            }
            .DateInput { background: transparent !important; width: 130px !important; }
            .DateInput_input {
                background: transparent !important;
                color: var(--text-p) !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                border-bottom: none !important;
                border-radius: 10px !important;
                padding: 8px 12px !important;
                cursor: pointer !important;
                font-family: var(--font-apple) !important;
            }
            .DateInput_input__focused { border-bottom: 1px solid var(--text-p) !important; }
            .SingleDatePicker_picker {
                background: var(--bg-card) !important;
                border-radius: var(--radius-card) !important;
                border: 1px solid var(--border-light) !important;
                box-shadow: 0 16px 48px rgba(0,0,0,0.16) !important;
                overflow: hidden !important;
                z-index: 9999 !important;
            }
            .DayPicker__withBorder { border-radius: var(--radius-card) !important; box-shadow: none !important; background: transparent !important; }
            .CalendarMonth, .CalendarMonthGrid { background: transparent !important; }
            .CalendarMonth_caption strong { color: var(--text-p) !important; font-size: 14px !important; font-weight: 600 !important; }
            .CalendarDay__default {
                border: none !important; border-radius: 50% !important;
                color: var(--text-p) !important; font-size: 13px !important; background: transparent !important;
            }
            .CalendarDay__default:hover {
                background: var(--bg-hover) !important;
                border-radius: 50% !important; color: var(--text-p) !important; border: none !important;
            }
            .CalendarDay__selected, .CalendarDay__selected:active, .CalendarDay__selected:hover {
                background: var(--accent) !important; border-radius: 50% !important;
                color: var(--accent-fg) !important; border: none !important;
            }
            .CalendarDay__today { color: var(--accent) !important; font-weight: 700 !important; }
            .CalendarDay__blocked_out_of_range, .CalendarDay__blocked_out_of_range:hover {
                color: var(--text-s) !important; background: transparent !important; border: none !important;
            }
            .DayPickerNavigation_button__default {
                border: 1px solid var(--border-color) !important; border-radius: 50% !important;
                background: transparent !important; padding: 4px !important;
            }
            .DayPickerNavigation_button__default:hover {
                background: var(--bg-hover) !important; border-color: var(--border-hover) !important;
            }
            .DayPicker_weekHeader_li small { color: var(--text-s) !important; font-weight: 600 !important; font-size: 11px !important; }
            .DateInput_fang { display: none !important; }
        </style>
    </head>
    <body>
        <div id="apple-splash">
            <div class="apple-spinner"></div>
            <div style="margin-top: 12px; font-weight: 500; color: var(--text-s); font-size: 12px; letter-spacing: 1px; text-transform: uppercase;">Loading</div>
        </div>
        
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
            <script>feather.replace()</script>
            <script>
                const observer = new MutationObserver((mutations) => {
                    feather.replace();
                });
                observer.observe(document.body, { childList: true, subtree: true });
            </script>
            <script>
                /* Keep Plotly charts sized to their cards. Fixes charts rendered
                   inside collapsed sections / while hidden, and any container
                   resize from flex wrapping or browser zoom changes. */
                (function () {
                    var ro = new ResizeObserver(function (entries) {
                        entries.forEach(function (entry) {
                            var gd = entry.target.querySelector('.js-plotly-plot');
                            if (!gd || !window.Plotly) return;
                            if (entry.target.clientWidth === 0) return; // hidden — skip
                            try { window.Plotly.Plots.resize(gd); } catch (e) {}
                        });
                    });
                    function attach() {
                        document.querySelectorAll('.dash-graph').forEach(function (g) {
                            if (!g._roAttached) { g._roAttached = true; ro.observe(g); }
                        });
                    }
                    new MutationObserver(attach).observe(document.body, { childList: true, subtree: true });
                    attach();
                })();
            </script>
        </footer>
    </body>
</html>
'''


@callback(
    Output("global-chat-panel", "style"),
    Input("global-chat-toggle-btn", "n_clicks"),
    Input("global-chat-close-btn", "n_clicks"),
    State("global-chat-panel", "style"),
    prevent_initial_call=True,
)
def toggle_global_chat(open_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0]
    new_style = dict(current_style)
    if triggered == "global-chat-close-btn":
        new_style["transform"] = "translateY(10px)"
        new_style["opacity"] = "0"
        new_style["pointerEvents"] = "none"
    else:
        new_style["transform"] = "translateY(0)"
        new_style["opacity"] = "1"
        new_style["pointerEvents"] = "auto"
    return new_style


@callback(
    Output("global-chat-messages", "children"),
    Output("global-chat-history",  "data"),
    Output("global-chat-input",    "value"),
    Input("global-chat-send-btn",  "n_clicks"),
    Input("global-chat-input",     "n_submit"),
    State("global-chat-input",     "value"),
    State("global-chat-history",   "data"),
    prevent_initial_call=True,
    running=[
        (Output("global-chat-send-btn", "disabled"), True, False),
        (Output("global-chat-input", "disabled"), True, False),
    ],
)
def global_chat(n_clicks, n_submit, user_message, history):
    if not user_message or not user_message.strip():
        return dash.no_update, dash.no_update, ""

    # Fetch live CR data from MySQL for context
    try:
        engine = get_engine()
        cr_df = pd.read_sql("SELECT `Change Request Id`, `Status`, `Risk`, `Category`, `Owner Work Group Name`, `Description`, `Request Registration Time` FROM cr_report", engine)
        
        sr_df = pd.read_sql("""
            SELECT `Service Request ID`, `Subject`, `Status`, `Workgroup`, `Location`, `Classification`, `LogTime`
            FROM sr_report WHERE `Workgroup` IN ('IT Support (ALC)', 'IT Support (EVSM)')
        """, engine)
        if not sr_df.empty:
            sr_df["date"] = pd.to_datetime(sr_df["LogTime"], errors="coerce")
    
        inc_df = pd.read_sql("""
            SELECT `Incident ID`, `Symptom`, `Status`, `Workgroup`, `Location`, `Classification`, `Priority`, `Log Time`
            FROM incident_report WHERE `Workgroup` IN ('IT Support (ALC)', 'IT Support (EVSM)')
        """, engine)
        if not inc_df.empty:
            inc_df["date"] = pd.to_datetime(inc_df["Log Time"], errors="coerce")
    
        user_msg_lower = user_message.lower()
        
        need_cr  = any(w in user_msg_lower for w in ['cr', 'change request', 'change', 'migration', 'risk'])
        need_sr  = any(w in user_msg_lower for w in ['sr', 'service request', 'service', 'subject', 'location'])
        need_inc = any(w in user_msg_lower for w in ['incident', 'inc', 'symptom', 'priority'])
        
        if not need_cr and not need_sr and not need_inc:
            need_cr = need_sr = need_inc = True
        
        summary_lines = []
        
        if need_cr and not cr_df.empty:
            cr_df["_month_label"] = pd.to_datetime(cr_df["Request Registration Time"], errors="coerce").dt.strftime("%B %Y")
            summary_lines.append("=== CR DATA ===")
            summary_lines.append(f"Total CRs: {len(cr_df)}")
            summary_lines.append(f"Statuses: {cr_df['Status'].value_counts().to_dict()}")
            summary_lines.append(f"Risk: {cr_df['Risk'].value_counts().to_dict()}")
            summary_lines.append(f"Categories: {cr_df['Category'].value_counts().to_dict()}")
            summary_lines.append(f"Workgroups: {cr_df['Owner Work Group Name'].value_counts().to_dict()}")
            monthly_cr = cr_df['_month_label'].value_counts().to_dict()
            summary_lines.append(f"CR tickets created per month exact counts: {monthly_cr}")
            summary_lines.append(f"CR total: {len(cr_df)}")
            if any(w in user_msg_lower for w in ['list', 'show', 'find', 'which', 'detail', 'id', 'specific']):
                cr_records = []
                for _, row in cr_df.head(40).iterrows():
                    date_val = row.get('Request Registration Time')
                    date_str = str(date_val)[:10] if pd.notna(date_val) else "Unknown"
                    cr_records.append(f"CR-ID:{row.get('Change Request Id')} | Date:{date_str} | Status:{row.get('Status')} | Risk:{row.get('Risk')} | Workgroup:{row.get('Owner Work Group Name')}")
                note = f" (showing first 40 of {len(cr_df)})" if len(cr_df) > 40 else ""
                summary_lines.append(f"CR Records{note}:\n" + "\n".join(cr_records))
        
        if need_sr and not sr_df.empty:
            sr_df["_month_label"] = sr_df["date"].dt.strftime("%B %Y")
            summary_lines.append("\n=== SR DATA ===")
            summary_lines.append(f"Total SRs: {len(sr_df)}")
            summary_lines.append(f"Statuses: {sr_df['Status'].value_counts().to_dict()}")
            summary_lines.append(f"Workgroups: {sr_df['Workgroup'].value_counts().to_dict()}")
            summary_lines.append(f"Classifications: {sr_df['Classification'].value_counts().to_dict()}")
            monthly_sr = sr_df['_month_label'].value_counts().to_dict()
            summary_lines.append(f"SR tickets created per month exact counts: {monthly_sr}")
            summary_lines.append(f"SR total: {len(sr_df)}")
            if any(w in user_msg_lower for w in ['list', 'show', 'find', 'which', 'detail', 'id', 'specific']):
                sr_records = []
                for _, row in sr_df.head(40).iterrows():
                    date_str = str(row.get('date'))[:10] if pd.notna(row.get('date')) else "Unknown"
                    sr_records.append(f"SR-ID:{row.get('Service Request ID')} | Date:{date_str} | Status:{row.get('Status')} | Workgroup:{row.get('Workgroup')} | Subject:{str(row.get('Subject',''))[:60]}")
                note = f" (showing first 40 of {len(sr_df)})" if len(sr_df) > 40 else ""
                summary_lines.append(f"SR Records{note}:\n" + "\n".join(sr_records))
        
        if need_inc and not inc_df.empty:
            inc_df["_month_label"] = inc_df["date"].dt.strftime("%B %Y")
            summary_lines.append("\n=== INCIDENT DATA ===")
            summary_lines.append(f"Total Incidents: {len(inc_df)}")
            summary_lines.append(f"Statuses: {inc_df['Status'].value_counts().to_dict()}")
            summary_lines.append(f"Workgroups: {inc_df['Workgroup'].value_counts().to_dict()}")
            summary_lines.append(f"Classifications: {inc_df['Classification'].value_counts().to_dict()}")
            summary_lines.append(f"Priorities: {inc_df['Priority'].value_counts().to_dict()}")
            monthly_inc = inc_df['_month_label'].value_counts().to_dict()
            summary_lines.append(f"Incident tickets created per month exact counts: {monthly_inc}")
            summary_lines.append(f"Incident total: {len(inc_df)}")
            if any(w in user_msg_lower for w in ['list', 'show', 'find', 'which', 'detail', 'id', 'specific']):
                inc_records = []
                for _, row in inc_df.head(40).iterrows():
                    date_str = str(row.get('date'))[:10] if pd.notna(row.get('date')) else "Unknown"
                    inc_records.append(f"INC-ID:{row.get('Incident ID')} | Date:{date_str} | Status:{row.get('Status')} | Priority:{row.get('Priority')} | Workgroup:{row.get('Workgroup')} | Symptom:{str(row.get('Symptom',''))[:60]}")
                note = f" (showing first 40 of {len(inc_df)})" if len(inc_df) > 40 else ""
                summary_lines.append(f"Incident Records{note}:\n" + "\n".join(inc_records))
        
        db_context = "\n".join(summary_lines)
    
    except Exception as e:
        db_context = f"Database error: {str(e)}"

    # Build conversation history for multi-turn chat
    messages = []
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    system_prompt = f"""You are a helpful, intelligent IT Analytics Assistant. You have two capabilities:

1. DATABASE ACCESS: You have direct access to live CR (Change Request), SR (Service Request), and Incident data from the company's MySQL database, summarized below. Use this data to answer specific questions about tickets, trends, counts, statuses, risks, and records.

2. GENERAL KNOWLEDGE: You can also answer any general question the user asks — programming questions, definitions, explanations, how-to questions, or anything unrelated to the database (e.g. "what is Python", "explain REST APIs", "how does SQL JOIN work"). Answer these normally using your own knowledge, just like a regular AI assistant would.

Decide which type of question is being asked and respond appropriately. If it's a database question, use the live data below. If it's a general question, answer directly without forcing in irrelevant database info.

Current Live Database Data:
{db_context}

Rules for database questions:
- Use exact numbers from the data provided, never estimate
- For month-specific counts use the "tickets created per month" values
- List specific record IDs when asked for details
- Be concise and well formatted

Rules for general questions:
- Answer naturally and helpfully like a knowledgeable assistant
- Keep answers concise but complete
- Use formatting (bullet points, code blocks) when helpful"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=1000,
            messages=[{"role": "system", "content": system_prompt}] + messages,
        )
        assistant_reply = response.choices[0].message.content
    except Exception as e:
        assistant_reply = f"Error: {str(e)}"

    # Update history
    new_history = history + [
        {"role": "user",      "content": user_message},
        {"role": "assistant", "content": assistant_reply},
    ]

    # Build message bubbles
    bubbles = []
    for msg in new_history:
        is_user = msg["role"] == "user"
        bubbles.append(html.Div([
            html.Div(msg["content"], style={
                "background": "var(--accent)" if is_user else "var(--bg-hover)",
                "color": "var(--accent-fg)" if is_user else "var(--text-p)",
                "padding": "10px 14px",
                "borderRadius": "18px",
                "fontSize": "13px", "lineHeight": "1.5", "maxWidth": "80%",
                "whiteSpace": "pre-wrap",
            }),
        ], style={"display": "flex", "justifyContent": "flex-end" if is_user else "flex-start"}))

    return bubbles, new_history, ""

dash.clientside_callback(
    "function(children) { setTimeout(function() { var c = document.getElementById('global-chat-messages-container'); if(c) { c.scrollTop = c.scrollHeight; } }, 100); return window.dash_clientside.no_update; }",
    Output("global-chat-messages-container", "id"),
    Input("global-chat-messages", "children"),
    prevent_initial_call=True
)

# --- TEMPORARILY DISABLED ---
# This feature calculates and displays the 'Today' CR, SR, and Incident counts.
# It is temporarily disabled because the current database contains historical data 
# rather than live daily data. Uncomment the code below to restore functionality.
# 
# @callback(
#     Output("today-summary-badges", "children"),
#     Input("today-strip-interval", "n_intervals"),
# )
# def update_today_strip(n):
#     try:
#         from db import get_engine
#         import pandas as pd
#         engine = get_engine()
#         now = pd.Timestamp.now()
#         yesterday = now - pd.Timedelta(hours=24)
# 
#         cr_df = pd.read_sql("SELECT `Request Registration Time` FROM cr_report", engine)
#         cr_df["dt"] = pd.to_datetime(cr_df["Request Registration Time"], errors="coerce")
#         new_crs = int((cr_df["dt"] >= yesterday).sum())
# 
#         sr_df = pd.read_sql("SELECT `LogTime` FROM sr_report", engine)
#         sr_df["dt"] = pd.to_datetime(sr_df["LogTime"], errors="coerce")
#         new_srs = int((sr_df["dt"] >= yesterday).sum())
# 
#         inc_df = pd.read_sql("SELECT `Log Time` FROM incident_report", engine)
#         inc_df["dt"] = pd.to_datetime(inc_df["Log Time"], errors="coerce")
#         new_incs = int((inc_df["dt"] >= yesterday).sum())
# 
#         pill_style = {
#             "borderRadius": "9999px", "padding": "6px 14px", "fontSize": "13px", "fontWeight": "600",
#             "background": "var(--bg-glass)"
#         }
#         
#         return [
#             html.Div("Today", style={"fontSize": "13px", "color": "var(--text-s)", "fontWeight": "600", "display": "flex", "alignItems": "center", "marginRight": "4px"}),
#             html.Div(f"CR {new_crs}", className="hover-lift", style={**pill_style, "border": "1px solid #3B82F6", "color": "#3B82F6"}),
#             html.Div(f"SR {new_srs}", className="hover-lift", style={**pill_style, "border": "1px solid #A855F7", "color": "#A855F7"}),
#             html.Div(f"INC {new_incs}", className="hover-lift", style={**pill_style, "border": "1px solid #F97316", "color": "#F97316"}),
#         ]
#     except Exception:
#         return html.Div("Today: data unavailable", style={"fontSize": "13px", "color": "var(--text-s)"})

dash.clientside_callback(
    """function(data) {
        if (data) return data;
        setTimeout(function() {
            var legends = document.querySelectorAll('.legend');
            if (legends.length > 0) {
                var hint = document.createElement('div');
                hint.innerText = '💡 Click legend items to filter';
                hint.style.cssText = 'position:absolute; background:#007AFF; color:white; padding:6px 12px; border-radius:8px; font-size:11px; z-index:1000; pointer-events:none; opacity:0.95;';
                document.body.appendChild(hint);
                var rect = legends[0].getBoundingClientRect();
                hint.style.top = (rect.top - 30) + 'px';
                hint.style.left = rect.left + 'px';
                setTimeout(function(){ hint.remove(); }, 4000);
            }
        }, 1500);
        return true;
    }
    """,
    Output("legend-hint-shown", "data"),
    Input("legend-hint-shown", "data"),
)

dash.clientside_callback(
    """function(id) {
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                var overlay = document.getElementById('cmdk-overlay');
                if (overlay) {
                    overlay.style.display = overlay.style.display === 'none' ? 'flex' : 'none';
                    var input = document.getElementById('cmdk-input');
                    if (input && overlay.style.display === 'flex') setTimeout(function(){ input.focus(); }, 50);
                }
            }
            if (e.key === 'Escape') {
                var overlay = document.getElementById('cmdk-overlay');
                if (overlay) overlay.style.display = 'none';
                var shortcuts = document.getElementById('shortcuts-modal');
                if (shortcuts) shortcuts.style.display = 'none';
            }
            if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
                var active = document.activeElement;
                if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) return;
                e.preventDefault();
                var modal = document.getElementById('shortcuts-modal');
                if (modal) {
                    modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
                }
            }
        });
        return id;
    }
    """,
    Output("cmdk-overlay", "id"),
    Input("cmdk-overlay", "id"),
)



@callback(
    Output("cmdk-results", "children"),
    Input("cmdk-input", "value")
)
def update_cmdk_results(search_text):
    bi_map = {
        "file-text": "bi bi-file-earmark-text",
        "inbox": "bi bi-inbox",
        "alert-triangle": "bi bi-exclamation-triangle",
        "bell": "bi bi-bell",
    }
    pages = [
        {"name": "Change Requests", "url": "/cr", "icon": "file-text"},
        {"name": "Service Requests", "url": "/sr", "icon": "inbox"},
        {"name": "Incidents", "url": "/incident", "icon": "alert-triangle"},
        {"name": "Notifications", "url": "/notifications", "icon": "bell"},
    ]
    if not search_text:
        return []
    
    search_text = search_text.lower()
    results = [p for p in pages if search_text in p["name"].lower()]
    
    if not results:
        return html.Div("No results found.", style={"padding": "12px", "color": "var(--text-s)", "fontSize": "14px"})
        
    return [
        dcc.Link(
            html.Div([
                html.I(className=bi_map.get(p['icon'], 'bi bi-circle'), style={"marginRight": "12px", "color": "var(--text-s)"}),
                html.Span(p["name"], style={"fontWeight": "500", "color": "var(--text-p)"})
            ], style={"padding": "12px 16px", "display": "flex", "alignItems": "center", "borderRadius": "8px", "cursor": "pointer", "transition": "background 0.2s"}, className="cmdk-item-hover"),
            href=p["url"],
            style={"textDecoration": "none"}
        ) for p in results
    ]


# ── Shortcuts Modal Close ─────────────────────────────────────────────────────
dash.clientside_callback(
    """function(n_clicks) {
        var modal = document.getElementById('shortcuts-modal');
        if (modal) modal.style.display = 'none';
        return window.dash_clientside.no_update;
    }
    """,
    Output("shortcuts-modal", "style"),
    Input("shortcuts-close-btn", "n_clicks"),
    prevent_initial_call=True
)


# ── Toast Notification Helper (Clientside) ────────────────────────────────────
dash.clientside_callback(
    """function(msg) {
        if (!msg) return window.dash_clientside.no_update;
        var container = document.getElementById('toast-container');
        if (!container) return window.dash_clientside.no_update;
        var toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.innerHTML = '<span style="margin-right:8px;font-size:16px">✓</span>' + msg;
        container.appendChild(toast);
        setTimeout(function() {
            toast.classList.add('toast-exit');
            setTimeout(function() { toast.remove(); }, 400);
        }, 3000);
        return window.dash_clientside.no_update;
    }
    """,
    Output("toast-container", "children"),
    Input("toast-store", "data"),
    prevent_initial_call=True
)


if __name__ == '__main__':
    app.run(debug=True, port=8050)