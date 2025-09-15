Note

- 2 files search_service.py at backend\services\search_service.py and ai_search\app\services\search_service.py are the same, i just make the copy from ai_search to the backend. If you ask about the main file that runs in our project i would say that it is the file service in the backend. currently during the search we should have the args named app_id to filter during the search progress to return the correct elements of the search for the correct apps
- Currently i use the free account tier on azure so the search function of the SearchClient, currently the arg query_type i can only set to simple only, cannot use the value of semantic for reranking because enable the reranking needs the higher tier accounts
- 
