from sqlalchemy import inspect
from app.database import engine

def get_db_schema():
    inspector = inspect(engine)
    schema = []
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append(f"{column['name']} ({column['type']})")
        schema.append(f"Table {table_name}: {', '.join(columns)}")
    return "\n".join(schema)
