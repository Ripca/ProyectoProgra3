import bcrypt

passwords = ["admin123", "docente123"]
for pwd in passwords:
    hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"{pwd}: {hashed}")
