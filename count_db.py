import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import DatabaseManager

def main():
    tables = DatabaseManager.execute_query('SHOW TABLES')
    for t in tables:
        table_name = list(t.values())[0]
        count = DatabaseManager.execute_query(f"SELECT COUNT(*) as c FROM {table_name}")[0]['c']
        print(f"{table_name}: {count}")

if __name__ == '__main__':
    main()
