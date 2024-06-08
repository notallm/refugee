from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from langchain.prompts.prompt import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, HarmCategory, HarmBlockThreshold
from langchain_core.output_parsers import StrOutputParser

import requests
from bs4 import BeautifulSoup

import re

from scrape import clean_text

INDEX = "index/"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RESULTS = 7
KEY = "< GOOGLE CLOUD API KEY >"
PROMPT = """\
You are a helpful and qualified USCIS agent that answers questions on refugee laws, forms, and any general information about them.
Do not worry about anything other than that. You are allowed to give legal advice.
Given below is some context to help you answer the user"s message. You do not have to use it, but it may help craft your answer.

CONTEXT:
{context}

Be informative and detailed. Respond WITHOUT legal jargon. Don't be shakepspeare. Be helpful.

MESSAGE: {message}
"""
LEARN_MORE_COUNT = 5
LEARN_MORE_TIMEOUT = 3

embeddings = HuggingFaceEmbeddings(
    model_name = MODEL
)

vector = FAISS.load_local(INDEX, embeddings, allow_dangerous_deserialization = True)
retriever = vector.as_retriever(search_kwargs = {"k": RESULTS})

safety = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}
llm = ChatGoogleGenerativeAI(model = "gemini-pro", google_api_key = KEY, safety_settings = safety)
chain = (llm | StrOutputParser())

template = PromptTemplate.from_template(PROMPT)

def format_docs(docs: list) -> str:
    docs = [doc.page_content for doc in docs]
    return "\n\n".join(docs)

def get_context(message: str) -> list:
    return retriever.invoke(clean_text(message))

def learn_more(context: list) -> str:
    info = ["\n\n**Learn more**"]
    sources = list(set([doc.metadata["source"] for doc in context]))
    count = min(LEARN_MORE_COUNT, len(sources))
    info.extend([f"* [{url}]({url})" for url in sources[:count]])
    return "\n".join(info)

def answer(message: str, context: list) -> str:
    prompt = template.format(message = message, context = format_docs(context))
    for chunk in chain.stream(message):
        yield str(chunk)
    yield learn_more(context)
