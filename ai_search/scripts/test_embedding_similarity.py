"""
Test script to compare embedding similarity between different sentence pairs.

This script tests two scenarios:
1. Semantically similar terms: "AI" vs "artificial intelligence"
2. Related but different concepts: "AI" vs long deep learning description

Usage:
    python scripts/test_embedding_similarity.py
"""

import os
import sys
import numpy as np
from typing import List, Tuple
import openai
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SETTINGS

def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a text using Azure OpenAI.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of embedding values
    """
    try:
        # Configure OpenAI client for Azure
        client = openai.AzureOpenAI(
            api_key=SETTINGS.azure_openai_key,
            api_version="2024-02-01",
            azure_endpoint=SETTINGS.azure_openai_endpoint
        )
        
        response = client.embeddings.create(
            input=text,
            model=SETTINGS.azure_openai_model_name
        )
        
        embedding = response.data[0].embedding
        print(f"   📐 Embedding dimension for '{text[:30]}...': {len(embedding)}")
        return embedding
    
    except Exception as e:
        print(f"❌ Error getting embedding for '{text}': {e}")
        return []

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score (0-1, higher = more similar)
    """
    if not embedding1 or not embedding2:
        return 0.0
    
    # Convert to numpy arrays and reshape for sklearn
    emb1 = np.array(embedding1).reshape(1, -1)
    emb2 = np.array(embedding2).reshape(1, -1)
    
    # Calculate cosine similarity
    similarity = cosine_similarity(emb1, emb2)[0][0]
    return similarity

def test_sentence_pairs():
    """Test embedding similarity for different sentence pairs."""
    
    print("🧪 Testing Embedding Similarity")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Case 1: Semantically Similar Terms",
            "sentence1": "Chuong Dep Zai",
            "sentence2": "Multimodal Language Models (VLMs) integrate text, images, and other data types to improve comprehension and generation tasks. By leveraging diverse modalities, they enable richer interactions and insights",
            "expected": "High similarity (synonymous terms)"
        },
        {
            "name": "Case 2: Related but Different Concepts", 
            "sentence1": "Phu the hippo",
            "sentence2": "Multimodal Language Models (VLMs) integrate text, images, and other data types to improve comprehension and generation tasks. By leveraging diverse modalities, they enable richer interactions and insights",
            "expected": "Medium similarity (related domain)"
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 {case['name']}")
        print(f"   Sentence 1: '{case['sentence1']}'")
        print(f"   Sentence 2: '{case['sentence2']}'")
        print(f"   Expected: {case['expected']}")
        
        # Get embeddings
        print("   🔄 Generating embeddings...")
        emb1 = get_embedding(case['sentence1'])
        emb2 = get_embedding(case['sentence2'])
        
        if emb1 and emb2:
            # Calculate similarity
            print(f"   📏 Dimensions: Sentence 1 = {len(emb1)}, Sentence 2 = {len(emb2)}")
            
            similarity = calculate_similarity(emb1, emb2)
            
            # Interpret similarity score
            if similarity >= 0.8:
                interpretation = "Very High"
            elif similarity >= 0.6:
                interpretation = "High"
            elif similarity >= 0.4:
                interpretation = "Medium"
            elif similarity >= 0.2:
                interpretation = "Low"
            else:
                interpretation = "Very Low"
            
            print(f"   ✅ Similarity Score: {similarity:.4f} ({interpretation})")
            
            results.append({
                "case": case['name'],
                "sentence1": case['sentence1'],
                "sentence2": case['sentence2'],
                "similarity": similarity,
                "interpretation": interpretation
            })
        else:
            print(f"   ❌ Failed to get embeddings")
            results.append({
                "case": case['name'],
                "sentence1": case['sentence1'],
                "sentence2": case['sentence2'],
                "similarity": 0.0,
                "interpretation": "Error"
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY RESULTS")
    print("=" * 50)
    
    for result in results:
        print(f"• {result['case']}")
        print(f"  Similarity: {result['similarity']:.4f} ({result['interpretation']})")
        print()
    
    # Analysis
    print("🔍 ANALYSIS")
    print("-" * 30)
    
    if len(results) >= 2:
        case1_sim = results[0]['similarity']
        case2_sim = results[1]['similarity']
        
        print(f"• Case 1 (AI vs artificial intelligence): {case1_sim:.4f}")
        print(f"• Case 2 (AI vs deep learning description): {case2_sim:.4f}")
        
        if case1_sim > case2_sim:
            print("✅ Expected: Case 1 shows higher similarity (synonymous terms)")
        else:
            print("⚠️ Unexpected: Case 2 shows higher similarity")
        
        diff = abs(case1_sim - case2_sim)
        print(f"• Difference: {diff:.4f}")
        
        if diff > 0.1:
            print("📈 Significant difference detected")
        else:
            print("📊 Similar similarity scores")

def main():
    """Main function to run the embedding similarity tests."""
    
    # Check configuration
    if not SETTINGS.azure_openai_key or not SETTINGS.azure_openai_endpoint:
        print("❌ Error: Azure OpenAI configuration missing")
        print("   Please check your .env file for:")
        print("   - AZURE_OPENAI_KEY")
        print("   - AZURE_OPENAI_ENDPOINT")
        print("   - AZURE_OPENAI_MODEL_NAME")
        return
    
    print(f"🔧 Configuration:")
    print(f"   Endpoint: {SETTINGS.azure_openai_endpoint}")
    print(f"   Model: {SETTINGS.azure_openai_model_name}")
    print(f"   Embeddings Enabled: {SETTINGS.enable_embeddings}")
    
    if not SETTINGS.enable_embeddings:
        print("⚠️ Warning: Embeddings are disabled in settings")
        print("   Set ENABLE_EMBEDDINGS=true in .env to enable")
    
    # Run tests
    test_sentence_pairs()

if __name__ == "__main__":
    main()
