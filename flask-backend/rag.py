import os
from azure.search.documents.models import VectorizedQuery
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SemanticSearch,
    SearchField,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
    SearchIndex,
)
from azure.core.credentials import AzureKeyCredential
from util import embed_text, generate
from prompt.rag_prompt import system_prompt_generator

index_client = SearchIndexClient(endpoint=os.environ["SEARCH_ENDPOINT"], credential=AzureKeyCredential(os.environ["SEARCH_KEY"]))

print('initialize index_client')

def create_index_definition(index_name: str, model: str):
	dimensions = 1536  # text-embedding-ada-002
	fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
		SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            # Size of the vector created by the text-embedding-ada-002 model.
            vector_search_dimensions=dimensions,
            vector_search_profile_name="myHnswProfile",
        ),
    ]
	
    # The "content" field should be prioritized for semantic ranking.
	semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            keywords_fields=[],
            content_fields=[SemanticField(field_name="content")],
        ),
    )

	# For vector search, we want to use the HNSW (Hierarchical Navigable Small World)
    # algorithm (a type of approximate nearest neighbor search algorithm) with cosine
    # distance.
	vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw",
                kind=VectorSearchAlgorithmKind.HNSW,
                parameters=HnswParameters(
                    m=4,
                    ef_construction=1000,
                    ef_search=1000,
                    metric=VectorSearchAlgorithmMetric.COSINE,
                ),
            ),
            ExhaustiveKnnAlgorithmConfiguration(
                name="myExhaustiveKnn",
                kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                parameters=ExhaustiveKnnParameters(metric=VectorSearchAlgorithmMetric.COSINE),
            ),
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            ),
            VectorSearchProfile(
                name="myExhaustiveKnnProfile",
                algorithm_configuration_name="myExhaustiveKnn",
            ),
        ],
    )
	semantic_search = SemanticSearch(configurations=[semantic_config])
	
	return SearchIndex(
        name=index_name,
        fields=fields,
        semantic_search=semantic_search,
        vector_search=vector_search,
    )

def create_docs_from_text(paragraphs:list[str], model: str) -> list[dict[str, any]]:
    items = []
    for i in range(len(paragraphs)):
        content = paragraphs[i]
        id = str(i)
        emb = embed_text(str(content),model)
        rec = {
            "id": id,
            "content": content,
            "contentVector": emb,
        }
        items.append(rec)
    return items
	
def create_index_from_text(index_name:str, paragraphs:list[str]):
    # index_client = SearchIndexClient(endpoint=os.environ["SEARCH_ENDPOINT"], credential=AzureKeyCredential(os.environ["SEARCH_KEY"]))
	# If a search index already exists, delete it:
    try:
        index_definition = index_client.get_index(index_name)
        index_client.delete_index(index_name)
        print(f"🗑️  Found existing index named '{index_name}', and deleted it")
    except Exception:
        pass

    # create an empty search index
    index_definition = create_index_definition(index_name, model=os.environ["EMBEDDINGS_MODEL_NAME"])
    index_client.create_index(index_definition)

    docs = create_docs_from_text(paragraphs, os.environ["EMBEDDINGS_MODEL_NAME"])
    
    # Add the documents to the index using the Azure AI Search client
    search_client = SearchClient(
        endpoint=os.environ["SEARCH_ENDPOINT"],
        index_name=index_name,
        credential=AzureKeyCredential(key=os.environ["SEARCH_KEY"]),
    )
    search_client.upload_documents(docs)
    print(f"➕ Uploaded {len(paragraphs)} documents to '{index_name}' index")
    return index_name


def retrieve_docs_hybrid(text: str, index_name: str, top_k: int, semantic_reranking: bool) -> str:
    """
    Retrieve documents using a hybrid search combining text and vector queries.

    Args:
        text (str): The text query for the search.
        index_name (str): The name of the search index.
        top_k (int): The number of top documents to retrieve.
        semantic_reranking (bool): Whether to use semantic reranking.

    Returns:
        str: The retrieved documents or an empty string if an error occurs.
    """
    try:
        search_client = SearchClient(
            endpoint=os.environ["SEARCH_ENDPOINT"],
            index_name=index_name,
            credential=AzureKeyCredential(key=os.environ["SEARCH_KEY"]),
        )
        vector_query = VectorizedQuery(
            vector=embed_text(text, model_name=os.getenv("EMBEDDING_MODEL_NAME")),
            k_nearest_neighbors=top_k,
            fields="contentVector"
        )
        search_params = {
            "search_text": text,
            "vector_queries": [vector_query],
            "select": ["content"],
            "top": top_k
        }
        if semantic_reranking:
            search_params.update({
                "query_type": "semantic",
                "semantic_query": text,
                "semantic_configuration_name": "default"
            })
        results = search_client.search(**search_params)
        retrieved_docs = "Retrieved course documents"
        for retrieved_doc in results:
            retrieved_docs += f"\n==========================================\n{retrieved_doc['content']}"
        return retrieved_docs
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return ''

def chat_with_web(query: str, index_name:str, top_k:int, context: dict = None) -> dict:
    if context is None:
        context = {}

    documents = retrieve_docs_hybrid(query,index_name, top_k, False)
    print(documents)

    system_message = system_prompt_generator(query=query, documents=documents)
    print(f"system prompt: {system_message}")
    response = generate(system_message)
    print(f"💬 Response: {response}")

    # Return a chat protocol compliant response
    return {"message": response, "context": context}
