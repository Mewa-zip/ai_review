import ollama
import chromadb
import hashlib
from langchain_community.document_loaders import PyPDFLoader


client = chromadb.Client()
collection = client.get_or_create_collection(name="review_standards")

# zasady do RAG
collection.add(
    documents=[
        "Methodology: A lack of a control group or small sample size is a major red flag.",
        "Citations: References older than 5 years without a seminal reason are considered outdated.",
        "Ethics: Any AI-based paper must disclose the specific model versions and prompts used.",
        "Aesthetics: Frequent typos and poor LaTeX formatting decrease the paper's credibility."
    ],
    ids=["rule1", "rule2", "rule3", "rule4"]
)


def get_paper_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

# ekstrakcja tekstu PDF
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n".join([p.page_content for p in pages])


def write_review(pdf_path, character_type="substantive"):
    content = load_pdf(pdf_path)
    # paper_id = get_paper_hash(content)

    # if paper_id in reviewed_papers_hashes:
    #     return f"ALERT: Paper {pdf_path} has already been reviewed"

    word_count = len(content.split())

    # RAG
    results = collection.query(query_texts=[content], n_results=2)
    rag_context = " | ".join(results['documents'][0])

    characters = {
        "substantive": "Focus purely on logic, the truth of the claims, and the validity of citations. Be an expert.",
        "hater": "You are biased towards a negative review. Be cynical, nitpick every small mistake, and be harsh.",
        "lazy": f"This paper has {word_count} words. You are bored. Provide a shallow, very short review. Mention the length.",
        "aesthete": "Focus on vocabulary, grammar, spelling, and the overall visual/linguistic flow of the paper."
    }

    system_instruction = f"You are a scientific reviewer. Your persona: {character_type.upper()}. {characters.get(character_type, '')}"

    full_prompt = f"""
    [RAG GUIDELINES]: 
    Use these standards if applicable: {rag_context}

    [ARTICLE CONTENT]: 
    {content[:10000]}

    [TASK]: 
    Write a review as your character. Be specific to the content of the article above.
    """

    response = ollama.chat(model='llama3.1', messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': full_prompt},
    ])

    return response['message']['content']


my_paper = "17_A_fast_algorithm_to_compute.pdf"

try:
    print(write_review(my_paper, "substantive"))
    print("\n")
    print(write_review(my_paper, "hater"))
    print("\n")
    print(write_review(my_paper, "lazy"))

except Exception as e:
    print(f"Error: {e}")