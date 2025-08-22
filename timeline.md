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

# 21/08

- kiểm tra lại chức năng search ( search "phú hà mã" ) ==> for the unmeaningful query, by default we use article search
- recommended authors and articles are not working now ==> now recommend articles = search (work) + recommend users thì đang làm
- *trang profile sai number, chưa hiển thị ngày tạo account ==> DONE*
- *trang home xóa số bài viết, lượt xem của author ==> DONE*
  ==> đã sửa thành có hiện bằng call query và tính toán ==> note là thằng cosmos db không cho xài aggregate function
- đã follow/like/dislike/bookmark nhưng reload thì mất (check status follow)
- phân trang đang xử lí bên frontend = nghĩa là hiện tại phân trang đang chưa đc take care đúng
- return field of total for search và các thứ bên backend đang chưa đồng bộ = total phải là tổng trang tuy nhiên total bên search hiện lại đang là tổng số elements
- trong quá trình return lại kết quả sau khi dùng DTO thì 2 thg kết quả search của articles và của authors đang bị chưa đúng thứ tự của score cao --> score thấp
- bug lúc register: khi register thành công, nó sẽ chưa login vô đc mà bị kẹt chỗ "User vô danh". nếu log out user vô danh thì login vô lại đc bình thường --> BUG
-
