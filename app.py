# pip install Flask requests msal
# winget install mkcert
# mkcert -install
# mkcert localhost

# Go to: https://portal.azure.com
# Register an app:
# Redirect URI: https://localhost:5000/auth/redirect
# Save the:
# Client ID 
# Client Secret 
# Tenant ID (or use common for multi-tenant)


from flask import Flask, redirect, url_for, session, request, render_template_string
from msal import ConfidentialClientApplication
import uuid
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  


CLIENT_ID = 'bd295cc0-7aa3-4aee-934d-7665d37a6654'
CLIENT_SECRET = '<supersecret>' # dans la vrai vie, il faudrait mettre ça dans une variable d'environnement
TENANT_ID = '4d8fa653-666b-49a1-8561-5e0e5c33a44a'  
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/auth/redirect"

SCOPE = ["User.Read"]
SESSION_TYPE = "filesystem"  

# MSAL client
def _build_msal_app(cache=None):
    return ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY,
        client_credential=CLIENT_SECRET, token_cache=cache)

def _build_auth_url():
    return _build_msal_app().get_authorization_request_url(
        scopes=SCOPE,
        state=str(uuid.uuid4()),
        redirect_uri=url_for("authorized", _external=True))

@app.route('/')
def index():
    if 'user' in session:
        user = session['user']
        return render_template_string("""
        <h2>Welcome {{ user['name'] }}</h2>
        <p>Email: {{ user['preferred_username'] }}</p>
        <a href="{{ url_for('logout') }}">Logout</a>
        """, user=user)
    return '<a href="/login">Login avec Microsoft</a>'

@app.route('/login')
def login():
    auth_url = _build_auth_url()
    return redirect(auth_url)

@app.route(REDIRECT_PATH)
def authorized():
    if request.args.get('error'):
        return f"Error: {request.args['error_description']}"

    if 'code' in request.args:
        code = request.args['code']
        result = _build_msal_app().acquire_token_by_authorization_code(
            code,
            scopes=SCOPE,
            redirect_uri=url_for("authorized", _external=True))
        
        if "id_token_claims" in result:
            session['user'] = result['id_token_claims']
            return redirect(url_for('index'))
        else:
            return f"Erreur avec le token: {result.get('error_description')}"

    return "Aucune code trouvé."

@app.route('/logout')
def logout():
    session.clear()
    return redirect(
        f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout' +
        f'?post_logout_redirect_uri={url_for("index", _external=True)}')

if __name__ == "__main__":
    app.run(debug=True, ssl_context=('localhost.pem', 'localhost-key.pem'))
