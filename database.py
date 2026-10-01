import sqlite3

def init_db():
    conn = sqlite3.connect('karak_gate.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول التجار المعتمدين والمعلقين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            phone TEXT,
            location TEXT,
            status TEXT
        )
    ''')
    
    # جدول السائقين المعتمدين والمعلقين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            vehicle TEXT,
            status TEXT
        )
    ''')
    
    # جدول الزبائن
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            address TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()