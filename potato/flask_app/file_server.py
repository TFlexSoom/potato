@app.route("/<path:filename>")
def get_file(filename):
    """Make files available for annotation access from a folder"""
    try:
        return flask.send_from_directory(os.getcwd(), filename)
    except FileNotFoundError:
        flask.abort(404)