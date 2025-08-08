# pip install Flask Flask-WTF

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory, flash
import json
import secrets
from flask_wtf import CSRFProtect
app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True

csrf = CSRFProtect(app)







content = {
	"map_data": {
		"map_provider": "openstreet",
		"map_lat": 40.7128,
		"map_lng": -74.0060,
		"google_maps_api_key": ""
	}
}





@app.route('/')
def setup():
	print(content)
	return render_template('setup.html', content=content)

@app.route('/map-page')
def map_page():
	print(content)
	return render_template('map-page.html', content=content)












@app.route('/api/update', methods=['POST'])
def api_update():
    data = request.json
    map_data = data.get('map_data', {})
    print("data from user", data)

    if 'map_lat' in map_data and 'map_lng' in map_data:
        try:
            map_data['map_lat'] = float(map_data['map_lat'])
            map_data['map_lng'] = float(map_data['map_lng'])
        except Exception:
            return jsonify({'error': 'Invalid latitude or longitude.'}), 400

    google_maps_api_key = map_data.pop('google_maps_api_key', None)

    content['map_data'].update(map_data)


    if google_maps_api_key is not None:
        content['map_data']['google_maps_api_key'] = google_maps_api_key

    print("updated content", content) 
    return jsonify({'success': True})





@app.after_request
def no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response









if __name__ == '__main__':
	app.run(debug=True)
