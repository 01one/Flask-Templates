from flask import Flask, render_template, request, jsonify
import requests
from functools import wraps

app = Flask(__name__)

from authkey import site_key, secrect_key
SITE_KEY =site_key
SECRET_KEY = secrect_key
RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

def verify_recaptcha(min_score=0.5):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            token = request.form.get('recaptcha_token')
            
            if not token:
                return jsonify({'error': 'No reCAPTCHA token provided'}), 400
            
            # Verify the token
            response = requests.post(RECAPTCHA_VERIFY_URL, data={
                'secret': SECRET_KEY,
                'response': token
            })
            
            result = response.json()
            print(result)
            
            if result['success'] and result['score'] >= min_score:
                return function(*args, **kwargs)
            else:
                return jsonify({
                    'error': 'reCAPTCHA verification failed',
                    'score': result.get('score', 0)
                }), 400
                
        return wrapper
    return decorator

@app.route('/')
def index():
    return render_template('index.html', site_key=SITE_KEY)

@app.route('/submit', methods=['POST'])
@verify_recaptcha(min_score=0.6)  # Adjust based on your security level
def submit():
    return jsonify({'success': True, 'message': 'Form submitted successfully'})

if __name__ == '__main__':
    app.debug = True
    app.run(port="5000")
