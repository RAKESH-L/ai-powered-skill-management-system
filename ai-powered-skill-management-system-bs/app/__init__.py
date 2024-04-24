from flask import Flask

def create_app():
    app = Flask(__name__)

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register the controllers blueprint
    from .controller import controllers_bp
    app.register_blueprint(controllers_bp)


    return app
