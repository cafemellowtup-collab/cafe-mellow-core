import json
import os

def generate_starter():
    print("🚀 GENERATING SESSION STARTER FOR GEMINI...")
    
    # Load DNA
    with open('TITAN_DNA.json', 'r') as f:
        dna = json.load(f)
    
    # Load README
    with open('SYSTEM_README.md', 'r') as f:
        readme = f.read()
        
    starter = f"""
I am working on Project Titan (Cafe Mellow ERP). 
CONTEXT:
{readme}

CURRENT DNA:
{json.dumps(dna, indent=2)}

Please confirm you understand this architecture. We are currently working on implementing more 'Pillars'.
    """
    
    with open('SESSION_STARTER.txt', 'w') as f:
        f.write(starter)
    print("✅ SESSION_STARTER.txt is ready. Paste its content to your new Gemini window.")

if __name__ == "__main__":
    generate_starter()