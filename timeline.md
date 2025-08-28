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

# 21/08 - 23/08

- ***Integrate with the real backend***
- ***Test if the indexers works correctly when there exists documents that are added / deleted / modified***
- ***Preparing for the Frontend devs***
- ***Asks NDK for suggestions and comments***
- ***trang profile sai number, chưa hiển thị ngày tạo account ==> DONE***
- ***trang home xóa số bài viết, lượt xem của author ==> DONE*
  ==> đã sửa thành có hiện bằng call query và tính toán ==> note là thằng cosmos db không cho xài aggregate function**

---

# 24/08

- ***trang homepage bây giờ loading 3 APIs for authors, articles stats and articles categories (tags) --> now this is done by concurrent loading ==> DONE***
- ***trang profile khi nhấn vào sẽ nằm ở đó, chỉ khi click lại lần nữa mới tắt ==> DONE***
- ***about page có 1 hình đang chưa hiển thị ==> DONE***
- ***recheck bookmark và dashboard page ==> DONE***
- ***đã follow/like/dislike/bookmark nhưng reload thì mất (check status follow) ==> DONE***
- ***hiện tại cache = backend redis cho homepage (call api for stats, categories and authors) + search results pages + blogs pages (có cái 3 mins cái thì 5 mins) ==> DONE***
- ***những card của article đang hiển thị lệch và không bằng nhau --> nguyên nhân maybe do có thằng có hình có thằng không có hình và maybe do hình của tụi nó không bằng nhau nữa ==> DONE***
- ***UI responsive for homepage + blog page + fix footer to correct redirect ==> DONE***

---

# 25/08

- ***bug lúc register: khi register thành công, nó sẽ chưa login vô đc mà bị kẹt chỗ "User vô danh". nếu log out user vô danh thì login vô lại đc bình thường ==> DONE***
- ***upload image when register not work ==> DONE***
- ***return field of total for search và các thứ bên backend đang chưa đồng bộ = total phải là tổng trang tuy nhiên total bên search hiện lại đang là tổng số elements ==> DONE ==> phân trang của articles + search now work perfectly in backend -> frontend***
- ***kiểm tra lại chức năng search ( search "phú hà mã" ) ==> for the unmeaningful query, currently by default we use article search***
- ***recommended articles now use title + abstract ==> DONE***
- ***should have auto tagging for each article ==> DONE***
- ***should have auto updated the recommended field of each article ==> DONE***
- ***fix bug when at the page of writing article, if we reload, we will be redirect to the login page ==> fix already in the `ProtectedRoute.js`***

---

# 26/08

- **Chức năng cấp quyền / xóa quyền writer của ADMIN cho 1 USER nào đó + Chức năng deactivate account của user / writer nào đó ==> DONE**
- **Chuong done deploy on Azure for the current webapp**

---

# 28/08

- update bị lâu do recommend ...      done
- check lại summary (api/articles/stats) xem đã filter is_active=false chưa, đang bị get all item xong mới đếm chứ hong phải là select + count done
- chương fix phân trang của tất cả :)))  
- hiện tại chương sẽ soft delete user TUY NHIÊN hong delete like dislike số lương bên article done
- get user by id hiện đang truyền app_id, tuy nhiên nếu sai app_id vẫn dô đc ==> chương fix   done
- get user in admin hiện đang truyền app_id, tuy nhiên nếu sai app_id vẫn dô đc ==> chương fix   done


---

# TODO

- add the `app_id` field for the users and authors and update the code for the `index` and `indexer` to get that field from cosmos db too and update the search function to include the `app_id` field in the `filter`. 
- update the backend for those creation methods to include the `app_id` field 
- update the deletion of user from the admin dashboard and backend api such that the `is_active=false` for soft delete (done in index, indexer of ai_search already).
- recommended authors and articles are not working now ==> now recommend articles = search (work) + recommend users thì đang làm
- trong quá trình return lại kết quả sau khi dùng DTO thì 2 thg kết quả search của articles và của authors đang bị chưa đúng thứ tự của score cao --> score thấp
- AUTO fit with new data or firms



