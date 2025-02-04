from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route('/')
def hello_world():
    return 'Hello World'

if __name__ == '__main__':
    app.run(port="5000",debug=True)
