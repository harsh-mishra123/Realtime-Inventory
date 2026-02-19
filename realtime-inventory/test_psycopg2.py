import psycopg2
import select

def listen_to_postgres():
    # PostgreSQL connection
    conn = psycopg2.connect(
        database="inventory_db",
        user="harshmishra",
        host="localhost"
    )
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    
    # Create cursor and listen
    cursor = conn.cursor()
    cursor.execute("LISTEN inventory_channel;")
    print("👂 Listening for notifications with psycopg2...")
    print("Ab doosre terminal mein update karo!\n")
    
    while True:
        # Wait for notification
        select.select([conn], [], [], 5)
        conn.poll()
        
        # Process all notifications
        while conn.notifies:
            notify = conn.notifies.pop(0)
            print("✅ NOTIFICATION RECEIVED!")
            print(f"   Channel: {notify.channel}")
            print(f"   Payload: {notify.payload}")
            print("-" * 50)

if __name__ == "__main__":
    listen_to_postgres()