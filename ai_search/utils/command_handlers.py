"""
Command handlers for the Azure AI Blog Search CLI application.

This module contains all command handling logic separated from the main application
entry point for better code organization and maintainability.

Design Pattern: Command Pattern - Each handler is a separate function that encapsulates
the logic for handling a specific CLI command.
"""

import sys
from typing import Any


def handle_create_indexes(args: Any) -> None:
    """
    Handle the 'create-indexes' command to set up Azure Search indexes.
    
    Args:
        args: Parsed command line arguments containing reset and verbose flags
    """
    print("🏗️  Creating Azure AI Search indexes...")
    from ai_search.search.indexes import create_indexes
    
    reset = getattr(args, 'reset', True)
    verbose = getattr(args, 'verbose', False)
    
    print(f"📋 Options: reset={reset}, verbose={verbose}")
    create_indexes(reset=reset, verbose=verbose)
    print("✅ Index creation completed successfully")


def handle_ingest(args: Any) -> None:
    """
    Handle the 'ingest' command to load data from Cosmos DB into search indexes.
    
    Args:
        args: Parsed command line arguments containing batch_size and verbose flags
    """
    print("📥 Starting data ingestion...")
    from ai_search.search.ingestion import ingest
    
    batch_size = getattr(args, 'batch_size', 100)
    verbose = getattr(args, 'verbose', False)
    
    ingest(batch_size=batch_size, verbose=verbose)
    print("✅ Data ingestion completed")


def handle_setup_indexers(args: Any) -> None:
    """
    Handle the 'setup-indexers' command to configure Azure Search indexers.
    
    Args:
        args: Parsed command line arguments containing reset and verbose flags
    """
    print("⚙️ Setting up Azure AI Search indexers...")
    from ai_search.search.indexers import setup_azure_indexers
    
    reset = getattr(args, 'reset', False)
    verbose = getattr(args, 'verbose', False)
    
    setup_azure_indexers(reset=reset, verbose=verbose)
    print("✅ Azure indexers setup completed")


def handle_check_indexers(args: Any) -> None:
    """
    Handle the 'check-indexers' command to verify indexer status.
    
    Args:
        args: Parsed command line arguments containing verbose flag
    """
    print("📊 Checking Azure AI Search indexers status...")
    from ai_search.search.indexers import check_indexer_status
    
    verbose = getattr(args, 'verbose', False)
    statuses = check_indexer_status(verbose=verbose)
    
    if not verbose:
        print("\n📈 Indexer Status Summary:")
        for status in statuses:
            if 'error' in status:
                print(f"   ❌ {status['name']}: {status['error']}")
            else:
                print(f"   ✅ {status['name']}: {status.get('status', 'Unknown')}")
    
    print("✅ Status check completed")


def handle_health(args: Any) -> None:
    """
    Handle the 'health' command to check overall system health.
    
    This comprehensive health check verifies:
    - Search indexes existence and accessibility
    - Indexers status and functionality
    - Cache configuration and status
    - Search service connectivity and capabilities
    
    Args:
        args: Parsed command line arguments containing verbose flag
    """
    print("🏥 Checking system health...")
    verbose = getattr(args, 'verbose', False)
    
    health_status = {
        'indexes': {'status': 'unknown', 'details': []},
        'indexers': {'status': 'unknown', 'details': []},
        'cache': {'status': 'unknown', 'details': []},
        'search_service': {'status': 'unknown', 'details': []},
        'overall': 'unknown'
    }
    
    # Check indexes
    health_status = _check_indexes_health(health_status, verbose)
    
    # Check indexers
    health_status = _check_indexers_health(health_status, verbose)
    
    # Check cache status
    health_status = _check_cache_health(health_status, verbose)
    
    # Check search service connectivity
    health_status = _check_search_service_health(health_status, verbose)
    
    # Determine overall health
    _determine_overall_health(health_status)
    
    # Print summary
    _print_health_summary(health_status)
    
    print("✅ Health check completed")


