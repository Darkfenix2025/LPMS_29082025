import crm_database as db

print("Testing database connection...")
try:
    conn = db.connect_db()
    print(f"Connection successful: {conn is not None}")
    if conn:
        conn.close()
        print("Connection closed successfully")
    else:
        print("Connection failed")
except Exception as e:
    print(f"Connection error: {e}")

print("\nTesting get_contactos...")
try:
    contactos = db.get_contactos()
    print(f"Contacts found: {len(contactos)}")
    if contactos:
        print(f"Sample contact: {contactos[0]}")
    else:
        print("No contacts found")
except Exception as e:
    print(f"Error getting contacts: {e}")