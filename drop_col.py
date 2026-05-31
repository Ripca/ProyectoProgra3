from database.db_manager import DatabaseManager

def drop_col():
    try:
        DatabaseManager.execute_query('ALTER TABLE personas DROP FOREIGN KEY fk_personas_tipo', fetch=False)
    except Exception as e:
        print("FK drop error:", e)
        
    try:
        DatabaseManager.execute_query('ALTER TABLE personas DROP COLUMN tipo_persona_id', fetch=False)
        print("Column dropped correctly.")
    except Exception as e:
        print("Column drop error:", e)

if __name__ == '__main__':
    drop_col()
