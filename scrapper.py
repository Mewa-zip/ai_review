import openreview
import os
import requests
import json

CONFERENCE_ID = 'ICLR.cc/2024/Conference'
LIMIT = 2
SAVE_DIR = "openreview_data"

USERNAME = XXXXXXXXX
PASSWORD = XXXXXXXXX

client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=USERNAME,
    password=PASSWORD
)



def download_data():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print(f"Pobieranie zgłoszeń z {CONFERENCE_ID}...")

    submissions = client.get_notes(invitation=f'{CONFERENCE_ID}/-/Submission', limit=LIMIT)

    for i, paper in enumerate(submissions):
        paper_id = paper.id
        content = paper.content
        title = content.get('title', {}).get('value', 'Untitled').replace(" ", "_")[:50]

        paper_folder = os.path.join(SAVE_DIR, f"paper_{i}_{paper_id}")
        if not os.path.exists(paper_folder):
            os.makedirs(paper_folder)

        print(f"[{i + 1}/{LIMIT}] Przetwarzanie: {title}...")

        pdf_path = os.path.join(paper_folder, "paper.pdf")
        pdf_url = f"https://openreview.net/pdf?id={paper_id}"

        try:
            r = requests.get(pdf_url)
            with open(pdf_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            print(f"   Błąd pobierania PDF: {e}")

        replies = client.get_notes(forum=paper_id)
        reviews = []

        for reply in replies:
            if 'Official_Review' in reply.invitation:
                # Wyciąganie tekstu recenzji i oceny w formacie v2
                rev_content = reply.content
                review_text = rev_content.get('review', {}).get('value', '')
                rating = rev_content.get('rating', {}).get('value', 'N/A')

                reviews.append({
                    "reviewer_id": reply.signatures[0],
                    "rating": rating,
                    "content": review_text
                })

        with open(os.path.join(paper_folder, "reviews.json"), "w", encoding="utf-8") as f:
            json.dump(reviews, f, indent=4, ensure_ascii=False)

        print(f"   Zapisano PDF i {len(reviews)} recenzji.")


if __name__ == "__main__":
    download_data()