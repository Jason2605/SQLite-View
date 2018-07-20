from SQLite_View import app
from flask import render_template, request, make_response
import json


@app.errorhandler(405)
def error_405(e):
    if request.method == "GET":
        print(str(e))
        return render_template("errors.html", error="405", error_msg=str(e))
    resp = make_response(json.dumps({"status": 405, "error": str(e)}))
    resp.headers["Allow"] = "HEAD, GET, OPTIONS"
    resp.headers["Content-Type"] = "application/json"
    return resp


@app.errorhandler(404)
def error_404(e):
    return render_template("errors.html", error="404", error_msg=str(e))


@app.errorhandler(500)
def error_500(e):
    return render_template("errors.html", error="500", error_msg=str(e))
