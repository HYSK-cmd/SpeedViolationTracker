import os
from flask import Flask
from src.web.routes import web_bp

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'assets/videos'
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
    # make sure the upload folder exists so /api/upload doesn't crash on a fresh checkout
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.register_blueprint(web_bp)
    return app

app = create_app()

if __name__ == '__main__':
    # host/port are configurable via env vars (see run.sh); default to local only.
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', '5000'))
    # debug is OFF by default (LAN deployment). Set FLASK_DEBUG=1 only while developing:
    # debug mode auto-reloads + exposes an interactive debugger, which is unsafe to serve.
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    # threaded=True is required: the SSE log stream (/api/logs/stream) holds a
    # connection open indefinitely and would otherwise block every other request.
    app.run(host=host, port=port, debug=debug, threaded=True)
