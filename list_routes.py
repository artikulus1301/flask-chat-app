from app import create_app

app = create_app()
with app.app_context():
    print('Registered routes:')
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f'{rule.rule:30s} -> {rule.endpoint:30s} [{methods}]')
