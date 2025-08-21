# 15/08/2025

Next steps:

- Ensure that when Cosmos DB data is updated / removed / added, everything has to be sync to the indexes in Azure AI Search
- Fix the Indexs of the AI Search because now we send everything from Cosmos DB to the Azure AI Search. BUT we need to only send necessary data for searching only
- Find a way to input the (query, k, page_idx, page_size) -> then retrieve only those article_id in this range
- LLM Layer for normalizing the query + filter + sorting + ... based on the definition of the function search
- LLM Layer for generating the answer based on the query + retrieved results

---

# 16/08/2025

Next steps:

- Integrate with the real backend
- Test if the indexers works correctly when there exists documents that are added / deleted / modified
- Preparing for the Frontend devs
- Asks NDK for suggestions and comments

Note:

- Although currently for searching we still implement the semantic + bm25 + dense + business score BUT for the free tier the semantic is not being used yet.
- Semantic is different from dense

  - Semantic ≠ Vector in Azure AI Search:
  - **Semantic search** = Azure **semantic ranker** that re-ranks text results, returning `@search.rerankerScore`. You don’t store vectors for this.
  - **Vector search** = KNN over your **embedding field** (HNSW), returning a similarity `@search.score` for the vector query.

---


21/08

- kiểm tra lại chức năng search( search "phú hà mã")
- trang profile sai number, chauw hiển thị ngày tạo account
- trang home xóa số bài viết, lượt xemm của author
- đã follow nhưng reload thì mất. (check status follow)
- phân trang đang xử lí bên frontend