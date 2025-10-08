#!/usr/bin/env python3
"""
Скрипт проверки готовности к деплою
"""

import os
import sys
import importlib

def check_requirements():
    """Проверка установленных зависимостей"""
    requirements = [
        'flask',
        'flask_socketio',
        'flask_sqlalchemy',
        'eventlet',
        'cryptography',
        'gunicorn',
        'psycopg2'
    ]
    
    missing = []
    for req in requirements:
        try:
            importlib.import_module(req.replace('_', ''))
            print(f"✅ {req}")
        except ImportError:
            missing.append(req)
            print(f"❌ {req}")
    
    return missing

def check_files():
    """Проверка наличия необходимых файлов"""
    required_files = [
        'app.py',
        'config.py',
        'requirements.txt',
        'Procfile',
        'render.yaml',
        'runtime.txt',
        '.gitignore',
        'extensions.py',
        'models/__init__.py',
        'models/user.py',
        'models/message.py',
        'routes/__init__.py',
        'routes/auth.py',
        'routes/chat.py',
        'routes/upload.py',
        'routes/groups.py',
        'utils/__init__.py',
        'utils/helpers.py',
        'utils/crypto.py',
        'utils/validators.py',
        'static/js/encryption.js',
        'static/js/app.js',
        'static/css/style.css',
        'templates/base.html',
        'templates/index.html',
        'templates/login.html',
        'templates/group.html'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            missing.append(file)
            print(f"❌ {file}")
    
    return missing

def main():
    print("🔍 Проверка готовности к деплою...\n")
    
    print("1. Проверка зависимостей:")
    missing_reqs = check_requirements()
    
    print("\n2. Проверка файлов:")
    missing_files = check_files()
    
    print("\n3. Результат:")
    if not missing_reqs and not missing_files:
        print("🎉 Всё готово к деплою!")
        print("\nСледующие шаги:")
        print("1. git add .")
        print("2. git commit -m 'Ready for deployment'")
        print("3. git push")
        print("4. Деплой на Render.com")
    else:
        if missing_reqs:
            print(f"❌ Отсутствуют зависимости: {', '.join(missing_reqs)}")
            print("   Установите: pip install " + " ".join(missing_reqs))
        if missing_files:
            print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        sys.exit(1)

if __name__ == "__main__":
    main()