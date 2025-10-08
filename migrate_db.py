import os
import sqlite3
from app import create_app
from extensions import db

app = create_app()

def migrate_database():
    with app.app_context():
        try:
            # Получаем путь к базе данных
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
            else:
                print("❌ Это не SQLite база данных")
                return
            
            print(f"📁 Работаем с базой: {db_path}")
            
            # Создаем резервную копию
            backup_path = db_path + '.backup'
            if os.path.exists(db_path):
                import shutil
                shutil.copy2(db_path, backup_path)
                print(f"✅ Создана резервная копия: {backup_path}")
            
            # Подключаемся к SQLite для прямого выполнения SQL
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Проверяем существование колонки codeword_hash
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"📊 Существующие колонки в users: {columns}")
            
            if 'codeword_hash' not in columns:
                print("🔄 Добавляем колонку codeword_hash...")
                
                # Создаем временную таблицу с новой структурой
                cursor.execute('''
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid VARCHAR(36) UNIQUE NOT NULL,
                        codeword_hash VARCHAR(64) NOT NULL DEFAULT '',
                        username VARCHAR(50) UNIQUE NOT NULL,
                        created_at DATETIME,
                        last_seen DATETIME,
                        is_online BOOLEAN DEFAULT 0
                    )
                ''')
                
                # Копируем данные из старой таблицы
                if 'codeword' in columns:
                    # Если есть старая колонка codeword - переносим её
                    cursor.execute('''
                        INSERT INTO users_new 
                        (id, uuid, codeword_hash, username, created_at, last_seen, is_online)
                        SELECT 
                            id, 
                            uuid, 
                            codeword as codeword_hash,  -- переносим codeword в codeword_hash
                            username, 
                            created_at, 
                            last_seen, 
                            is_online 
                        FROM users
                    ''')
                else:
                    # Если нет колонки codeword - создаем пустые значения
                    cursor.execute('''
                        INSERT INTO users_new 
                        (id, uuid, codeword_hash, username, created_at, last_seen, is_online)
                        SELECT 
                            id, 
                            uuid, 
                            '' as codeword_hash,  -- пустой хеш
                            username, 
                            created_at, 
                            last_seen, 
                            is_online 
                        FROM users
                    ''')
                
                # Удаляем старую таблицу и переименовываем новую
                cursor.execute('DROP TABLE users')
                cursor.execute('ALTER TABLE users_new RENAME TO users')
                
                print("✅ Миграция таблицы users завершена!")
            else:
                print("✅ Таблица users уже актуальна")
            
            # Проверяем другие таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"📋 Все таблицы в базе: {tables}")
            
            conn.commit()
            conn.close()
            
            print("🎉 Миграция базы данных завершена успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            import traceback
            traceback.print_exc()
            
            # Восстанавливаем из резервной копии при ошибке
            if os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, db_path)
                    print("✅ Восстановлена резервная копия")
                except:
                    print("⚠️ Не удалось восстановить резервную копию")

if __name__ == '__main__':
    migrate_database()