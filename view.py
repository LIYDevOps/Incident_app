from db_config import SessionLocal, User

db = SessionLocal()
users = db.query(User).all()

for u in users:
    print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, Role: {u.role}, Password: {u.password}")

db.close()
