from database.db_manager import DatabaseManager

def run():
    print("Connecting to DB...")
    with open('database/migration_roles.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        
    queries = sql.split(';')
    for q in queries:
        q = q.strip()
        if q:
            print(f"Executing: {q[:50]}...")
            try:
                DatabaseManager.execute_query(q, fetch=False)
            except Exception as e:
                print(f"Error executing query: {e}")
                
    print("Migration finished successfully.")

if __name__ == '__main__':
    run()
