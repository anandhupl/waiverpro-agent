import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("[-] Missing Supabase environment variables. Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

VECTOR_CACHE_PATH = os.path.join(os.path.dirname(__file__), '../data/vector_cache.json')


def inject_data():
    print("[*] Loading local vector cache...")
    try:
        with open(VECTOR_CACHE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[-] Error: Could not find {VECTOR_CACHE_PATH}")
        return

    print(f"[*] Preparing to inject {len(data)} chunks into Supabase...")
    
    # Map our JSON cache to the exact column names in your new SQL table
    rows_to_insert = []
    for item in data:
        rows_to_insert.append({
            "chunk_index": item["chunk_id"],
            "content": item["text"],
            "embedding": item["vector"]
        })

    print("[*] Firing payload to remote database...")
    # Bulk insert the entire array at once
    response = supabase.table("waiverpro_dom_elements").insert(rows_to_insert).execute()
    
    print("[+] Injection complete! Data is now live in Supabase.")

if __name__ == "__main__":
    inject_data()