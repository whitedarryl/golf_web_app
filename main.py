import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app1_golf_score_calculator')))
from flask import Blueprint
print("DEBUG: ", os.listdir("callaway_results_app"))
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
sys.path.append(os.path.dirname(__file__))
from landing_page.app import app as landing_app
from app1_golf_score_calculator.app import app as app1
from app2_golf_script_runner.app import app as app2
from callaway_results_app import create_app
app3 = create_app()
from app4_five_results.app import app as app4
from app5_historical_data.app import app as app5
from flask import send_from_directory

css_path = os.path.join("static", "css", "scorecard.css")
print("🧪 File exists at static/css/scorecard.css? ", os.path.exists(css_path))

@landing_app.route('/static/<path:filename>')
def static_from_root(filename):
    return send_from_directory('static', filename)

@landing_app.route('/test-css')
def test_css():
    return send_from_directory('static/css', 'scorecard.css')

application = DispatcherMiddleware(landing_app, {
    '/golf_score_calculator': app1,
    '/golf_script_runner': app2,
    '/callaway_results': app3,
    '/five_results': app4,
    '/historical_data': app5,
})

if __name__ == '__main__':
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True)
