from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import pyotp
import pyqrcode
from io import BytesIO
import base64
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

app = Flask(__name__)


app.secret_key = secrets.token_urlsafe(32)

# Sample database (dictionary) for testing
admin_setup_data = {
    "username": "admin",
    "password": generate_password_hash("12345678"),
    "two_fa_enabled": False,
    "two_fa_secret": None
}





LOGIN_TEMPLATE = '''<!DOCTYPE html><html><head><title>Login - 2FA Demo</title><style>body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }.form-group { margin-bottom: 15px; }label { display: block; margin-bottom: 5px; }input { width: 100%; padding: 8px; box-sizing: border-box; }button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }button:hover { background: #0056b3; }.error { color: red; margin-top: 10px; }.success { color: green; margin-top: 10px; }</style></head><body><h2>Login</h2><form method="POST"><div class="form-group"><label>Username:</label><input type="text" name="username" required></div><div class="form-group"><label>Password:</label><input type="password" name="password" required></div><button type="submit">Login</button></form>{% with messages = get_flashed_messages() %}{% if messages %}{% for message in messages %}<div class="error">{{ message }}</div>{% endfor %}{% endif %}{% endwith %}</body></html>'''

VERIFY_2FA_TEMPLATE = '''<!DOCTYPE html><html><head><title>2FA Verification</title><style>body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }.form-group { margin-bottom: 15px; }label { display: block; margin-bottom: 5px; }input { width: 100%; padding: 8px; box-sizing: border-box; }button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }button:hover { background: #0056b3; }.error { color: red; margin-top: 10px; }</style></head><body><h2>Enter 2FA Code</h2><p>Please enter the 6-digit code from your Google Authenticator app:</p><form method="POST"><div class="form-group"><label>2FA Code:</label><input type="text" name="token" maxlength="6" required></div><button type="submit">Verify</button></form>{% with messages = get_flashed_messages() %}{% if messages %}{% for message in messages %}<div class="error">{{ message }}</div>{% endfor %}{% endif %}{% endwith %}</body></html>'''

DASHBOARD_TEMPLATE = '''<!DOCTYPE html><html><head><title>Dashboard - 2FA Demo</title><style>body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }.user-info { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }.form-group { margin-bottom: 15px; }button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-right: 10px; }button:hover { background: #0056b3; }.danger { background: #dc3545; }.danger:hover { background: #c82333; }.success { background: #28a745; }.success:hover { background: #218838; }.qr-code { text-align: center; margin: 20px 0; }.secret-key { background: #f8f9fa; padding: 10px; font-family: monospace; margin: 10px 0; }</style></head><body><h2>Dashboard</h2><div class="user-info"><h3>User Information</h3><p><strong>Username:</strong> {{ username }}</p><p><strong>2FA Status:</strong> {% if two_fa_enabled %}<span style="color: green;">✓ Enabled</span>{% else %}<span style="color: red;">✗ Disabled</span>{% endif %}</p></div><h3>Two-Factor Authentication</h3>{% if not two_fa_enabled %}<p>Secure your account by enabling 2FA with Google Authenticator:</p><form method="POST" action="{{ url_for('setup_2fa') }}"><button type="submit" class="success">Enable 2FA</button></form>{% else %}<p>2FA is currently enabled for your account.</p><form method="POST" action="{{ url_for('disable_2fa') }}"><button type="submit" class="danger">Disable 2FA</button></form>{% endif %}<br><br><a href="{{ url_for('logout') }}"><button type="button">Logout</button></a></body></html>'''

