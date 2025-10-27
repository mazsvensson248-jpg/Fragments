import os
import re
from flask import Flask, request, send_file, render_template
import whisper
import tempfile

app = Flask(__name__)

# Load Whisper tiny once (fits free plan RAM)
model = whisper.load_model("tiny")

def clean_for_ffmpeg(text):
    return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_video():
    """
    Expects multipart/form-data:
    - video: .mp4
    - voice: .mp3 (required)
    - music: .mp3 (optional)
    - text: optional prompt
    """
    files = request.files
    video_file = files.get("video")
    voice_file = files.get("voice")  # required
    music_file = files.get("music")
    text = request.form.get("text", "")

    if not video_file or not voice_file:
        return "❌ Video and voice files are required", 400

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.mp4")
        video_file.save(video_path)

        voice_path = os.path.join(tmpdir, "voice.mp3")
        voice_file.save(voice_path)

        # Transcribe with Whisper tiny
        result = model.transcribe(voice_path, word_timestamps=True, language="en")
        segments = result["segments"]

        # Build drawtext filters with default Courier font
        filters = ""
        font_part = "font='Courier':"

        for segment in segments:
            for word_info in segment.get("words", []):
                word = clean_for_ffmpeg(word_info["word"])
                start = word_info["start"]
                end = word_info["end"]
                filters += (
                    f"drawtext={font_part}text='{word}':"
                    f"fontsize=48:fontcolor=white:bordercolor=black:borderw=2:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2:"
                    f"enable='between(t,{start},{end})',"
                )
        filters = filters.rstrip(",")

        # Mix audio if music provided
        if music_file:
            music_path = os.path.join(tmpdir, "music.mp3")
            music_file.save(music_path)
            mixed_audio = os.path.join(tmpdir, "mixed_audio.mp3")
            os.system(f"""ffmpeg -y -i "{voice_path}" -i "{music_path}" \
-filter_complex "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=3" \
-c:a aac -b:a 192k "{mixed_audio}" """)
            audio_input = mixed_audio
        else:
            audio_input = voice_path

        # Render final 720p video
        output_file = os.path.join(tmpdir, "final_video_720p.mp4")
        cmd = f"""ffmpeg -y -i "{video_path}" -i "{audio_input}" \
-vf "scale=1280:720,{filters}" -map 0:v -map 1:a \
-c:v libx264 -c:a aac -shortest "{output_file}" """
        exit_code = os.system(cmd)
        if exit_code != 0 or not os.path.exists(output_file):
            return "❌ Failed to create video", 500

        return send_file(output_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
