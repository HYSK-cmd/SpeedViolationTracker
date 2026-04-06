from flask import Flask
from src.web.routes import web_bp

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'assets/videos'
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
    app.register_blueprint(web_bp)
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
