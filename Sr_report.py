import re

with open('c:/Users/Admin/OneDrive/Desktop/Call Analysis tool/Call-Analysis-Tool/Frontend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove `import dash_auth`
content = re.sub(r'^import dash_auth\n', '', content, flags=re.MULTILINE)

# 2. Add flask imports right after `from dash import ...`
content = content.replace(
    'from dash import html, dcc, Input, Output, State, callback\n',
    'from dash import html, dcc, Input, Output, State, callback\nfrom flask import request, session, redirect, render_template_string\n'
)

# 3. Replace auth = dash_auth.BasicAuth... with Flask server logic
flask_logic = """
# ── Authentication & Flask Routes ─────────────────────────────────────────────
server = app.server
server.secret_key = os.getenv("SECRET_KEY", "fallback-secret-for-dev")

@server.before_request
def check_login():
    if request.path in ['/login', '/logout', '/_favicon.ico']:
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
        if VALID_USERS.get(username) == password:
            session['logged_in'] = True
            return redirect('/')
        else:
            error = "Invalid credentials. Please try again."
            
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Login - IT Analytics Dashboard</title>
        <style>
            body {
                background: #F5F5F7;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif;
                margin: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }
            .login-card {
                background: #FFFFFF;
                border-radius: 18px;
                padding: 40px 32px;
                width: 320px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
                text-align: center;
            }
            .title {
                font-size: 24px;
                font-weight: 700;
                color: #1D1D1F;
                margin-bottom: 8px;
            }
            .subtitle {
                font-size: 14px;
                color: #86868B;
                margin-bottom: 32px;
            }
            .input-group {
                margin-bottom: 16px;
                text-align: left;
            }
            .input-group input {
                width: 100%;
                padding: 12px 16px;
                border-radius: 12px;
                border: 1px solid transparent;
                background: #F5F5F7;
                font-size: 14px;
                color: #1D1D1F;
                box-sizing: border-box;
                outline: none;
                transition: all 0.2s ease;
            }
            .input-group input:focus {
                background: #FFFFFF;
                border-color: #0071E3;
                box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.2);
            }
            .submit-btn {
                width: 100%;
                padding: 12px;
                border-radius: 980px;
                background: #0071E3;
                color: #FFFFFF;
                border: none;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 16px;
                transition: opacity 0.2s ease;
            }
            .submit-btn:hover {
                opacity: 0.9;
            }
            .error {
                color: #FF3B30;
                font-size: 13px;
                margin-bottom: 16px;
                font-weight: 500;
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="title">Log In</div>
            <div class="subtitle">IT Analytics Dashboard</div>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            <form method="POST">
                <div class="input-group">
                    <input type="text" name="username" placeholder="Username" required autofocus>
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Password" required>
                </div>
                <button type="submit" class="submit-btn">Continue</button>
            </form>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, error=error)

@server.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
"""

content = re.sub(r'# Login gate[\s\S]*?auth = dash_auth\.BasicAuth\(app, VALID_USERS\)\n', flask_logic, content)

with open('c:/Users/Admin/OneDrive/Desktop/Call Analysis tool/Call-Analysis-Tool/Frontend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
