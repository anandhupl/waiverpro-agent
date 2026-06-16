import os
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("[-] Missing Supabase environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load the local mathematical engine
print("[*] Booting up local SentenceTransformer...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def query_database(query_text):
    print(f"\n[*] Target Query: '{query_text}'")
    print("[*] Embedding query...")
    # Convert the text into a 384-dimension vector
    query_vector = model.encode(query_text).tolist()

    print("[*] Searching Supabase for semantic matches...")
    # Call the SQL function we just created
    response = supabase.rpc(
        "match_dom_elements",
        {
            "query_embedding": query_vector,
            "match_threshold": 0.2, # Minimum similarity score
            "match_count": 3        # Return top 3 results
        }
    ).execute()

    results = response.data
    if not results:
        print("[-] No matching chunks found. Try lowering the threshold.")
        return

    print(f"[+] Found {len(results)} matches:\n")
    for idx, match in enumerate(results):
        print(f"--- Match {idx+1} (Score: {match['similarity']:.2f}) ---")
        # Print the first 250 characters of the matched DOM chunk
        print(match['content'][:250] + "...\n")

if __name__ == "__main__":
    # Let's test it against the rule trap we identified earlier
    test_query = "What is the text label of the new application or waiver request button in the sidebar?"
    query_database(test_query)