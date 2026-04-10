import os
import fitz  # PyMuPDF
import ollama
import chromadb
from PIL import Image
from langchain_community.document_loaders import PyPDFLoader
from analyze_image import analyze_visuals

client = chromadb.Client()
collection = client.get_or_create_collection(name="review_standards")

collection.add(
    documents=[
        "Methodology: A lack of a control group or small sample size is a major red flag.",
        "Citations: References older than 5 years without a seminal reason are considered outdated.",
        "Ethics: Any AI-based paper must disclose specific model versions and prompts.",
        "Aesthetics: Frequent typos and poor LaTeX formatting decrease credibility.",
        "Visualization: Plots must have labeled axes, units, and high contrast for accessibility."
    ],
    ids=["rule1", "rule2", "rule3", "rule4", "rule5"]
)

FEW_SHOT_EXAMPLES = {
    "substantive": [
        {
            "paper_snippet": "We achieve state-of-the-art results on the CIFAR-10 dataset using our modified Transformer block, outperforming the baseline by 0.5%.",
            "review_snippet": """
            Summary of Contribution: The authors propose a variation of the Transformer architecture for image classification.
            Strengths: The empirical results show a marginal improvement over the baseline.
            Weaknesses & Critical Flaws: 
            1. The significance of the 0.5% gain is questionable without a proper significance test (e.g., p-values or confidence intervals over multiple seeds). 
            2. CIFAR-10 is a saturated benchmark; to demonstrate SOTA, the authors should evaluate on larger datasets like ImageNet-1k. 
            3. The ablation study in Section 4.2 fails to isolate the effect of the new attention mask from the increased learning rate.
            """
        },
        {
            "paper_snippet": "The theoretical proof for the convergence of the algorithm is provided in the appendix under Theorem 3.1.",
            "review_snippet": """
            Technical Quality: I have concerns regarding the theoretical grounding. 
            Theorem 3.1 assumes the objective function is strongly convex, which is rarely the case for deep neural networks. 
            The authors must clarify how their convergence bounds hold in a non-convex setting or adjust their claims to reflect these restrictive assumptions.
            """
        }
    ],
    "hater": [
        {
            "paper_snippet": "We introduce 'NanoNet', a novel architecture designed for edge devices.",
            "review_snippet": """
            Novelty: The claim of novelty is overstated. NanoNet appears to be a straightforward combination of Depthwise Separable Convolutions (from MobileNet) and Squeeze-and-Excitation blocks. 
            The paper lacks a fundamental architectural breakthrough and feels like a marginal incremental update. 
            Recommendation: Reject. The contribution does not meet the bar for a top-tier conference.
            """
        },
        {
            "paper_snippet": "Our model was trained on 4 NVIDIA A100 GPUs for 48 hours.",
            "review_snippet": """
            Reproducibility: The authors mention the hardware but fail to provide the source code or specific hyperparameter grids. 
            Given the sensitivity of this method to the learning rate scheduler, the current description is insufficient for an independent reproduction of the results.
            """
        }
    ],
    "lazy": [
        {
            "paper_snippet": "Detailed analysis of 15 different hyperparameters and their cross-interactions...",
            "review_snippet": """
            General Impression: The paper is excessively long and dense. 
            While the hyperparameter analysis in Section 5 is thorough, it obscures the main message of the paper. 
            The authors should move the secondary plots to the Appendix to improve readability. Word count is excessive for a 10-page limit.
            """
        }
    ],
    "aesthete": [
        {
            "paper_snippet": "As seen in the results table below, the performance is better.",
            "review_snippet": """
            Clarity and Presentation: 
            1. Table 2 is missing units for the 'Latency' column. 
            2. The mathematical notation is inconsistent; the authors use both bold 'x' and italic 'x' for vectors in Equations 4 and 5. 
            3. Figures 2 and 3 are rasterized and become blurry when zoomed in; they should be replaced with vector graphics (PDF/SVG).
            """
        }
    ]
}


def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n".join([p.page_content for p in pages])


def write_review(pdf_path, character_type="substantive"):
    if not os.path.exists(pdf_path):
        return f"Error: File {pdf_path} not found."

    content = load_pdf(pdf_path)
    word_count = len(content.split())
    visual_report = analyze_visuals(pdf_path)

    results = collection.query(query_texts=[content], n_results=2)
    rag_context = " | ".join(results['documents'][0])

    examples = FEW_SHOT_EXAMPLES.get(character_type, [])
    examples_str = "".join(
        [f"\nExample Input: {ex['paper_snippet']}\nExample Review: {ex['review_snippet']}\n" for ex in examples])

    # Definicja Persony
    personas = {
        "substantive": "Focus purely on logic, the truth of the claims, and the validity of citations. Be an expert.",
        "hater": "You are biased towards a negative review. Be cynical, nitpick every small mistake, and be harsh.",
        "lazy": f"This paper has {word_count} words. You are bored. Provide a shallow, very short review. Mention the length.",
        "aesthete": "Focus on vocabulary, grammar, spelling, and the overall visual/linguistic flow of the paper."
    }

    system_instruction = f"You are a scientific reviewer. Persona: {character_type.upper()}. {personas.get(character_type, '')}"

    full_prompt = f"""
    [RAG GUIDELINES]:
    {rag_context}

    [FEW-SHOT EXAMPLES]:
    {examples_str}

    [VISUAL ANALYSIS REPORT]:
    {visual_report}

    [ACTUAL ARTICLE CONTENT (TRUNCATED)]:
    {content[:10000]}

    [TASK]:
    Write a review for the ACTUAL article content above. 
    Use the visual analysis to comment on figures. 
    Maintain the style shown in the few-shot examples.
    """

    response = ollama.chat(model='llama3.1', messages=[
        {'role': 'system', 'content': system_instruction},
        {'role': 'user', 'content': full_prompt},
    ])

    return response['message']['content']


if __name__ == "__main__":
    my_paper = "C:\\Users\\malwi\\ai_review\\openreview_data\\eUgS9Ig8JG_SaNN__Simple_Yet_Powerful_Simplicial_aware_Neural_Networks\\paper.pdf"

    try:
        print(write_review(my_paper, "substantive"))
        print("\n")
        print(write_review(my_paper, "hater"))
        print("\n")
        print(write_review(my_paper, "lazy"))

    except Exception as e:
        print(f"Error: {e}")