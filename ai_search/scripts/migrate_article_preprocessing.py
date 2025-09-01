"""
Migration script to add preprocessed searchable text to existing articles.

This script processes all existing articles in batches to generate
the preprocessed_searchable_text field for better search quality.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

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
from ai_search.utils.text_preprocessing import generate_preprocessed_content


async def migrate_articles_preprocessing(batch_size: int = 50, dry_run: bool = False, force: bool = False):
    """
    Migrate existing articles to include preprocessed searchable text.
    
    Args:
        batch_size: Number of articles to process in each batch
        dry_run: If True, only shows what would be updated without making changes
        force: If True, reprocesses all articles regardless of existing preprocessed text
    """
    print("🔄 Starting article preprocessing migration...")
    print(f"📋 Batch size: {batch_size}, Dry run: {dry_run}, Force reprocess: {force}")
    
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
        
        # Process articles in batches
        for offset in range(0, total_articles, batch_size):
            print(f"\n📦 Processing batch {offset//batch_size + 1} (articles {offset + 1}-{min(offset + batch_size, total_articles)})")
            
            # Get batch of articles
            articles = await article_repo.get_articles_batch(offset, batch_size)
            
            if not articles:
                print("⚠️ No articles returned for this batch")
                continue
            
            batch_updates = []
            
            for article in articles:
                try:
                    processed_count += 1
                    article_id = article.get('id')
                    
                    # Check if article already has preprocessed text
                    existing_preprocessed = article.get('preprocessed_searchable_text')
                    
                    # Generate new preprocessed text
                    new_preprocessed = generate_preprocessed_content(article)
                    
                    # Only update if different or missing, unless force is True
                    if force or existing_preprocessed != new_preprocessed:
                        update_data = {
                            'id': article_id,
                            'preprocessed_searchable_text': new_preprocessed
                        }
                        batch_updates.append(update_data)
                        
                        if dry_run:
                            action = "force reprocess" if force else "update"
                            print(f"  🔍 Would {action} article {article_id}: {len(new_preprocessed)} chars")
                        else:
                            action = "Force reprocessing" if force else "Updating"
                            print(f"  ✏️ {action} article {article_id}: {len(new_preprocessed)} chars")
                    else:
                        print(f"  ✅ Article {article_id} already has current preprocessed text")
                        
                except Exception as e:
                    error_count += 1
                    print(f"  ❌ Error processing article {article.get('id', 'unknown')}: {e}")
            
            # Perform batch updates
            if batch_updates and not dry_run:
                try:
                    for update_data in batch_updates:
                        await article_repo.update_article(
                            update_data['id'],
                            {'preprocessed_searchable_text': update_data['preprocessed_searchable_text']}
                        )
                        updated_count += 1
                    print(f"  ✅ Updated {len(batch_updates)} articles in this batch")
                except Exception as e:
                    error_count += len(batch_updates)
                    print(f"  ❌ Error updating batch: {e}")
            elif batch_updates and dry_run:
                print(f"  🔍 Would update {len(batch_updates)} articles in this batch")
                updated_count += len(batch_updates)
        
        # Summary
        print(f"\n📈 Migration Summary:")
        print(f"  📊 Total articles processed: {processed_count}")
        print(f"  ✅ Articles updated: {updated_count}")
        print(f"  ❌ Errors encountered: {error_count}")
        print(f"  📋 Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}{' (FORCE REPROCESS)' if force else ''}")
        
        if dry_run:
            print(f"\n💡 To apply changes, run with dry_run=False")
        else:
            print(f"\n🎉 Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


async def verify_preprocessing_migration():
    """
    Verify that the preprocessing migration was successful.
    """
    print("🔍 Verifying preprocessing migration...")
    
    try:
        # Sample a few articles to check
        sample_size = 10
        articles = await article_repo.get_articles_batch(0, sample_size)
        
        missing_preprocessing = 0
        has_preprocessing = 0
        
        for article in articles:
            article_id = article.get('id')
            preprocessed = article.get('preprocessed_searchable_text')
            
            if not preprocessed:
                missing_preprocessing += 1
                print(f"  ❌ Article {article_id} missing preprocessed text")
            else:
                has_preprocessing += 1
                print(f"  ✅ Article {article_id} has preprocessed text ({len(preprocessed)} chars)")
        
        print(f"\n📊 Verification Results:")
        print(f"  ✅ Articles with preprocessing: {has_preprocessing}")
        print(f"  ❌ Articles missing preprocessing: {missing_preprocessing}")
        
        if missing_preprocessing == 0:
            print(f"🎉 All sampled articles have preprocessed text!")
        else:
            print(f"⚠️ {missing_preprocessing} articles still need preprocessing")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate articles to include preprocessed searchable text")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    parser.add_argument("--force", action="store_true", help="Force reprocess all articles regardless of existing preprocessed text")
    parser.add_argument("--verify", action="store_true", help="Verify migration results")
    
    args = parser.parse_args()
    
    if args.verify:
        asyncio.run(verify_preprocessing_migration())
    else:
        asyncio.run(migrate_articles_preprocessing(args.batch_size, args.dry_run, args.force))
