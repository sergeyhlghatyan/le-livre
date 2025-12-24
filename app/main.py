#!/usr/bin/env python3
"""
Flask web application for viewing and comparing USC sections.

Reads data from ../data/sections/ JSON files.
No static file generation needed - everything is dynamic!
"""

import time
from flask import Flask, render_template, request
from routes import sections, comparison

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-in-production'

# Register blueprints
app.register_blueprint(sections.bp)
app.register_blueprint(comparison.bp)


# Request logging middleware
@app.before_request
def before_request():
    """Record request start time."""
    request.start_time = time.time()


@app.after_request
def after_request(response):
    """Log request completion with timing."""
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        print(f"[{request.method}] {request.path} - {elapsed:.2f}s - {response.status_code}")
    return response


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html', error=error), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("USC Section Viewer - Flask Web App")
    print("="*60)
    print("\nStarting server at http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, port=5001, host='0.0.0.0')
