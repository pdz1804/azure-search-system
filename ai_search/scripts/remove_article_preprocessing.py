"""
Reverse migration script to remove preprocessed_searchable_text field from existing articles.

This script processes all existing articles in batches to remove
the preprocessed_searchable_text field and restore the original article structure.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
import time

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
backend_path = os.path.join(project_root, 'backend')
ai_search_path = os.path.join(project_root, 'ai_search')

# Ensure the project root is on sys.path so top-level packages like
# 'backend' and 'ai_search' can be imported as packages. Appending the
# package directory itself (e.g. backend_path) prevents Python from
# locating the package name.
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.repositories import article_repo
from backend.database.cosmos import close_cosmos


async def remove_articles_preprocessing(batch_size: int = 50, dry_run: bool = False, retry_count: int = 3):
    """
    Remove preprocessed_searchable_text field from existing articles.
    
    Args:
        batch_size: Number of articles to process in each batch
        dry_run: If True, only shows what would be updated without making changes
        retry_count: Number of retries for failed operations
    """
    print("🔄 Starting article preprocessing field removal...")
    print(f"📋 Batch size: {batch_size}, Dry run: {dry_run}, Retry count: {retry_count}")
    
    try:
        # Get total count of articles
        total_articles = await article_repo.count_articles()
        print(f"📊 Total articles to process: {total_articles}")
        
        if total_articles == 0:
            print("✅ No articles found to process")
            return
        
        processed_count = 0
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        # Process articles in batches
        for offset in range(0, total_articles, batch_size):
            print(f"\n📦 Processing batch {offset//batch_size + 1} (articles {offset + 1}-{min(offset + batch_size, total_articles)})")
            
            # Retry logic for network issues
            batch_articles = None
            for attempt in range(retry_count):
                try:
                    # Get batch of articles
                    batch_articles = await article_repo.get_articles_batch(offset, batch_size)
                    break
                except Exception as e:
                    print(f"  ⚠️ Attempt {attempt + 1} failed to get batch: {e}")
                    if attempt < retry_count - 1:
                        print(f"  🔄 Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                    else:
                        print(f"  ❌ Failed to get batch after {retry_count} attempts")
                        batch_articles = []
            
            if not batch_articles:
                print("⚠️ No articles returned for this batch")
                continue
            
            batch_updates = []
            
            for article in batch_articles:
                try:
                    processed_count += 1
                    article_id = article.get('id')
                    
                    # Check if article has preprocessed_searchable_text field
                    has_preprocessed = 'preprocessed_searchable_text' in article
                    
                    if has_preprocessed:
                        if dry_run:
                            print(f"  🔍 Would remove preprocessed_searchable_text from article {article_id}")
                            updated_count += 1
                        else:
                            # Remove the field with retry logic
                            success = False
                            for attempt in range(retry_count):
                                try:
                                    success = await article_repo.remove_field_from_article(article_id, 'preprocessed_searchable_text')
                                    if success:
                                        updated_count += 1
                                        print(f"  ✅ Removed preprocessed_searchable_text from article {article_id}")
                                        break
                                except Exception as e:
                                    print(f"  ⚠️ Attempt {attempt + 1} failed for article {article_id}: {e}")
                                    if attempt < retry_count - 1:
                                        print(f"  🔄 Retrying in 1 second...")
                                        await asyncio.sleep(1)
                            
                            if not success:
                                error_count += 1
                                print(f"  ❌ Failed to update article {article_id} after {retry_count} attempts")
                    else:
                        skipped_count += 1
                        print(f"  ⏭️ Article {article_id} doesn't have preprocessed_searchable_text field")
                        
                except Exception as e:
                    error_count += 1
                    print(f"  ❌ Error processing article {article.get('id', 'unknown')}: {e}")
            
            # Add small delay between batches to avoid overwhelming the database
            if offset + batch_size < total_articles:
                await asyncio.sleep(0.5)
        
        # Summary
        print(f"\n📈 Removal Summary:")
        print(f"  📊 Total articles processed: {processed_count}")
        print(f"  ✅ Articles updated: {updated_count}")
        print(f"  ⏭️ Articles skipped (no field): {skipped_count}")
        print(f"  ❌ Errors encountered: {error_count}")
        print(f"  📋 Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
        
        if dry_run:
            print(f"\n💡 To apply changes, run with dry_run=False")
        else:
            print(f"\n🎉 Field removal completed successfully!")
            
    except Exception as e:
        print(f"❌ Field removal failed: {e}")
        raise
    finally:
        # Properly close the Cosmos DB connection to avoid warnings
        try:
            await close_cosmos()
        except Exception as e:
            print(f"⚠️ Error closing Cosmos connection: {e}")


async def verify_preprocessing_removal():
    """
    Verify that the preprocessing field removal was successful.
    """
    print("🔍 Verifying preprocessing field removal...")
    
    try:
        # Sample a few articles to check
        sample_size = 10
        articles = await article_repo.get_articles_batch(0, sample_size)
        
        still_has_preprocessing = 0
        field_removed = 0
        
        for article in articles:
            article_id = article.get('id')
            has_preprocessed = 'preprocessed_searchable_text' in article
            
            if has_preprocessed:
                still_has_preprocessing += 1
                print(f"  ⚠️ Article {article_id} still has preprocessed_searchable_text field")
            else:
                field_removed += 1
                print(f"  ✅ Article {article_id} preprocessed_searchable_text field removed")
        
        print(f"\n📊 Verification Results:")
        print(f"  ✅ Articles with field removed: {field_removed}")
        print(f"  ⚠️ Articles still with field: {still_has_preprocessing}")
        
        if still_has_preprocessing == 0:
            print(f"🎉 All sampled articles have preprocessed_searchable_text field removed!")
        else:
            print(f"⚠️ {still_has_preprocessing} articles still have the field")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise
    finally:
        # Properly close the Cosmos DB connection
        try:
            await close_cosmos()
        except Exception as e:
            print(f"⚠️ Error closing Cosmos connection: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove preprocessed_searchable_text field from articles")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size for processing (default: 25, reduced for stability)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--verify", action="store_true", help="Verify removal results")
    parser.add_argument("--retry-count", type=int, default=3, help="Number of retries for failed operations")
    
    args = parser.parse_args()
    
    if args.verify:
        asyncio.run(verify_preprocessing_removal())
    else:
        asyncio.run(remove_articles_preprocessing(args.batch_size, args.dry_run, args.retry_count))