def handle_serve(args: Any) -> None:
    """
    Handle the 'serve' command to start the FastAPI server.
    
    Args:
        args: Parsed command line arguments containing server configuration
    """
    print("🌐 Starting FastAPI server...")
    import uvicorn
    
    host = getattr(args, 'host', '127.0.0.1')
    port = getattr(args, 'port', 8000)
    reload = getattr(args, 'reload', False)
    workers = getattr(args, 'workers', 1)
    
    # uvicorn doesn't support workers with reload
    if reload:
        workers = 1
    
    print(f"📋 Server options: {host}:{port}, reload={reload}, workers={workers}")
    # Use package-qualified module path so the reloader can import the app when running
    # via `python -m ai_search.main serve`.
    uvicorn.run(
        "ai_search.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )


def _check_indexes_health(health_status: dict, verbose: bool) -> dict:
    """
    Check the health of search indexes.
    
    Args:
        health_status: Current health status dictionary
        verbose: Whether to enable verbose output
        
    Returns:
        Updated health status dictionary
    """
    try:
        print("\n🔍 Checking search indexes...")
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
        from ai_search.config.settings import SETTINGS
        
        index_client = SearchIndexClient(SETTINGS.search_endpoint, AzureKeyCredential(SETTINGS.search_key))
        
        expected_indexes = ['articles-index', 'authors-index']
        existing_indexes = [idx.name for idx in index_client.list_indexes()]
        
        missing_indexes = [idx for idx in expected_indexes if idx not in existing_indexes]
        
        if not missing_indexes:
            health_status['indexes']['status'] = 'healthy'
            health_status['indexes']['details'] = [f"✅ {idx} exists" for idx in expected_indexes]
            print("   ✅ All required indexes exist")
        else:
            health_status['indexes']['status'] = 'unhealthy'
            health_status['indexes']['details'] = [
                f"✅ {idx} exists" for idx in expected_indexes if idx in existing_indexes
            ] + [
                f"❌ {idx} missing" for idx in missing_indexes
            ]
            print(f"   ❌ Missing indexes: {', '.join(missing_indexes)}")
        
        if verbose:
            for detail in health_status['indexes']['details']:
                print(f"     {detail}")
        
    except Exception as e:
        health_status['indexes']['status'] = 'error'
        health_status['indexes']['details'] = [f"❌ Error checking indexes: {e}"]
        print(f"   ❌ Error checking indexes: {e}")
    
    return health_status


def _check_indexers_health(health_status: dict, verbose: bool) -> dict:
    """
    Check the health of indexers.
    
    Args:
        health_status: Current health status dictionary
        verbose: Whether to enable verbose output
        
    Returns:
        Updated health status dictionary
    """
    try:
        print("\n⚙️ Checking indexers...")
        from ai_search.search.indexers import check_indexer_status
        
        indexer_statuses = check_indexer_status(verbose=False)
        healthy_indexers = 0
        total_indexers = len(indexer_statuses)
        
        for status in indexer_statuses:
            if 'error' not in status and status.get('status') == 'running':
                healthy_indexers += 1
                health_status['indexers']['details'].append(f"✅ {status['name']}: {status.get('status', 'Unknown')}")
            else:
                error_msg = status.get('error', 'Unknown status')
                health_status['indexers']['details'].append(f"❌ {status['name']}: {error_msg}")
        
        if healthy_indexers == total_indexers:
            health_status['indexers']['status'] = 'healthy'
            print(f"   ✅ All {total_indexers} indexers are running")
        elif healthy_indexers > 0:
            health_status['indexers']['status'] = 'partial'
            print(f"   ⚠️ {healthy_indexers}/{total_indexers} indexers are healthy")
        else:
            health_status['indexers']['status'] = 'unhealthy'
            print(f"   ❌ No indexers are running properly")
        
        if verbose:
            for detail in health_status['indexers']['details']:
                print(f"     {detail}")
        
    except Exception as e:
        health_status['indexers']['status'] = 'error'
        health_status['indexers']['details'] = [f"❌ Error checking indexers: {e}"]
        print(f"   ❌ Error checking indexers: {e}")
    
    return health_status


def _check_cache_health(health_status: dict, verbose: bool) -> dict:
    """
    Check the health of indexer cache configuration.
    
    Args:
        health_status: Current health status dictionary
        verbose: Whether to enable verbose output
        
    Returns:
        Updated health status dictionary
    """
    try:
        print("\n🗂️ Checking cache configuration...")
        from ai_search.search.indexers import check_cache_status
        from ai_search.config.settings import SETTINGS
        
        cache_statuses = check_cache_status(verbose=False)
        cache_enabled_count = 0
        cache_configured_count = 0
        total_indexers = len(cache_statuses)
        
        for cache_status in cache_statuses:
            indexer_name = cache_status.get('indexer_name', 'unknown')
            
            if cache_status.get('cache_enabled', False):
                cache_enabled_count += 1
                
                if cache_status.get('cache_details', {}).get('storage_connection_configured', False):
                    cache_configured_count += 1
                    health_status['cache']['details'].append(f"✅ {indexer_name}: cache enabled and configured")
                else:
                    health_status['cache']['details'].append(f"⚠️ {indexer_name}: cache enabled but storage not configured")
            else:
                health_status['cache']['details'].append(f"ℹ️ {indexer_name}: cache disabled")
        
        if verbose:
            for detail in health_status['cache']['details']:
                print(f"     {detail}")
        
    except Exception as e:
        health_status['cache']['status'] = 'error'
        health_status['cache']['details'] = [f"❌ Error checking cache: {e}"]
        print(f"   ❌ Error checking cache: {e}")
    
    return health_status


def _check_search_service_health(health_status: dict, verbose: bool) -> dict:
    """
    Check the health of search service connectivity.
    
    Args:
        health_status: Current health status dictionary
        verbose: Whether to enable verbose output
        
    Returns:
        Updated health status dictionary
    """
    try:
        print("\n🔍 Checking search service connectivity...")
        # Import here to avoid circular imports and lazy loading
        from ai_search.main import get_search_service
        
        search_svc = get_search_service()
        
        # If we got here without exception, search service is working
        health_status['search_service']['status'] = 'healthy'
        health_status['search_service']['details'] = [
            "✅ Search service connection established",
            f"✅ Semantic search: {'enabled' if search_svc.semantic_enabled else 'disabled'}"
        ]
        print("   ✅ Search service is accessible")
        print(f"   ✅ Semantic search: {'enabled' if search_svc.semantic_enabled else 'disabled'}")
        
        if verbose:
            for detail in health_status['search_service']['details']:
                print(f"     {detail}")
        
    except Exception as e:
        health_status['search_service']['status'] = 'error'
        health_status['search_service']['details'] = [f"❌ Search service error: {e}"]
        print(f"   ❌ Search service error: {e}")
    
    return health_status


def _determine_overall_health(health_status: dict) -> None:
    """
    Determine overall system health based on component statuses.
    
    Args:
        health_status: Health status dictionary to update
    """
    # Core components (cache is optional)
    core_statuses = [
        health_status['indexes']['status'], 
        health_status['indexers']['status'], 
        health_status['search_service']['status']
    ]
    
    # Include cache status if it's not disabled
    cache_status = health_status['cache']['status']
    if cache_status not in ['disabled']:
        component_statuses = core_statuses + [cache_status]
    else:
        component_statuses = core_statuses
    
    if all(status == 'healthy' for status in component_statuses):
        health_status['overall'] = 'healthy'
        print("\n🎉 Overall system health: HEALTHY")
    elif any(status == 'healthy' for status in component_statuses):
        health_status['overall'] = 'partial'
        print("\n⚠️ Overall system health: PARTIAL")
    else:
        health_status['overall'] = 'unhealthy'
        print("\n❌ Overall system health: UNHEALTHY")


def _print_health_summary(health_status: dict) -> None:
    """
    Print a summary of the health check results.
    
    Args:
        health_status: Health status dictionary containing all component statuses
    """
    print("\n📋 Health Check Summary:")
    print(f"   Indexes: {health_status['indexes']['status'].upper()}")
    print(f"   Indexers: {health_status['indexers']['status'].upper()}")
    print(f"   Cache: {health_status['cache']['status'].upper()}")
    print(f"   Search Service: {health_status['search_service']['status'].upper()}")
    print(f"   Overall: {health_status['overall'].upper()}")
    
    # Add cache explanation if disabled
    if health_status['cache']['status'] == 'disabled':
        print(f"   💡 Cache is disabled - enable with ENABLE_INDEXER_CACHE=true in .env")


def get_command_handlers() -> dict:
    """
    Get a dictionary mapping command names to their handler functions.
    
    This follows the Command Pattern, providing a clean way to map
    CLI commands to their respective handler functions.
    
    Returns:
        Dictionary mapping command names to handler functions
    """
    return {
        'create-indexes': handle_create_indexes,
        'ingest': handle_ingest,
        'setup-indexers': handle_setup_indexers,
        'check-indexers': handle_check_indexers,
        'health': handle_health,
        'serve': handle_serve
    }
