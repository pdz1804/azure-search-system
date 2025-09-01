"""
Unit tests for text preprocessing functionality.

This module tests all text preprocessing utilities to ensure they work
correctly and handle edge cases properly.
"""

import unittest
import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
ai_search_path = os.path.join(project_root, 'ai_search')
if ai_search_path not in sys.path:
    sys.path.append(ai_search_path)

from ai_search.utils.text_preprocessing import (
    strip_html_tags,
    remove_urls,
    remove_emails,
    normalize_whitespace,
    remove_special_characters,
    remove_excessive_punctuation,
    clean_and_normalize_text,
    prepare_searchable_text,
    generate_preprocessed_content
)


class TestTextPreprocessing(unittest.TestCase):
    """Test cases for text preprocessing utilities."""

    def test_strip_html_tags(self):
        """Test HTML tag removal functionality."""
        # Basic HTML removal
        text = "<p>Hello <b>world</b>!</p>"
        result = strip_html_tags(text)
        self.assertEqual(result, "Hello world!")
        
        # Complex HTML with attributes
        text = '<div class="content"><a href="http://example.com">Link</a></div>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Link")
        
        # HTML entities with script content - scripts are completely removed (security and cleanliness)
        text = "&lt;script&gt;alert(&#39;test&#39;);&lt;/script&gt;"
        result = strip_html_tags(text)
        self.assertEqual(result, "")
        
        # HTML entities in regular content - entities decoded, tags removed
        text = "&lt;p&gt;Hello &amp; welcome!&lt;/p&gt;"
        result = strip_html_tags(text)
        self.assertEqual(result, "Hello & welcome!")
        
        # Embedded content removal
        text = '<p>Text before</p><img src="image.jpg" alt="image"/><p>Text after</p>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Text beforeText after")
        
        # CSS and JavaScript removal
        text = '<style>body{color:red;}</style><p>Content</p><script>alert("hi");</script>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Content")
        
        # Video and iframe removal
        text = '<p>Watch this:</p><iframe src="video.mp4"></iframe><p>More content</p>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Watch this:More content")
        
        # Empty and None input
        self.assertEqual(strip_html_tags(""), "")
        self.assertEqual(strip_html_tags(None), "")

    def test_remove_urls(self):
        """Test URL removal functionality."""
        # HTTP URLs
        text = "Visit https://example.com for more info"
        result = remove_urls(text)
        self.assertEqual(result, "Visit  for more info")
        
        # HTTPS URLs with paths
        text = "Check out https://example.com/path/to/page?param=value"
        result = remove_urls(text)
        self.assertEqual(result, "Check out ")
        
        # WWW URLs
        text = "Go to www.example.com"
        result = remove_urls(text)
        self.assertEqual(result, "Go to ")
        
        # Domain only
        text = "Contact us at example.com"
        result = remove_urls(text)
        self.assertEqual(result, "Contact us at ")
        
        # Multiple URLs
        text = "Visit http://site1.com and https://site2.com"
        result = remove_urls(text)
        self.assertEqual(result, "Visit  and ")
        
        # No URLs
        text = "No URLs in this text"
        result = remove_urls(text)
        self.assertEqual(result, "No URLs in this text")

    def test_remove_emails(self):
        """Test email removal functionality."""
        # Simple email
        text = "Contact us at test@example.com"
        result = remove_emails(text)
        self.assertEqual(result, "Contact us at ")
        
        # Complex email
        text = "Reach out to user.name+tag@domain.co.uk"
        result = remove_emails(text)
        self.assertEqual(result, "Reach out to ")
        
        # Multiple emails
        text = "Email john@doe.com or jane@smith.org"
        result = remove_emails(text)
        self.assertEqual(result, "Email  or ")
        
        # No emails
        text = "No emails in this text"
        result = remove_emails(text)
        self.assertEqual(result, "No emails in this text")

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        # Multiple spaces
        text = "Hello    world"
        result = normalize_whitespace(text)
        self.assertEqual(result, "Hello world")
        
        # Mixed whitespace
        text = "Hello\t\t\nworld\r\n  test"
        result = normalize_whitespace(text)
        self.assertEqual(result, "Hello world test")
        
        # Leading/trailing whitespace
        text = "  Hello world  "
        result = normalize_whitespace(text)
        self.assertEqual(result, "Hello world")
        
        # Empty string
        self.assertEqual(normalize_whitespace(""), "")
        self.assertEqual(normalize_whitespace(None), "")

    def test_remove_special_characters(self):
        """Test special character removal."""
        # Preserve punctuation
        text = "Hello, world! How are you?"
        result = remove_special_characters(text, preserve_basic_punctuation=True)
        self.assertEqual(result, "Hello, world! How are you?")
        
        # Remove all special chars
        text = "Hello@#$%^&*()world!"
        result = remove_special_characters(text, preserve_basic_punctuation=False)
        self.assertEqual(result, "Helloworld")
        
        # Keep basic punctuation, remove others
        text = "Hello@#$%^&*()world! How are you?"
        result = remove_special_characters(text, preserve_basic_punctuation=True)
        self.assertEqual(result, "Helloworld! How are you?")

    def test_remove_excessive_punctuation(self):
        """Test excessive punctuation removal."""
        # Multiple dots
        text = "Hello... world"
        result = remove_excessive_punctuation(text)
        self.assertEqual(result, "Hello. world")
        
        # Multiple exclamations
        text = "Amazing!!!"
        result = remove_excessive_punctuation(text)
        self.assertEqual(result, "Amazing!")
        
        # Multiple question marks
        text = "Really???"
        result = remove_excessive_punctuation(text)
        self.assertEqual(result, "Really?")
        
        # Mixed excessive punctuation
        text = "Wait... what?? No way!!!"
        result = remove_excessive_punctuation(text)
        self.assertEqual(result, "Wait. what? No way!")

    def test_clean_and_normalize_text(self):
        """Test comprehensive text cleaning."""
        # Complex input with multiple issues
        text = """
        <p>Hello <b>world</b>!</p>
        
        Visit https://example.com for more details...
        Contact us at test@example.com!!!
        
        Special chars: @#$%^&*()
        """
        
        result = clean_and_normalize_text(text)
        expected = "Hello world! Special chars:"
        self.assertEqual(result, expected)
        
        # Test with all flags disabled
        result = clean_and_normalize_text(
            text,
            remove_html=False,
            remove_urls_flag=False,
            remove_emails_flag=False,
            remove_special_chars=False,
            normalize_ws=True,
            remove_excess_punct=True
        )
        # Should only normalize whitespace and excessive punctuation
        self.assertIn("https://example.com", result)
        self.assertIn("test@example.com", result)

    def test_prepare_searchable_text(self):
        """Test searchable text preparation."""
        # Normal case
        title = "Article Title"
        abstract = "This is the abstract."
        content = "This is the main content."
        
        result = prepare_searchable_text(title, abstract, content)
        self.assertEqual(result, "Article Title This is the abstract. This is the main content.")
        
        # With HTML and special chars
        title = "<h1>Title</h1>"
        abstract = "Abstract with https://example.com"
        content = "Content with test@example.com!!!"
        
        result = prepare_searchable_text(title, abstract, content)
        self.assertEqual(result, "Title Abstract with Content with")
        
        # Empty fields
        result = prepare_searchable_text("", "", "")
        self.assertEqual(result, "")
        
        # Some empty fields
        result = prepare_searchable_text("Title", "", "Content")
        self.assertEqual(result, "Title Content")
        
        # Custom separator
        result = prepare_searchable_text("Title", "Abstract", "Content", separator=" | ")
        self.assertEqual(result, "Title | Abstract | Content")
        
        # Max length truncation
        long_content = "word " * 100  # 500 characters
        result = prepare_searchable_text("Title", "Abstract", long_content, max_length=50)
        self.assertTrue(len(result) <= 50)
        self.assertTrue(result.endswith("word"))  # Should truncate at word boundary

    def test_generate_preprocessed_content(self):
        """Test preprocessed content generation from article data."""
        # Complete article
        article_data = {
            "title": "<h1>Article Title</h1>",
            "abstract": "This is the abstract with https://example.com",
            "content": "Main content with test@example.com and special chars@#$!"
        }
        
        result = generate_preprocessed_content(article_data)
        expected = "Article Title This is the abstract with Main content with and special chars"
        self.assertEqual(result, expected)
        
        # Missing fields
        article_data = {
            "title": "Title Only"
        }
        
        result = generate_preprocessed_content(article_data)
        self.assertEqual(result, "Title Only")
        
        # Empty article
        article_data = {}
        result = generate_preprocessed_content(article_data)
        self.assertEqual(result, "")

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # None inputs
        self.assertEqual(strip_html_tags(None), "")
        self.assertEqual(remove_urls(None), "")
        self.assertEqual(remove_emails(None), "")
        self.assertEqual(normalize_whitespace(None), "")
        
        # Very long text
        long_text = "a" * 10000
        result = clean_and_normalize_text(long_text)
        self.assertTrue(len(result) <= 10000)
        
        # Unicode characters
        unicode_text = "Hello 🌍 World! café naïve résumé"
        result = clean_and_normalize_text(unicode_text)
        self.assertIn("Hello", result)
        self.assertIn("World", result)

    def test_sentiment_preservation(self):
        """Test that positive and negative sentiment is preserved."""
        # Positive sentiment
        positive_text = "This is an amazing and wonderful article! Great work!"
        result = clean_and_normalize_text(positive_text)
        self.assertIn("amazing", result)
        self.assertIn("wonderful", result)
        self.assertIn("Great", result)
        
        # Negative sentiment
        negative_text = "This is terrible and awful content. Bad work!"
        result = clean_and_normalize_text(negative_text)
        self.assertIn("terrible", result)
        self.assertIn("awful", result)
        self.assertIn("Bad", result)
        
        # Mixed sentiment
        mixed_text = "Some parts are good but others are bad."
        result = clean_and_normalize_text(mixed_text)
        self.assertIn("good", result)
        self.assertIn("bad", result)


