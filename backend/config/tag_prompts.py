"""
Prompts configuration for auto-tagging service
"""

TAG_GENERATION_PROMPT = """Analyze this article and generate {needed_count} additional relevant tags.

Title: {clean_title}
Abstract: {clean_abstract}
Content preview: {clean_content}

Existing user tags: {existing_tags_text}

Generate {needed_count} NEW tags that:
- Are 1-3 words maximum
- Use lowercase with hyphens between words (e.g., "machine-learning", "data-science", "ai")
- Are relevant to the content topic
- Complement the existing tags (avoid duplicates)
- Are useful for article categorization
- Follow format: single-word OR word-word OR word-word-word

Return ONLY the new tags separated by commas, nothing else.
Example format: ai, machine-learning, natural-language-processing, data-science, computer-vision"""

TAG_VALIDATION_RULES = {
    "max_words": 3,
    "format": "lowercase-with-hyphens", 
    "separator": "-",
    "max_total_tags": 4,
    "max_user_tags": 2
}
