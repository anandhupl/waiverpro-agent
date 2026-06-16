import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Note: We are using raw_dom.json based on your latest git commit
DOM_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/raw_dom.json')
VECTOR_CACHE_PATH = os.path.join(os.path.dirname(__file__), '../data/vector_cache.json')

def process_and_embed():
    print("[*] Loading extracted DOM payload...")
    try:
        with open(DOM_FILE_PATH, 'r', encoding='utf-8') as f:
            dom_data = json.load(f)
    except FileNotFoundError:
        print(f"[-] Error: Could not find {DOM_FILE_PATH}")
        return
        
    # Convert the JSON tree back into a formatted string for chunking
    dom_string = json.dumps(dom_data, indent=2)
    
    print("[*] Initializing Recursive Text Splitter...")
    # The separators prioritize splitting at logical JSON boundaries (newlines, brackets)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", "{", "}", " ", ""]
    )
    
    chunks = splitter.split_text(dom_string)
    print(f"[+] Sliced DOM into {len(chunks)} contextual chunks.")
    
    print("[*] Booting up local SentenceTransformer (all-MiniLM-L6-v2)...")
    # This will download the ~80MB model to your machine on the first run
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("[*] Generating mathematical embeddings for each chunk...")
    # Convert the text chunks into mathematical vectors
    embeddings = model.encode(chunks)
    
    print(f"[+] Successfully generated {len(embeddings)} vectors.")
    print(f"[*] Vector dimension size: {len(embeddings[0])}")
    
    print("[*] Saving raw vectors to local cache for verification...")
    output_data = []
    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        output_data.append({
            "chunk_id": i,
            "text": chunk,
            "vector": vector.tolist() # Convert numpy array to list for JSON serialization
        })
        
    os.makedirs(os.path.dirname(VECTOR_CACHE_PATH), exist_ok=True)
    with open(VECTOR_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"[+] Local vector cache secured at: {VECTOR_CACHE_PATH}")

if __name__ == "__main__":
    process_and_embed()