SETUP_2FA_TEMPLATE = '''<!DOCTYPE html><html><head><title>Setup 2FA</title><style>body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }.qr-code { text-align: center; margin: 20px 0; }.secret-key { background: #f8f9fa; padding: 10px; font-family: monospace; margin: 10px 0; word-break: break-all; }.form-group { margin-bottom: 15px; }label { display: block; margin-bottom: 5px; }input { width: 100%; padding: 8px; box-sizing: border-box; }button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-right: 10px; }button:hover { background: #0056b3; }.cancel { background: #6c757d; }.cancel:hover { background: #5a6268; }.error { color: red; margin-top: 10px; }.instructions { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }</style></head><body><h2>Setup Two-Factor Authentication</h2><div class="instructions"><h3>Instructions:</h3><ol><li>Install Google Authenticator on your phone</li><li>Scan the QR code below with the app</li><li>Enter the 6-digit code from the app to complete setup</li></ol></div><div class="qr-code"><h3>Scan this QR Code:</h3><img src="data:image/png;base64,{{ qr_code }}" alt="QR Code"></div><div><h3>Or enter this secret key manually:</h3><div class="secret-key">{{ secret_key }}</div></div><form method="POST"><div class="form-group"><label>Enter verification code from Google Authenticator:</label><input type="text" name="token" maxlength="6" required></div><button type="submit">Complete Setup</button><a href="{{ url_for('dashboard') }}"><button type="button" class="cancel">Cancel</button></a></form>{% with messages = get_flashed_messages() %}{% if messages %}{% for message in messages %}<div class="error">{{ message }}</div>{% endfor %}{% endif %}{% endwith %}</body></html>'''







@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check credentials
        if (username == admin_setup_data['username'] and 
            check_password_hash(admin_setup_data['password'], password)):
            
            # Check if 2FA is enabled
            if admin_setup_data['two_fa_enabled']:
                session['temp_user'] = username
                return redirect(url_for('verify_2fa'))
            else:
                session['user'] = username
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'temp_user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        token = request.form['token']
        
        # Verify the token
        totp = pyotp.TOTP(admin_setup_data['two_fa_secret'])
        if totp.verify(token):
            session['user'] = session.pop('temp_user')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid 2FA code')
    
    return render_template_string(VERIFY_2FA_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                  username=admin_setup_data['username'],
                                  two_fa_enabled=admin_setup_data['two_fa_enabled'])

@app.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Check if this is the initial setup request (no token) or verification (with token)
        if 'token' not in request.form:
            # This is the initial setup request from dashboard
            # Generate a new secret key
            secret = pyotp.random_base32()
            session['temp_secret'] = secret
            
            # Create the provisioning URI for Google Authenticator
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=admin_setup_data['username'],
                issuer_name="2FA Demo Flask App"
            )
            
            # Generate QR code
            qr = pyqrcode.create(totp_uri)
            stream = BytesIO()
            qr.png(stream, scale=6)
            qr_code = base64.b64encode(stream.getvalue()).decode()
            
            return render_template_string(SETUP_2FA_TEMPLATE,
                                          qr_code=qr_code,
                                          secret_key=secret)
        else:
            # This is the verification request
            token = request.form['token']
            secret = session.get('temp_secret')
            
            if not secret:
                flash('Setup session expired. Please try again.')
                return redirect(url_for('dashboard'))
            
            # Verify the token
            totp = pyotp.TOTP(secret)
            if totp.verify(token):
                # Save the secret and enable 2FA
                admin_setup_data['two_fa_secret'] = secret
                admin_setup_data['two_fa_enabled'] = True
                session.pop('temp_secret', None)
                flash('2FA has been successfully enabled!')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid code. Please try again.')
                
                # Regenerate QR code for retry
                totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                    name=admin_setup_data['username'],
                    issuer_name="2FA Demo Flask App"
                )
                qr = pyqrcode.create(totp_uri)
                stream = BytesIO()
                qr.png(stream, scale=6)
                qr_code = base64.b64encode(stream.getvalue()).decode()
                
                return render_template_string(SETUP_2FA_TEMPLATE,
                                              qr_code=qr_code,
                                              secret_key=secret)
    
    # GET request - redirect to dashboard
    return redirect(url_for('dashboard'))

@app.route('/disable-2fa', methods=['POST'])
def disable_2fa():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    admin_setup_data['two_fa_enabled'] = False
    admin_setup_data['two_fa_secret'] = None
    flash('2FA has been disabled.')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
