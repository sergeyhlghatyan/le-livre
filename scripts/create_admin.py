#!/usr/bin/env python3
"""Create initial admin user for Le Livre."""
import sys
import getpass
import psycopg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin():
    """Create admin user interactively."""
    print("=== Le Livre Admin User Creation ===\n")

    # Get email
    email = input("Admin email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        sys.exit(1)

    # Get password
    password = getpass.getpass("Admin password: ")
    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)

    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Error: Passwords don't match!")
        sys.exit(1)

    # Hash password
    print("\nHashing password...")
    hashed = pwd_context.hash(password)

    # Database connection string
    conn_string = "host=localhost port=5432 dbname=lelivre_gold user=lelivre password=lelivre123"

    try:
        print("Connecting to database...")
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Check if user already exists
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    print(f"Error: User with email '{email}' already exists!")
                    sys.exit(1)

                # Create admin user
                print("Creating admin user...")
                cur.execute(
                    """
                    INSERT INTO users (email, hashed_password, is_active, is_superuser)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (email, hashed, True, True)
                )
                user_id = cur.fetchone()[0]
                conn.commit()

                print(f"\n✓ Admin user created successfully!")
                print(f"  User ID: {user_id}")
                print(f"  Email: {email}")
                print(f"  Superuser: Yes")
                print(f"\nYou can now login at http://localhost:5174/login")

    except psycopg.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin()
