import sys
import os

# Set up python paths
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from app import app
except Exception as e:
    import traceback
    err_str = traceback.format_exc()
    from flask import Flask, Response
    app = Flask(__name__)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return Response(f"<h1>Application Cold Start Error</h1><pre>{err_str}</pre>", status=500, mimetype="text/html")
