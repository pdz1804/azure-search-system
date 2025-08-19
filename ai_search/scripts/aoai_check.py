# scripts/aoai_check.py
import os
from openai import AzureOpenAI

from dotenv import load_dotenv
load_dotenv()

# Read from your existing settings/env
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("OPENAI_API_BASE")
KEY = os.getenv("AZURE_OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_MODELNAME")  # preferred: set this to your deployment name

if not ENDPOINT or not KEY:
    raise SystemExit("Missing AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_KEY in environment.")

client = AzureOpenAI(
    api_key=KEY,
    api_version="2024-02-01",  # ok; newer versions like 2024-06-01 or 2024-10-21 also work
    azure_endpoint=ENDPOINT.rstrip("/"),
)

print(f"Endpoint: {ENDPOINT}")
print("Listing deployments (their IDs are the names you must use as model=):")
deployments = list(client.models.list())
for m in deployments:
    print("  -", m.id)

if not DEPLOYMENT:
    if deployments:
        DEPLOYMENT = deployments[0].id
        print(f"\nNo AZURE_OPENAI_MODELNAME set; trying first deployment: {DEPLOYMENT}")
    else:
        raise SystemExit("No deployments found. Create a deployment in the Azure portal first.")

print("\nTesting a sample embedding call...")
resp = client.embeddings.create(
    model=DEPLOYMENT,            # MUST be a deployment name
    input="hello world"
)
vec = resp.data[0].embedding
print(f"Success. Embedding length = {len(vec)}")
