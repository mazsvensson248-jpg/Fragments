from flask import Flask, request, jsonify, send_from_directory
import os, re, subprocess
from gtts import gTTS
import whisper

app = Flask(__name__)

# Runtime folders
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

@app.route("/generate", methods=["POST"])
def generate():
    video = request.files.get("video")
    voice = request.files.get("voice")
    music = request.files.get("music")
    font = request.files.get("font")
    text = request.form.get("text", "").strip()

    if not video:
        return jsonify({"error":"No video uploaded"}), 400

    video_path = os.path.join("uploads", video.filename)
    video.save(video_path)

    # Generate voice if not provided
    if voice:
        voice_path = os.path.join("uploads", voice.filename)
        voice.save(voice_path)
    else:
        if not text:
            return jsonify({"error":"No voice or text provided"}), 400
        voice_path = os.path.join("uploads","voice_output.mp3")
        tts = gTTS(text=text, lang="en")
        tts.save(voice_path)

    # Whisper transcription
    model = whisper.load_model("tiny")  # smaller model for speed
    result = model.transcribe(voice_path, word_timestamps=True, language="en")
    segments = result["segments"]

    # Build drawtext filters
    def clean_for_ffmpeg(txt):
        return re.sub(r"[^a-zA-Z0-9,.?!' ]", "", txt)

    filters = ""
    font_part = f"fontfile='{font.filename}':" if font else "font='Courier':"
    for s in segments:
        for w in s.get("words", []):
            word = clean_for_ffmpeg(w["word"])
            start, end = w["start"], w["end"]
            filters += (
                f"drawtext={font_part}text='{word}':fontsize=60:"
                f"fontcolor=white:bordercolor=black:borderw=2:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,{start},{end})',"
            )
    filters = filters.rstrip(",")

    # Mix voice + music
    if music:
        music_path = os.path.join("uploads", music.filename)
        music.save(music_path)
        subprocess.run([
            "ffmpeg", "-y", "-i", voice_path, "-i", music_path,
            "-filter_complex",
            "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=first",
            "-c:a", "aac", "-b:a", "192k", "uploads/mixed.mp3"
        ])
        audio_input = "uploads/mixed.mp3"
    else:
        audio_input = voice_path

    # Render final video
    output_file = os.path.join("outputs", "final_video.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-i", audio_input,
        "-vf", filters, "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-c:a", "aac", "-shortest", output_file
    ]
    subprocess.run(cmd)

    return jsonify({"download_url": f"/download/{os.path.basename(output_file)}"})

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("outputs", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
