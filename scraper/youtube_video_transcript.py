from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF
import os

class VideoTranscript:
    def __init__(self, video_ids_file, output_directory, pdf_output_directory):
        self.video_ids_file = video_ids_file
        self.output_directory = output_directory
        self.pdf_output_directory = pdf_output_directory
        os.makedirs(output_directory, exist_ok=True)

    def load_video_ids(self):
        with open(self.video_ids_file, 'r', encoding='utf-8') as file:
            video_ids = file.readlines()
            video_ids = [video_id.strip().split('?v=')[1] for video_id in video_ids]
        return video_ids

    def fetch_transcript(self, video_id):
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['es'])
            transcript_data = transcript.fetch()
            text = ' '.join([item['text'] for item in transcript_data])
            return {'video_id': video_id, 'text': text}
        except Exception as e:
            print(f"Error fetching transcript for video {video_id}: {e}")
            return {'video_id': video_id, 'text': ''}

    def save_transcript_txt(self, transcript):
        file_path = os.path.join(self.output_directory, f"{transcript['video_id']}.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(f"URL: https://www.youtube.com/watch?v={transcript['video_id']}\n")
            file.write(f"Transcript:\n{transcript['text']}\n")
            file.write("\n" + "#"*25 + "\n")

    def save_transcript_pdf(self, transcript):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, f"URL: https://www.youtube.com/watch?v={transcript['video_id']}\n")
        pdf.multi_cell(0, 10, "Transcript:\n")
        pdf.multi_cell(0, 10, transcript['text'])

        file_path = os.path.join(self.pdf_output_directory, f"{transcript['video_id']}.pdf")
        pdf.output(file_path)

    def get_all_transcripts(self):
        video_ids = self.load_video_ids()
        all_transcripts = []
        for video_id in video_ids:
            transcript = self.fetch_transcript(video_id)
            all_transcripts.append(transcript)
            self.save_transcript_txt(transcript)
            self.save_transcript_pdf(transcript)
        return all_transcripts

if __name__ == '__main__':
    video_ids_file = 'data/raw/youtube_videos_urls.txt'  # Path to the file containing video URLs
    output_directory = 'data/processed/transcripts'
    pdf_output_directory = 'data/processed/pdf_files'
    video_transcript = VideoTranscript(video_ids_file, output_directory, pdf_output_directory)
    transcripts = video_transcript.get_all_transcripts()
    
    for transcript in transcripts:
        print(f"Saved transcript for Video ID: {transcript['video_id']}")
