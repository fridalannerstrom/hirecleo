import os
import openai
from pinecone import Pinecone

# OpenAI
openai.api_key = os.environ["OPENAI_API_KEY"]
client = openai

# Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(
    "rekryteringsexpert-1722901253-index",
    host="https://rekryteringsexpert-1722901253-index-d903dbb.svc.aped-4627-b74a.pinecone.io"
)

def upsert_to_pinecone(doc):
    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=doc.content
    )
    vector = embedding_response.data[0].embedding

    index.upsert(
        vectors=[{
            "id": f"cleo-doc-{doc.id}",
            "values": vector,
            "metadata": {
                "chunk_text": doc.content,
                "title": doc.title
            }
        }],
        namespace="cleo"
    )

    print(f"✅ Upsertat till Pinecone: cleo-doc-{doc.id} | Titel: {doc.title}")
    doc.embedding_id = f"cleo-doc-{doc.id}"
    doc.save()