"""
list_routes.py — вспомогательный скрипт для просмотра всех зарегистрированных маршрутов Flask-приложения.
Запуск:
    python list_routes.py
"""

from app import create_app

def list_routes(app):
    print("\n📜 Registered Flask Routes:\n" + "-" * 60)
    routes = sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint))

    for rule in routes:
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        blueprint = rule.endpoint.split('.')[0] if '.' in rule.endpoint else '-'
        print(f"{rule.rule:40s}  ->  {rule.endpoint:30s}  [{methods}]  (Blueprint: {blueprint})")

    print("-" * 60)
    print(f"Total routes: {len(routes)}")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        list_routes(app)
