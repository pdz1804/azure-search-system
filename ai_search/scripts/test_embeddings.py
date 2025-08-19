"""
Test script to verify Azure OpenAI embedding functionality.
"""

from app.services.embeddings import encode
from config.settings import SETTINGS

def main():
    print("🧪 Testing Azure OpenAI embedding generation")
    print(f"🔧 Using Azure OpenAI endpoint: {SETTINGS.azure_openai_endpoint}")
    print(f"🔧 Using Azure OpenAI model name: {SETTINGS.azure_openai_model_name}")
    
    test_text = "This is a test of the Azure OpenAI embedding functionality."
    
    print(f"📝 Test text: '{test_text}'")
    print("🔄 Generating embedding...")
    
    try:
        embedding = encode(test_text)
        print(f"✅ Successfully generated embedding with dimension: {len(embedding)}")
        print(f"📊 First 5 values: {embedding[:5]}")
        return True
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False

if __name__ == "__main__":
    main()
