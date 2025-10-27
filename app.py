import gradio as gr
import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import tempfile

# Mock video generator function
def generate_video(prompt, voice_file):
    try:
        # Step 1: Pick a stock video from local folder or URL (mock)
        # For Hugging Face demo, we'll use a placeholder clip
        video_path = "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"

        # Step 2: Download temp video
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        os.system(f"wget -q -O {temp_video.name} {video_path}")

        # Step 3: Add user voice file to video
        video = VideoFileClip(temp_video.name)
        voice = AudioFileClip(voice_file)

        # Ensure duration fits
        min_duration = min(video.duration, voice.duration)
        video = video.subclip(0, min_duration)
        voice = voice.subclip(0, min_duration)

        # Combine
        final = video.set_audio(voice)

        # Step 4: Save final video
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, bitrate="1M")

        return output_path
    except Exception as e:
        return f"Error: {e}"

# Gradio UI
demo = gr.Interface(
    fn=generate_video,
    inputs=[
        gr.Textbox(label="🎬 Video Prompt", placeholder="Describe your video idea..."),
        gr.Audio(label="🎤 Upload Voice File", type="filepath"),
    ],
    outputs=gr.Video(label="📽️ Generated Video"),
    title="FRAGMENTS — AI Video Generator",
    description="Upload your voice and write a prompt to generate a 720p video clip.",
)

if __name__ == "__main__":
    demo.launch()
