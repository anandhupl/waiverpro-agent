import os
import json
import glob
from sentence_transformers import SentenceTransformer

DOM_DIR = os.path.join(os.path.dirname(__file__), '../data/dom/')
VECTOR_CACHE_PATH = os.path.join(os.path.dirname(__file__), '../data/vector_cache.json')

def flatten_dom(node, page_name, current_path="Root", elements=None):
    if elements is None:
        elements = []
        
    if not isinstance(node, dict):
        return elements

    tag = node.get("tag", "unknown")
    text = node.get("text", "").strip()
    attributes = node.get("attributes", {})
    bbox = node.get("boundingBox", {})
    
    if text or tag in ["button", "input", "a", "select"]:
        attr_str = ", ".join([f"{k}='{v}'" for k, v in attributes.items()])
        bbox_str = f"[x: {bbox.get('x')}, y: {bbox.get('y')}, width: {bbox.get('width')}, height: {bbox.get('height')}]" if bbox else "Unknown"
        
        # THE FIX: Prepending the page identity to the semantic string
        desc = f"[PAGE: {page_name}] UI Element: <{tag}>. Location hierarchy: {current_path}. Screen Coordinates: {bbox_str}. "
        if text: 
            desc += f"Visible Text Content: '{text}'. "
        if attr_str: 
            desc += f"HTML Attributes: {attr_str}. "
            
        elements.append(desc.strip())

    children = node.get("children", [])
    for child in children:
        flatten_dom(child, page_name, f"{current_path} > {tag}", elements)
        
    return elements

def process_and_embed():
    print("[*] Scanning for enriched DOM payloads...")
    dom_files = glob.glob(os.path.join(DOM_DIR, '*.json'))
    
    if not dom_files:
        print(f"[-] Error: No JSON files found in {DOM_DIR}. Run the scraper first.")
        return
        
    all_semantic_chunks = []
    
    for file_path in dom_files:
        page_name = os.path.basename(file_path).replace('_raw.json', '')
        print(f"[*] Processing {page_name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            dom_data = json.load(f)
            
        chunks = flatten_dom(dom_data, page_name)
        all_semantic_chunks.extend(chunks)
    
    # Remove duplicates
    all_semantic_chunks = list(dict.fromkeys(all_semantic_chunks))
    print(f"[+] Extracted {len(all_semantic_chunks)} spatially-aware UI components across {len(dom_files)} pages.")
    
    print("[*] Booting up local SentenceTransformer (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("[*] Generating mathematical embeddings for semantic chunks...")
    embeddings = model.encode(all_semantic_chunks)
    
    print("[*] Saving spatial-semantic vectors to local cache...")
    output_data = []
    for i, (chunk, vector) in enumerate(zip(all_semantic_chunks, embeddings)):
        output_data.append({
            "chunk_id": i,
            "text": chunk,
            "vector": vector.tolist()
        })
        
    os.makedirs(os.path.dirname(VECTOR_CACHE_PATH), exist_ok=True)
    with open(VECTOR_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"[+] Multi-page vector cache secured at: {VECTOR_CACHE_PATH}")

if __name__ == "__main__":
    process_and_embed()