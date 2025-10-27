import gradio as gr
from pytube import YouTube
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import tempfile
import os

MAX_DURATION = 70  # 1 minute 10 seconds

# --- Download YouTube videos ---
def download_youtube_videos(video_links):
    clips = []
    for url in video_links:
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            stream.download(output_path=os.path.dirname(temp_file.name), filename=os.path.basename(temp_file.name))
            clip = VideoFileClip(temp_file.name).resize(height=1080)
            clips.append(clip.subclip(0, min(clip.duration, MAX_DURATION)))
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    return clips

# --- Generate final video ---
def generate_video(prompt, voice_file, video_links):
    clips = download_youtube_videos(video_links)
    if not clips:
        return None
    final_clip = concatenate_videoclips(clips)
    final_clip = final_clip.subclip(0, min(final_clip.duration, MAX_DURATION))
    voice = AudioFileClip(voice_file).subclip(0, min(final_clip.duration, MAX_DURATION))
    final_clip = final_clip.set_audio(voice)
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, bitrate="4M")
    return output_path

# --- Gradio Interface ---
with gr.Blocks() as demo:
    gr.Markdown("## 🎬 FRAGMENTS — AI Video Generator (1min10sec max)")

    prompt_input = gr.Textbox(label="Video Prompt", placeholder="Describe your video...")
    voice_input = gr.Audio(label="Upload Voice File (.mp3/.wav)", type="filepath")
    youtube_checkbox = gr.CheckboxGroup(
        label="Select YouTube Videos",
        choices=[
            "https://youtu.be/tCBOhczn6Ok",
            "https://youtu.be/-LZceM7L8AE",
            "https://youtu.be/7mTTdWTw5p0",
            "https://youtu.be/_A3po0HYwkY",
            "https://youtu.be/-yPjP85CbQE",
            "https://youtu.be/_-2ZUciZgls",
            "https://youtu.be/t_r-ST06jR4",
            "https://youtu.be/s600FYgI5-s",
            "https://youtu.be/952ILTHDgC4",
            "https://youtu.be/u7kdVe8q5zs"
        ]
    )

    generate_btn = gr.Button("Generate")

    # Loading bar HTML
    loading_html = gr.HTML(
        """
        <div id="loading-bar" style="position:relative;width:100%;height:8px;background:#444;border-radius:4px;margin-top:10px;display:none;">
            <div style="
                position:absolute;
                width:20px;
                height:20px;
                border-radius:50%;
                background:limegreen;
                top:-6px;
                animation: move 1s infinite alternate;">
            </div>
        </div>
        <style>
        @keyframes move {
            0% { left:0; }
            100% { left:calc(100% - 20px); }
        }
        </style>
        """
    )

    file_output = gr.File(label="Downloading video...")

    # Generate click
    def run_generate(prompt, voice_file, video_links):
        return generate_video(prompt, voice_file, video_links)

    generate_btn.click(
        run_generate,
        inputs=[prompt_input, voice_input, youtube_checkbox],
        outputs=file_output,
        _js="""
        () => {
            const bar = document.getElementById('loading-bar');
            bar.style.display = 'block';
            this.innerText = 'Generating...';
            return;
        }
        """
    )

    demo.append(loading_html)

demo.launch()
