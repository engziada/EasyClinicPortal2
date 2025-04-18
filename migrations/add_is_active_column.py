"""
Migration script to add is_active column to users table.
"""
import sqlite3
import os

def run_migration():
    """Add is_active column to users table."""
    # Get the database path
    db_path = 'app.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'is_active' not in column_names:
            # Add the is_active column with default value of 1 (True)
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added is_active column to users table.")
        else:
            print("Column is_active already exists in users table.")
    
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
