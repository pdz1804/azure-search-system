"""
Command line argument parser for the Blog Search API.
Provides CLI commands for index creation, ingestion, and server startup.
"""

import argparse
import sys
from typing import Optional

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Blog Search API - Azure AI Search + Cosmos DB + Embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py create-indexes --verbose
  python main.py create-indexes --reset
  python main.py ingest --verbose
  python main.py serve --host 0.0.0.0 --port 8000
        """)
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create indexes command
    create_idx_parser = subparsers.add_parser(
        'create-indexes', 
        help='Create Azure AI Search indexes (articles-index, authors-index)'
    )
    create_idx_parser.add_argument(
        '--reset', 
        action='store_true', 
        help='Delete existing indexes before creating new ones (default: True)'
    )
    create_idx_parser.add_argument(
        '--no-reset', 
        action='store_true', 
        help='Do not delete existing indexes before creating'
    )
    create_idx_parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose debug output during index creation'
    )
    
    # Ingest data command
    ingest_parser = subparsers.add_parser(
        'ingest', 
        help='Ingest data from Cosmos DB into Azure AI Search indexes'
    )
    ingest_parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose output during data ingestion'
    )
    ingest_parser.add_argument(
        '--batch-size', 
        type=int, 
        default=100, 
        help='Batch size for document ingestion (default: 100)'
    )
    
    # Serve FastAPI command
    serve_parser = subparsers.add_parser(
        'serve', 
        help='Start the FastAPI server'
    )
    serve_parser.add_argument(
        '--host', 
        type=str, 
        default='127.0.0.1', 
        help='Host to bind the server to (default: 127.0.0.1)'
    )
    serve_parser.add_argument(
        '--port', 
        type=int, 
        default=8000, 
        help='Port to bind the server to (default: 8000)'
    )
    serve_parser.add_argument(
        '--reload', 
        action='store_true', 
        help='Enable auto-reload for development'
    )
    serve_parser.add_argument(
        '--workers', 
        type=int, 
        default=1, 
        help='Number of worker processes (default: 1)'
    )
    
    # Azure Indexers command
    indexers_parser = subparsers.add_parser(
        'setup-indexers', 
        help='Setup Azure AI Search indexers for automatic Cosmos DB sync'
    )
    indexers_parser.add_argument(
        '--reset', 
        action='store_true', 
        help='Delete existing indexers before creating new ones'
    )
    indexers_parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose output during indexer setup'
    )
    
    # Check indexers status command
    status_parser = subparsers.add_parser(
        'check-indexers', 
        help='Check status of Azure AI Search indexers'
    )
    status_parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose status output'
    )
    
    # Health check command
    health_parser = subparsers.add_parser(
        'health', 
        help='Check health status of indexes, indexers, and search service'
    )
    health_parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable detailed health information'
    )
    
    return parser

def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_parser()
    if args is None:
        args = sys.argv[1:]
    
    parsed = parser.parse_args(args)
    
    # Handle conflicting reset options
    if hasattr(parsed, 'reset') and hasattr(parsed, 'no_reset'):
        if parsed.no_reset:
            parsed.reset = False
        elif not hasattr(parsed, 'reset') or parsed.reset is None:
            parsed.reset = True  # Default to reset
    
    return parsed
