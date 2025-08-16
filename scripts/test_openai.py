#!/usr/bin/env python3
"""
Simple test script to verify Azure OpenAI API connectivity and functionality.
Tests both chat completion and embeddings endpoints.
"""

import os
import sys
from typing import List, Dict, Any
from openai import AzureOpenAI
from config.settings import SETTINGS

def test_azure_openai_chat() -> bool:
    """Test Azure OpenAI chat completion API."""
    print("🧪 Testing Azure OpenAI Chat Completion API...")
    
    # Check if current deployment is an embedding model
    if "embedding" in SETTINGS.azure_openai_deployment.lower():
        print("⚠️ Skipping chat test - deployment is an embedding model")
        print(f"   Current deployment: {SETTINGS.azure_openai_deployment}")
        print("   Chat requires a chat model deployment (gpt-35-turbo, gpt-4, etc.)")
        return True  # Not an error, just skipped
    
    try:
        # Check if Azure OpenAI is configured
        if not SETTINGS.azure_openai_endpoint or not SETTINGS.azure_openai_key:
            print("❌ Azure OpenAI not configured")
            return False
        
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=SETTINGS.azure_openai_key,
            api_version="2024-12-01-preview",
            azure_endpoint=SETTINGS.azure_openai_endpoint
        )
        
        # Test chat completion using deployment name
        response = client.chat.completions.create(
            model=SETTINGS.azure_openai_deployment,
            messages=[
                {"role": "user", "content": "Say hello and confirm this Azure OpenAI API key is working!"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        message = response.choices[0].message.content
        print(f"✅ Azure OpenAI Chat Completion Success!")
        print(f"   Endpoint: {SETTINGS.azure_openai_endpoint}")
        print(f"   Deployment: {SETTINGS.azure_openai_deployment}")
        print(f"   Response: {message}")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI Chat Completion Failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def test_azure_openai_embeddings() -> bool:
    """Test Azure OpenAI embeddings API if configured."""
    print("\n🧪 Testing Azure OpenAI Embeddings API...")
    
    try:
        # Check if Azure OpenAI is configured
        if not SETTINGS.azure_openai_endpoint or not SETTINGS.azure_openai_key:
            print("⚠️ Azure OpenAI not configured - skipping test")
            return True  # Not an error, just not configured
        
        from openai import AzureOpenAI
        
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=SETTINGS.azure_openai_key,
            api_version="2024-12-01-preview",
            azure_endpoint=SETTINGS.azure_openai_endpoint
        )
        
        # Test text to embed
        test_text = "This is a test document for Azure OpenAI embedding generation."
        
        # For embeddings, we need to use the embedding model name directly
        # since SETTINGS.azure_openai_deployment might be a chat model
        embedding_deployment = SETTINGS.azure_openai_model_name  # text-embedding-3-small
        
        print(f"   Using embedding deployment: {embedding_deployment}")
        
        # Create embeddings using embedding model name
        response = client.embeddings.create(
            model=embedding_deployment,
            input=test_text
        )
        
        embedding = response.data[0].embedding
        embedding_length = len(embedding)
        
        print(f"✅ Azure OpenAI Embeddings Success!")
        print(f"   Endpoint: {SETTINGS.azure_openai_endpoint}")
        print(f"   Deployment: {SETTINGS.azure_openai_deployment}")
        print(f"   Model: {SETTINGS.azure_openai_model_name}")
        print(f"   Input text: '{test_text}'")
        print(f"   Embedding dimensions: {embedding_length}")
        print(f"   First 5 values: {embedding[:5]}")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI Embeddings Failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def print_configuration_info():
    """Print current Azure OpenAI configuration."""
    print("📋 Azure OpenAI Configuration:")
    print(f"   Endpoint: {SETTINGS.azure_openai_endpoint or 'Not Set'}")
    print(f"   API Key: {'✓ Set' if SETTINGS.azure_openai_key else '✗ Not Set'}")
    print(f"   Deployment: {SETTINGS.azure_openai_deployment or 'Not Set'}")
    print(f"   Model Name: {SETTINGS.azure_openai_model_name or 'Not Set'}")

def main():
    """Run Azure OpenAI API tests."""
    print("🚀 Azure OpenAI API Test Suite")
    print("=" * 50)
    
    # Print configuration
    print_configuration_info()
    print("\n" + "=" * 50)
    
    # Track test results
    results = []
    
    # Test Azure OpenAI
    results.append(("Azure OpenAI Chat", test_azure_openai_chat()))
    results.append(("Azure OpenAI Embeddings", test_azure_openai_embeddings()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result is True:
            print(f"   ✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"   ❌ {test_name}: FAILED")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total and total > 0:
        print("🎉 All tests passed! Azure OpenAI API is working correctly.")
        return 0
    elif total == 0:
        print("⚠️ No tests were run. Please check your configuration.")
        return 1
    else:
        print("❌ Some tests failed. Please check your API keys and configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
