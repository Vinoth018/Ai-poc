# from flask import Flask, render_template, request, redirect, url_for, send_file
# import whisper
# from moviepy.editor import VideoFileClip, AudioFileClip
# from deep_translator import GoogleTranslator
# from gtts import gTTS
# from pydub import AudioSegment, silence
# import os

# app = Flask(__name__)

# # Load the Whisper model
# model = whisper.load_model("base")

# # Language choices for translation
# language_choices = {
#     'en': 'English', 
#     'es': 'Spanish',
#     'fr': 'French',
#     'de': 'German',
#     'hi': 'Hindi',
#     'ml': 'Malayalam',
#     'kn': 'Kannada',
#     'ta': 'Tamil',
#     'te': 'Telugu',
#     'mr': 'Marathi',
#     'bn': 'Bengali',
#     'ur': 'Urdu'
# }

# # Extract audio from a video
# def extract_audio(video_path, audio_path):
#     video_clip = VideoFileClip(video_path)
#     video_clip.audio.write_audiofile(audio_path)

# # Transcribe the extracted audio and detect language
# def transcribe_and_detect_language(audio_path):
#     result = model.transcribe(audio_path)
#     detected_language = result['language']
#     transcription = result['text']
#     return detected_language, transcription

# # Split audio into segments based on silence
# def split_audio_into_segments(audio_path, min_silence_len=700, silence_thresh=-40):
#     audio = AudioSegment.from_wav(audio_path)
#     segments = silence.split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
#     return segments

# # Translate text into a specified language
# def translate_text(text, target_lang):
#     translator = GoogleTranslator(source='auto', target=target_lang)
#     return translator.translate(text)

# # Convert text to speech in a specified language for a segment
# def text_to_speech_segment(text, lang, audio_output_path):
#     tts = gTTS(text=text, lang=lang)
#     tts.save(audio_output_path)

# # Replace the original audio with the translated audio in the video
# def replace_audio_with_translated_segments(video_path, audio_segments_paths, output_video_path):
#     video_clip = VideoFileClip(video_path)

#     combined_audio = AudioSegment.empty()
#     for segment_path in audio_segments_paths:
#         combined_audio += AudioSegment.from_file(segment_path)

#     combined_audio.export("translated_audio_combined.mp3", format="mp3")

#     audio_clip = AudioFileClip("translated_audio_combined.mp3")
#     final_video = video_clip.set_audio(audio_clip)
#     final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

# # Route for the homepage (upload video and select language)
# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         # Save the uploaded video
#         video_file = request.files["video"]
#         target_lang = request.form.get("language")
        
#         if video_file and target_lang:
#             video_path = os.path.join("static", video_file.filename)
#             video_file.save(video_path)
#             audio_path = "audio.wav"
            
#             # Extract audio and process it
#             extract_audio(video_path, audio_path)
#             detected_language, transcription = transcribe_and_detect_language(audio_path)

#             # Split the audio, translate, and convert to speech
#             audio_segments = split_audio_into_segments(audio_path)
#             if not os.path.exists('audio_segments'):
#                 os.makedirs('audio_segments')

#             translated_audio_paths = []
#             for i, segment in enumerate(audio_segments):
#                 segment_path = f'audio_segments/segment_{i}.wav'
#                 segment.export(segment_path, format='wav')

#                 translated_text = translate_text(transcription, target_lang)
#                 translated_segment_path = f'audio_segments/translated_segment_{i}.mp3'
#                 text_to_speech_segment(translated_text, target_lang, translated_segment_path)

#                 translated_audio_paths.append(translated_segment_path)

#             # Replace audio with translated audio
#             output_video_path = "static/output_video_with_translated_audio.mp4"
#             replace_audio_with_translated_segments(video_path, translated_audio_paths, output_video_path)

#             return redirect(url_for("result", video_path=output_video_path))

#     return render_template("index.html", languages=language_choices)

# # Route to display the result video
# @app.route("/result")
# def result():
#     video_path = request.args.get("video_path")
#     return render_template("result.html", video_path=video_path)

# if __name__ == "__main__":
#     app.run(debug=True)



from flask import Flask, render_template, request, redirect, url_for
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from deep_translator import GoogleTranslator
from gtts import gTTS
from pydub import AudioSegment
import os
import concurrent.futures

app = Flask(__name__)

# Load the Whisper model once at startup
model = whisper.load_model("tiny")

# Language choices for translation
language_choices = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'hi': 'Hindi',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'bn': 'Bengali',
    'ur': 'Urdu'
}

def extract_audio(video_path, audio_path):
    video_clip = VideoFileClip(video_path)
    video_clip.audio.write_audiofile(audio_path)

def transcribe_and_detect_language(audio_path):
    result = model.transcribe(audio_path)
    detected_language = result['language']
    transcription = result['text']
    return detected_language, transcription

def translate_text(text, target_lang):
    translator = GoogleTranslator(source='auto', target=target_lang)
    return translator.translate(text)

def text_to_speech(text, lang, output_path):
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)

def replace_audio_with_translated_audio(video_path, translated_audio_path, output_video_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(translated_audio_path)
    final_video = video_clip.set_audio(audio_clip)
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_file = request.files["video"]
        target_lang = request.form.get("language")
        
        if video_file and target_lang:
            video_path = os.path.join("static", video_file.filename)
            video_file.save(video_path)
            audio_path = "audio.wav"

            extract_audio(video_path, audio_path)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_transcription = executor.submit(transcribe_and_detect_language, audio_path)
                detected_language, transcription = future_transcription.result()

                future_translation = executor.submit(translate_text, transcription, target_lang)
                translated_text = future_translation.result()

                translated_audio_path = "translated_audio.mp3"
                future_tts = executor.submit(text_to_speech, translated_text, target_lang, translated_audio_path)
                future_tts.result()

            output_video_path = "static/output_video_with_translated_audio.mp4"
            replace_audio_with_translated_audio(video_path, translated_audio_path, output_video_path)

            return redirect(url_for("result", video_path=output_video_path))

    return render_template("index.html", languages=language_choices)

@app.route("/result")
def result():
    video_path = request.args.get("video_path")
    return render_template("result.html", video_path=video_path)

if __name__ == "__main__":
    app.run(debug=True)
