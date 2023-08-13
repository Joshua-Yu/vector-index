## Artefacts of testing Neo4j Vector Index of version 5.11.0

Test Cases 

Common settings: 
  - dataset: GIST1M
  - Java Page Cache: 24gb
  - query using random sampling:

WITH toInteger(rand() * 1000000) AS seed 
MATCH (emb)  WHERE id(emb) = seed
CALL db.index.vector.queryNodes("embeddingIndex2", 100, emb.value) YIELD node, score
RETURN id(node), score;


TC1 - Cosine Similarity search, JDK 17, top 25

TC2 - Cosine Similarity search, JDK 21 + Vector API, top 25

TC3 - Cosine Similarity search, JDK 21 + Vector API, top 5

TC4 - Rest of TC2, after reload data

TC5 - Both Cosine and Euclidean Similarity, JDK 21 + Vector API, top 100 
