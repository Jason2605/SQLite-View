from SQLite_View import app


@app.errorhandler(404)
def error_404(e):
    return str(e)
