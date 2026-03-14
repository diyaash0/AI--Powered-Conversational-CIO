"""Simple test script to connect to Supabase Postgres and query the
`applications` table using a raw SQL query.

Usage:
  - Fill in the password in `backend/.env` or set `DIRECT_URL`/`DATABASE_URL` in env.
  - Install dependencies: `pip install -r backend/requirements.txt`.
  - Run: `python backend/test_supabase.py`
"""
import os
import json
import sys
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras


def main():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)

    db_url = os.getenv('DIRECT_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        print('No database URL found. Set DIRECT_URL or DATABASE_URL in backend/.env')
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(dsn=db_url, cursor_factory=psycopg2.extras.RealDictCursor)
        with conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM applications LIMIT 100;')
                rows = cur.fetchall()
                print(json.dumps(rows, default=str, indent=2))
    except Exception as e:
        print('Error connecting or querying database:')
        print(str(e))
        sys.exit(2)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
