from langchain_community.document_loaders import DirectoryLoader
from langchain_core.documents import Document

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import FAISS

DOCS = "docs/"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

loader = DirectoryLoader(DOCS, show_progress = True)
docs = loader.load()

formatted = []
for doc in docs:
    content = doc.page_content.split("\n")
    url = content[0].replace("URL: ", "")
    doc.page_content = "".join(content)
    doc.metadata["source"] = url
    formatted.append(doc)

embeddings = HuggingFaceEmbeddings(
    model_name = MODEL,
    model_kwargs = {
        "token": TOKEN
    }
)
chunker = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name = "gpt-4",
    chunk_size = 512,
    chunk_overlap = 256,
)
chunked = chunker.split_documents(formatted)
print("chunked into", len(chunked), "documents")

db = FAISS.from_documents(chunked, embeddings)
db.save_local("index")
print("saved faiss to index/")
