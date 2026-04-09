import openreview
import os
import time

# --- CONFIGURATION ---
USERNAME = "XXXXXXXXXXXXX"
PASSWORD = "XXXXXXXXXXXXX"
VENUE_ID = 'ICLR.cc/2024/Conference'
DOWNLOAD_DIR = 'openreview_data'
LIMIT = 2

# Initialize authenticated client
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=USERNAME,
    password=PASSWORD
)


def scrape_papers():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    print(f"Fetching papers for {VENUE_ID}...")
    submissions = client.get_notes(content={'venueid': VENUE_ID}, limit=LIMIT)

    for paper in submissions:
        paper_id = paper.id
        title_val = paper.content.get('title', {}).get('value', 'Untitled')

        clean_title = "".join([c if c.isalnum() else "_" for c in title_val])[:60]
        paper_folder = os.path.join(DOWNLOAD_DIR, f"{paper_id}_{clean_title}")

        if not os.path.exists(paper_folder):
            os.makedirs(paper_folder)

        print(f"\nProcessing: {title_val}")

        pdf_path = os.path.join(paper_folder, "paper.pdf")
        if not os.path.exists(pdf_path):
            try:
                pdf_binary = client.get_pdf(id=paper_id)
                with open(pdf_path, "wb") as f:
                    f.write(pdf_binary)
                print(f"PDF saved.")
            except Exception as e:
                print(f"PDF error: {e}")

        try:
            replies = client.get_all_notes(forum=paper_id)
            review_count = 0

            for note in replies:
                invit = note.invitations[0] if note.invitations else ""
                if 'Official_Review' in invit:
                    review_count += 1
                    review_path = os.path.join(paper_folder, f"review_{review_count}.txt")

                    content = note.content
                    rating = content.get('rating', {}).get('value', 'N/A')
                    confidence = content.get('confidence', {}).get('value', 'N/A')
                    review_text = content.get('review', {}).get('value', 'No text')

                    with open(review_path, "w", encoding="utf-8") as rf:
                        rf.write(f"Rating: {rating}\n")
                        rf.write(f"Confidence: {confidence}\n")
                        rf.write("-" * 20 + "\n\n")
                        rf.write(review_text)

            print(f"{review_count} reviews saved.")
        except Exception as e:
            print(f"Review error: {e}")

        # avoid hitting rate limits
        time.sleep(1)


if __name__ == "__main__":
    scrape_papers()