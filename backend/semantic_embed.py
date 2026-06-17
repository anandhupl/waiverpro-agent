import os
import json
from sentence_transformers import SentenceTransformer

# Pointing to the NEW enriched DOM file
DOM_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/dom/dashboard_raw.json')
VECTOR_CACHE_PATH = os.path.join(os.path.dirname(__file__), '../data/vector_cache.json')

def flatten_dom(node, current_path="Root", elements=None):
    if elements is None:
        elements = []
        
    if not isinstance(node, dict):
        return elements

    tag = node.get("tag", "unknown")
    text = node.get("text", "").strip()
    attributes = node.get("attributes", {})
    bbox = node.get("boundingBox", {})
    
    # We only care about nodes that have visible text or are interactive
    if text or tag in ["button", "input", "a", "select"]:
        attr_str = ", ".join([f"{k}='{v}'" for k, v in attributes.items()])
        bbox_str = f"[x: {bbox.get('x')}, y: {bbox.get('y')}, width: {bbox.get('width')}, height: {bbox.get('height')}]" if bbox else "Unknown"
        
        # Constructing the ultimate semantic sentence for the AI
        desc = f"UI Element: <{tag}>. Location hierarchy: {current_path}. Screen Coordinates: {bbox_str}. "
        if text: 
            desc += f"Visible Text Content: '{text}'. "
        if attr_str: 
            desc += f"HTML Attributes: {attr_str}. "
            
        elements.append(desc.strip())

    # Traverse children recursively
    children = node.get("children", [])
    for child in children:
        flatten_dom(child, f"{current_path} > {tag}", elements)
        
    return elements

def process_and_embed():
    print("[*] Loading enriched DOM payload...")
    try:
        with open(DOM_FILE_PATH, 'r', encoding='utf-8') as f:
            dom_data = json.load(f)
    except FileNotFoundError:
        print(f"[-] Error: Could not find {DOM_FILE_PATH}. Did you run the Playwright script first?")
        return
        
    print("[*] Flattening JSON into spatial-semantic strings...")
    semantic_chunks = flatten_dom(dom_data)
    
    # Remove duplicates
    semantic_chunks = list(dict.fromkeys(semantic_chunks))
    print(f"[+] Extracted {len(semantic_chunks)} meaningful, spatially-aware UI components.")
    
    print("[*] Booting up local SentenceTransformer (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("[*] Generating mathematical embeddings for semantic chunks...")
    embeddings = model.encode(semantic_chunks)
    
    print("[*] Saving spatial-semantic vectors to local cache...")
    output_data = []
    for i, (chunk, vector) in enumerate(zip(semantic_chunks, embeddings)):
        output_data.append({
            "chunk_id": i,
            "text": chunk,
            "vector": vector.tolist()
        })
        
    os.makedirs(os.path.dirname(VECTOR_CACHE_PATH), exist_ok=True)
    with open(VECTOR_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"[+] Semantic vector cache secured at: {VECTOR_CACHE_PATH}")

if __name__ == "__main__":
    process_and_embed()