class TestAdvancedHTMLHandling(unittest.TestCase):
    """Test advanced HTML handling capabilities."""

    def test_embedded_content_removal(self):
        """Test removal of embedded content like images, videos, iframes."""
        # Images
        text = '<p>Before image</p><img src="test.jpg" alt="test"/><p>After image</p>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Before imageAfter image")
        
        # Videos
        text = '<p>Video:</p><video src="test.mp4" controls></video><p>End</p>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Video:End")
        
        # Iframes
        text = '<div>Content</div><iframe src="https://example.com"></iframe><div>More</div>'
        result = strip_html_tags(text)
        self.assertEqual(result, "ContentMore")
        
        # SVG
        text = '<p>Icon:</p><svg><circle r="5"/></svg><p>Text</p>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Icon:Text")

    def test_css_javascript_removal(self):
        """Test removal of CSS and JavaScript blocks."""
        # CSS removal
        text = '<style type="text/css">body { color: red; }</style><p>Content</p>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Content")
        
        # JavaScript removal
        text = '<script>alert("hello");</script><div>Text</div>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Text")
        
        # NoScript removal
        text = '<noscript>No JS message</noscript><p>Main content</p>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Main content")
        
        # Combined
        text = '''
        <style>
        .class { color: blue; }
        </style>
        <script type="text/javascript">
        function test() { return true; }
        </script>
        <p>Real content here</p>
        '''
        result = strip_html_tags(text)
        self.assertEqual(result.strip(), "Real content here")

    def test_nested_html_handling(self):
        """Test handling of deeply nested HTML structures."""
        # Nested tags with text
        text = '<div><p>Outer <span>inner <b>bold</b> text</span> more</p></div>'
        result = strip_html_tags(text)
        self.assertEqual(result, "Outer inner bold text more")
        
        # Nested with embedded content
        text = '<div><p>Text</p><img src="test.jpg"/><span>More text</span></div>'
        result = strip_html_tags(text)
        self.assertEqual(result, "TextMore text")
        
        # Complex nesting
        text = '''
        <article>
            <header><h1>Title</h1></header>
            <section>
                <p>Paragraph with <a href="link">link</a></p>
                <img src="image.jpg" alt="Image"/>
                <p>Another paragraph</p>
            </section>
        </article>
        '''
        result = strip_html_tags(text)
        # Should preserve text content, remove image
        self.assertIn("Title", result)
        self.assertIn("Paragraph with link", result)
        self.assertIn("Another paragraph", result)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete preprocessing pipeline."""

    def test_real_world_article(self):
        """Test with realistic article content."""
        article_data = {
            "title": "Getting Started with Machine Learning",
            "abstract": "This article covers the basics of ML. Visit https://ml-guide.com for more resources.",
            "content": """
            <h2>Introduction</h2>
            <p>Machine learning is an <strong>exciting</strong> field!</p>
            
            <h3>Key Concepts:</h3>
            <ul>
                <li>Supervised learning</li>
                <li>Unsupervised learning</li>
                <li>Reinforcement learning</li>
            </ul>
            
            <p>For questions, contact us at help@mlguide.com</p>
            
            Links:
            - https://scikit-learn.org
            - https://tensorflow.org
            
            Special characters: @#$%^&*()
            """
        }
        
        result = generate_preprocessed_content(article_data)
        
        # Should contain core content
        self.assertIn("Getting Started with Machine Learning", result)
        self.assertIn("Machine learning", result)
        self.assertIn("exciting", result)  # Sentiment preserved
        self.assertIn("Supervised learning", result)
        
        # Should not contain noise
        self.assertNotIn("<h2>", result)
        self.assertNotIn("<p>", result)
        self.assertNotIn("https://", result)
        self.assertNotIn("@", result)
        self.assertNotIn("#$%", result)

    def test_complex_html_article(self):
        """Test with article containing complex HTML including embedded content."""
        article_data = {
            "title": "Machine Learning Guide",
            "abstract": "Complete guide with examples. Visit https://ml-examples.com",
            "content": """
            <style>
            .highlight { background: yellow; }
            </style>
            <h2>Introduction</h2>
            <p>Machine learning is <strong>powerful</strong>!</p>
            
            <script>
            function trackEvent() { analytics.track('view'); }
            </script>
            
            <div class="video-container">
                <iframe src="https://youtube.com/embed/xyz" width="560" height="315"></iframe>
            </div>
            
            <img src="diagram.png" alt="ML Diagram" />
            
            <p>Key concepts:</p>
            <ul>
                <li>Supervised learning</li>
                <li>Neural networks</li>
            </ul>
            
            <p>Contact us at support@mlguide.com for questions.</p>
            """
        }
        
        result = generate_preprocessed_content(article_data)
        
        # Should contain core content
        self.assertIn("Machine Learning Guide", result)
        self.assertIn("Complete guide with examples", result)
        self.assertIn("Introduction", result)
        self.assertIn("Machine learning is powerful", result)
        self.assertIn("Key concepts", result)
        self.assertIn("Supervised learning", result)
        self.assertIn("Neural networks", result)
        
        # Should not contain removed elements
        self.assertNotIn("style", result)
        self.assertNotIn("script", result)
        self.assertNotIn("function", result)
        self.assertNotIn("iframe", result)
        self.assertNotIn("youtube.com", result)
        self.assertNotIn("support@mlguide.com", result)
        self.assertNotIn("https://ml-examples.com", result)

    def test_performance_text(self):
        """Test preprocessing performance with large text."""
        # Create large article
        large_content = """
        <p>This is a paragraph with <strong>bold text</strong> and links to https://example.com.</p>
        """ * 100
        
        article_data = {
            "title": "Large Article",
            "abstract": "This is a large article for testing.",
            "content": large_content
        }
        
        import time
        start_time = time.time()
        result = generate_preprocessed_content(article_data)
        end_time = time.time()
        
        # Should complete reasonably quickly (under 1 second)
        self.assertLess(end_time - start_time, 1.0)
        
        # Should produce reasonable output
        self.assertTrue(len(result) > 0)
        self.assertNotIn("<p>", result)
        self.assertNotIn("https://", result)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
