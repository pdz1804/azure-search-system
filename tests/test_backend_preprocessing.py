"""
Integration tests for backend text preprocessing functionality.

This module tests the integration between backend services and
text preprocessing utilities.
"""

import unittest
import asyncio
import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')
ai_search_path = os.path.join(project_root, 'ai_search')

if backend_path not in sys.path:
    sys.path.append(backend_path)
if ai_search_path not in sys.path:
    sys.path.append(ai_search_path)

from backend.services.text_preprocessing_service import (
    preprocess_article_text,
    should_regenerate_preprocessed_text
)


class TestBackendTextPreprocessing(unittest.TestCase):
    """Test backend text preprocessing service integration."""

    def test_preprocess_article_text(self):
        """Test article text preprocessing service."""
        article_data = {
            "title": "<h1>Test Article</h1>",
            "abstract": "Abstract with https://example.com",
            "content": "Content with test@example.com and special chars@#$!"
        }
        
        result = preprocess_article_text(article_data)
        
        # Should return clean text
        self.assertIn("Test Article", result)
        self.assertNotIn("<h1>", result)
        self.assertNotIn("https://", result)
        self.assertNotIn("@example.com", result)
        self.assertNotIn("@#$", result)

    def test_preprocess_article_text_fallback(self):
        """Test preprocessing fallback behavior."""
        # Test with missing fields
        article_data = {
            "title": "Title Only"
        }
        
        result = preprocess_article_text(article_data)
        self.assertEqual(result, "Title Only")
        
        # Test with empty data
        article_data = {}
        result = preprocess_article_text(article_data)
        self.assertEqual(result, "")

    def test_should_regenerate_preprocessed_text(self):
        """Test preprocessed text regeneration logic."""
        # Case 1: No current preprocessed text
        should_regenerate = should_regenerate_preprocessed_text(
            current_preprocessed="",
            title="New Title",
            abstract="New Abstract",
            content="New Content"
        )
        self.assertTrue(should_regenerate)
        
        # Case 2: Content hasn't changed
        preprocessed = preprocess_article_text({
            "title": "Title",
            "abstract": "Abstract", 
            "content": "Content"
        })
        
        should_regenerate = should_regenerate_preprocessed_text(
            current_preprocessed=preprocessed,
            title="Title",
            abstract="Abstract",
            content="Content"
        )
        self.assertFalse(should_regenerate)
        
        # Case 3: Content has changed
        should_regenerate = should_regenerate_preprocessed_text(
            current_preprocessed=preprocessed,
            title="New Title",  # Changed
            abstract="Abstract",
            content="Content"
        )
        self.assertTrue(should_regenerate)

    def test_preprocessing_consistency(self):
        """Test that preprocessing produces consistent results."""
        article_data = {
            "title": "Consistent Title",
            "abstract": "Consistent abstract with https://example.com",
            "content": "Consistent content with test@example.com"
        }
        
        # Run preprocessing multiple times
        result1 = preprocess_article_text(article_data)
        result2 = preprocess_article_text(article_data)
        result3 = preprocess_article_text(article_data)
        
        # Should be identical
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)

    def test_preprocessing_with_various_inputs(self):
        """Test preprocessing with various input scenarios."""
        test_cases = [
            # Standard article
            {
                "title": "Standard Article",
                "abstract": "This is a normal abstract.",
                "content": "This is normal content."
            },
            # Article with HTML
            {
                "title": "<h1>HTML Title</h1>",
                "abstract": "<p>HTML abstract</p>",
                "content": "<div>HTML content</div>"
            },
            # Article with URLs and emails
            {
                "title": "Article with Links",
                "abstract": "Check https://example.com",
                "content": "Contact test@example.com"
            },
            # Article with special characters
            {
                "title": "Special Characters @#$%",
                "abstract": "Abstract with symbols &*^%$#",
                "content": "Content with punctuation!!!"
            },
            # Empty fields
            {
                "title": "",
                "abstract": "",
                "content": ""
            },
            # Missing fields
            {
                "title": "Only Title"
            }
        ]
        
        for i, article_data in enumerate(test_cases):
            with self.subTest(case=i):
                result = preprocess_article_text(article_data)
                
                # Should always return a string
                self.assertIsInstance(result, str)
                
                # Should not contain HTML tags if they were present
                if any('<' in str(v) for v in article_data.values() if v):
                    self.assertNotIn('<', result)
                    self.assertNotIn('>', result)


class TestAsyncIntegration(unittest.TestCase):
    """Test async integration scenarios."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_async_preprocessing_mock(self):
        """Test async preprocessing workflow (mocked)."""
        
        async def mock_article_creation():
            """Mock async article creation with preprocessing."""
            # Simulate article data
            article_data = {
                "title": "Async Article",
                "abstract": "Async abstract with https://example.com",
                "content": "Async content with test@example.com"
            }
            
            # Simulate preprocessing during creation
            preprocessed = preprocess_article_text(article_data)
            article_data["preprocessed_searchable_text"] = preprocessed
            
            return article_data
        
        # Run the async function
        result = self.loop.run_until_complete(mock_article_creation())
        
        # Verify preprocessing occurred
        self.assertIn("preprocessed_searchable_text", result)
        self.assertIn("Async Article", result["preprocessed_searchable_text"])
        self.assertNotIn("https://", result["preprocessed_searchable_text"])
        self.assertNotIn("@example.com", result["preprocessed_searchable_text"])

    def test_async_preprocessing_update_mock(self):
        """Test async preprocessing during article update (mocked)."""
        
        async def mock_article_update():
            """Mock async article update with preprocessing."""
            # Original article
            original_article = {
                "title": "Original Title",
                "abstract": "Original abstract",
                "content": "Original content",
                "preprocessed_searchable_text": "Original Title Original abstract Original content"
            }
            
            # Update data
            update_data = {
                "title": "Updated Title",
                "content": "Updated content with https://newlink.com"
            }
            
            # Check if preprocessing needed
            current_title = update_data.get('title', original_article.get('title'))
            current_abstract = update_data.get('abstract', original_article.get('abstract'))
            current_content = update_data.get('content', original_article.get('content'))
            
            article_data = {
                'title': current_title,
                'abstract': current_abstract,
                'content': current_content
            }
            
            # Generate new preprocessed text
            new_preprocessed = preprocess_article_text(article_data)
            update_data["preprocessed_searchable_text"] = new_preprocessed
            
            # Apply update
            updated_article = original_article.copy()
            updated_article.update(update_data)
            
            return updated_article
        
        # Run the async function
        result = self.loop.run_until_complete(mock_article_update())
        
        # Verify preprocessing was updated
        self.assertEqual(result["title"], "Updated Title")
        self.assertIn("Updated Title", result["preprocessed_searchable_text"])
        self.assertNotIn("https://newlink.com", result["preprocessed_searchable_text"])
        self.assertNotIn("Original Title", result["preprocessed_searchable_text"])


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
