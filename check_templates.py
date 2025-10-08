from app import create_app

app = create_app()
with app.app_context():
    try:
        tmpl = app.jinja_env.get_template('index.html')
        print('index.html parsed OK')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('TEMPLATE ERROR:', e)
