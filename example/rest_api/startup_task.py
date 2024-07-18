import sqlite3

def init_db():
    dbfile = "tasks.db"
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    
    # Create the processes table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processes (
        token TEXT PRIMARY KEY,
        status TEXT,
        payload TEXT
    )
    ''')
    
    conn.commit()
    conn.close()