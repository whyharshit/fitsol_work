from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
import re

def get_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def save_as_text(text, filename="transcript.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Successfully saved to {filename}")

def save_as_pdf(text, filename="transcript.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12) # Use Helvetica as a safer default
    
    # Clean text to avoid encoding errors in PDF
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=clean_text)
    pdf.output(filename)
    print(f"✅ Successfully saved to {filename}")

def main():
    video_url = input("Enter YouTube URL: ").strip()
    video_id = get_video_id(video_url)
    
    if not video_id:
        print("❌ Invalid URL.")
        return

    try:
        print(f"Fetching transcript for ID: {video_id}...")
        
        # New recommended way to fetch
        # This will try to fetch the transcript directly
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        full_text = " ".join([item['text'] for item in transcript_list])
        
        save_as_text(full_text)
        save_as_pdf(full_text)
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        print("\nTip: If you still see 'no attribute', run: pip install --upgrade youtube-transcript-api")

if __name__ == "__main__":
    main()