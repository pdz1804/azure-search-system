#!/usr/bin/env python3
"""
Script to list available Azure OpenAI deployments.
This helps identify the correct deployment names to use in configuration.
"""

import sys
from openai import AzureOpenAI
from config.settings import SETTINGS

def list_deployments():
    """List all available deployments in the Azure OpenAI resource."""
    print("🔍 Listing Azure OpenAI Deployments")
    print("=" * 50)
    
    try:
        # Check if Azure OpenAI is configured
        if not SETTINGS.azure_openai_endpoint or not SETTINGS.azure_openai_key:
            print("❌ Azure OpenAI not configured")
            return False
        
        print(f"📋 Resource: {SETTINGS.azure_openai_endpoint}")
        print(f"🔑 API Key: {'✓ Set' if SETTINGS.azure_openai_key else '✗ Not Set'}")
        print("\n" + "=" * 50)
        
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=SETTINGS.azure_openai_key,
            api_version="2024-12-01-preview",
            azure_endpoint=SETTINGS.azure_openai_endpoint
        )
        
        # List deployments using the management API
        print("📊 Available Deployments:")
        print("   Note: This requires the Management API, which may not be accessible.")
        print("   If this fails, check Azure Portal > Azure OpenAI > Model deployments")
        
        # Try to get deployments (this might not work with data plane API key)
        try:
            # This is a workaround - try to test known model types
            test_models = [
                "gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-35-turbo", 
                "text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"
            ]
            
            print("\n🧪 Testing Common Deployment Names:")
            working_deployments = []
            
            for model in test_models:
                try:
                    print(f"   Testing: {model} ... ", end="", flush=True)
                    
                    # Test if it's a chat model
                    if "gpt" in model:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": "test"}],
                            max_tokens=1
                        )
                        print("✅ (Chat Model)")
                        working_deployments.append((model, "chat"))
                    else:
                        # Test if it's an embedding model
                        response = client.embeddings.create(
                            model=model,
                            input="test"
                        )
                        print("✅ (Embedding Model)")  
                        working_deployments.append((model, "embedding"))
                        
                except Exception as e:
                    if "DeploymentNotFound" in str(e):
                        print("❌ (Not Found)")
                    elif "OperationNotSupported" in str(e):
                        print("❌ (Wrong Model Type)")
                    else:
                        print(f"❌ ({type(e).__name__})")
            
            print(f"\n✅ Working Deployments Found:")
            if working_deployments:
                for deployment, model_type in working_deployments:
                    print(f"   📌 {deployment} ({model_type})")
            else:
                print("   ❌ No working deployments found")
                
            return len(working_deployments) > 0
            
        except Exception as e:
            print(f"❌ Failed to list deployments: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main function."""
    success = list_deployments()
    
    print("\n" + "=" * 50)
    print("💡 Next Steps:")
    print("1. Check Azure Portal > Azure OpenAI > Model deployments")
    print("2. Create a deployment with text-embedding-3-small model if missing")
    print("3. Update AZURE_OPENAI_DEPLOYMENT in .env with the correct deployment name")
    print("4. For embeddings, you may need a separate deployment name")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
