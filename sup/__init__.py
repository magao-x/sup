import os.path
import sys
import eventlet
from eventlet import greenthread
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, send, emit
from pathlib import Path

static_folder_name = "static"
app = Flask(__name__, static_folder=static_folder_name)
static_path = Path(__file__).parent / static_folder_name
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/api/properties')
def api_properties():
    return jsonify({
        'maths_y.enable_active.value': 'On',
        'maths_y.val.value': '2',
        'maths_y.maths.abs': '2',
        'maths_y.maths.prod': '24',
        'maths_y.maths.sqr': '4',
        'maths_y.maths.sqrt': '1.4142136',
        'maths_y.maths.value': '2',
        'maths_y.state.current': '1',
        'maths_x.enable_active.value': 'On',
        'maths_x.val.value': '12',
        'maths_x.maths.abs': '12',
        'maths_x.maths.prod': '24',
        'maths_x.maths.sqr': '144',
        'maths_x.maths.sqrt': '3.4641016',
        'maths_x.maths.value': '12',
        'maths_x.state.current': '1',
        'maths_x.enable_active.value': 'On',
        'maths_x.val.value': '12',
        'maths_y.enable_active.value': 'On',
        'maths_y.val.value': '2',
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    real_path = (static_path / path).resolve()
    if static_path in real_path.parents:  # prevent traversal vulnerability
        if real_path.exists():
            return app.send_static_file(path)

    return app.send_static_file("index.html")

@socketio.on('connect')
def handle_connect():
    emit('bytes', b'abcdef')

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

ticks = 0

def background_thread():
    global ticks
    while True:
        socketio.emit('tick', b'rawbytes')
        ticks += 1
        greenthread.sleep(1)

def main(*args, **kwargs):
    greenthread.spawn(background_thread)
    socketio.run(app, *args, **kwargs)

def console_entrypoint():
    debug = '--debug' in sys.argv
    sys.exit(main(debug=debug))

if __name__ == '__main__':
    console_entrypoint()
