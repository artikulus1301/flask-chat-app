import eventlet
eventlet.monkey_patch()

from app import create_app
from extensions import socketio

if __name__ == '__main__':
    try:
        app = create_app()
        print('Starting app via debug_start...')
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('ERROR:', e)