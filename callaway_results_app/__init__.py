from flask import Flask

def create_app():
    app = Flask(__name__)

    # ✅ Delayed import to prevent circular imports
    from callaway_results_app.views import callaway_app
    app.register_blueprint(callaway_app)

    return app
