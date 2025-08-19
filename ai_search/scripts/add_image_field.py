#!/usr/bin/env python
"""
Add image fields to articles in a JSON dataset.

This utility script adds a random image URL to each article in the blog_seed.json file,
creating an updated version with image fields. The images are sourced from picsum.photos
with fixed seeds for reproducibility.

Usage:
    python add_image_field.py

Input: blog_seed.json in the project root
Output: blog_seed_UPDATED.json in the project root
"""

import json
import os
import random

# Path configuration
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(ROOT, 'blog_seed.json')
OUTPUT = os.path.join(ROOT, 'blog_seed_UPDATED.json')

# Sample image URLs with fixed seeds for reproducibility
images = [
    "https://picsum.photos/seed/2d6a77ae-05c0-4145-9614-614c3df49101/800/400",
    "https://picsum.photos/seed/a4d7c1cb-3429-4640-bd37-24962eb2fa10/800/400",
    "https://picsum.photos/seed/7b02c905-dc41-46f8-8ef2-babfe5af3885/800/400",
    "https://picsum.photos/seed/cceb8fd8-4268-40c5-8739-1c5c6b89762f/800/400",
    "https://picsum.photos/seed/3f9c7de6-8ab8-45b1-ade5-2eb42cfae04b/800/400",
    "https://picsum.photos/seed/c60a1c5d-1c6c-4f33-b179-3ac4cc424589/800/400",
    "https://picsum.photos/seed/48832eb3-af83-480d-93d5-610a8d788278/800/400",
    "https://picsum.photos/seed/4916a11a-8e16-45c2-8e5d-c28bd8025ef2/800/400",
    "https://picsum.photos/seed/9c31fa31-a09a-4f87-bfe3-d2d7f893ca71/800/400",
    "https://picsum.photos/seed/6e96b8ed-63bb-4657-8f60-9ffb4247eaae/800/400",
    "https://picsum.photos/seed/b6f87dee-0c9b-4efc-bff4-dcf7e02daa5a/800/400"
]

# Main execution
def main():
    """Add image field to each article and save the updated data."""
    try:
        # Load the source data
        with open(INPUT, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Add image field to each article
        articles = data.get('Articles', [])
        for article in articles:
            article['image'] = random.choice(images)

        # Save the updated data
        with open(OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f'✅ Success! Added images to {len(articles)} articles.')
        print(f'📄 Output saved to: {OUTPUT}')
    
    except Exception as e:
        print(f'❌ Error: {e}')
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
