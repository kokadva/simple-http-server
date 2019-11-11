import mimetypes
import os
import re

from flask import Flask, request, Response
from flask_cors import CORS, cross_origin

UPLOAD_DIRECTORY = 'files/'

app = Flask(__name__)
CORS(app)

DEFAULT_RESPONSE_HEADERS = [('Accept-Ranges', 'bytes'), ('Access-Control-Request-Headers', '*'), ("Access-Control-Allow-Headers", '*'), ('Access-Control-Allow-Origin', '*')]


def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def add_default_response_headers(response):
    for key, value in DEFAULT_RESPONSE_HEADERS:
        response.headers.add(key, value)


app.after_request(add_cors_headers)


@app.route("/<path:path>")
@cross_origin()
def get_file(path):
    start, end = get_range()
    return partial_response(path, start, end)


def partial_response(path, start, end=None):
    path = UPLOAD_DIRECTORY + path
    file_size = os.path.getsize(path)

    if end is None:
        end = file_size - start - 1

    end = min(end, file_size - 1)
    length = end - start + 1

    with open(path, 'rb') as fd:
        fd.seek(start)
        data = fd.read(length)
    assert len(data) == length

    response = Response(
        data,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True,
    )
    response.headers.add(
        'Content-Range', 'bytes {0}-{1}/{2}'.format(
            start, end, file_size,
        ), )
    add_default_response_headers(response)

    return response


def get_range():
    range_header = request.headers.get('Range')
    if range_header:
        m = re.match('bytes=(?P<start>\d+)-(?P<end>\d+)?', range_header)
        if m:
            start = m.group('start')
            end = m.group('end')
            start = int(start)
            if end is not None:
                end = int(end)
            return start, end
    return 0, None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 5000), debug=True)
