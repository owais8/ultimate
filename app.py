from flask import Flask, render_template, request,jsonify, Response
import openai
import re
from openai import OpenAI
import subprocess
import shutil
import os

app = Flask(__name__)

# Replace 'YOUR_API_KEY' with your actual GPT-3 API key
api_key = ''
openai.api_key = api_key

languages = {
    'Russian': 'russian',
    'Spanish': 'spanish',
    'French': 'french',

    # Add more languages as needed
}

@app.route('/')
def index():
    return render_template('index.html', languages=languages.keys())

@app.route('/translate', methods=['POST'])
def translate():
    user_input = request.form.get('user_input')
    selected_language = request.form.get('selected_language')

    # Map the selected language to the corresponding GPT-3 engine name
    engine_name = 'gpt-3.5-turbo-instruct'

    prompt = f"translate this text to {selected_language.lower()}: {user_input}"

    response = openai.completions.create(
        model=engine_name,
        prompt=prompt,
        max_tokens=350,
        temperature=0.5
    )
    chatbot_response = response.choices[0].text
    return render_template('index.html', user_input=user_input, chatbot_response=chatbot_response, languages=languages.keys(), selected_language=selected_language)


@app.route('/generate_translate_questions', methods=['GET', 'POST'])
def generate_translate_questions():
    if request.method == 'GET':
        # Render the initial page
        return render_template('questions.html')

    elif request.method == 'POST':
        selected_language = request.form.get('language')
        selected_topic = request.form.get('topic')
        # Map the selected language to the corresponding GPT-3 engine name
        engine_name = 'gpt-3.5-turbo-instruct'

        # Generate questions based on the selected topic
        questions_prompt = f"generate text such as 'you wanted to talk about' {selected_topic}, followed by a simple question about {selected_topic} in single sentence and also generate 3 simple sentences as answer suggestions to the question which is asked"
        questions_response = openai.completions.create(
            model=engine_name,
            prompt=questions_prompt,
            max_tokens=300,
            temperature=0.7
        )
        print(questions_response)
        # Extract generated questions
        generated_questions = [choice.text for choice in questions_response.choices]
        questions = re.findall(r'"([^"]*)"', generated_questions[0])        # Translate the generated questions to the selected language
        translated_questions = []
        print("Hell",questions)

        for question in questions:
            translation_prompt = f"translate this text to {selected_language.lower()}: {question}"
            translation_response = openai.completions.create(
                model=engine_name,
                prompt=translation_prompt,
                max_tokens=350,
                temperature=0.5
            )
            translated_question = translation_response.choices[0].text

            translated_questions.append(translated_question)

        return render_template('questions.html', selected_language=selected_language, selected_topic=selected_topic, generated_questions=questions, translated_questions=translated_questions)

@app.route('/generate_audio',methods=['POST'])
def generate_audio():
    print('called')
    your_text=request.json.get('question')
    your_openai_key = 'sk-...'
    client = openai.OpenAI(api_key=api_key)

    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",  # other voices: 'echo', 'fable', 'onyx', 'nova', 'shimmer'
        input=your_text
    )
    filename='Wav2Lip/adio.wav'
    response.stream_to_file('Wav2Lip/adio.wav')
    with open(filename, "rb") as f:
        file_data = f.read()
    checkpoint_path = 'Wav2lip/checkpoints/wav2lip_gan.pth'
    video_path = 'Wav2lip/image.jpg'
    audio_source = 'Wav2lip/adio.wav'

    # Build the command string
    command = f"python Wav2lip/inference.py --checkpoint_path {checkpoint_path} --face {video_path} --audio {audio_source}"

    # Use subprocess to run the command
    try:
        subprocess.run(command, shell=True, check=True)
        source_file_path = 'Wav2lip/results/result_voice.mp4'

        # Specify the destination directory path
        destination_directory = 'static/'
        os.remove('static/result_voice.mp4')
        # Move the file
        shutil.move(source_file_path, destination_directory)

        return jsonify({'video_url':'static/result_voice.mp4'})
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return Response(e)

    


def generate_engaging(text,language):
    engine_name = 'gpt-3.5-turbo-instruct'

    # Generate questions based on the selected topic
    questions_prompt = f"generate text such as 'you wanted to talk about' {text}, followed by a simple engaging question about {text} in single sentence and also generate 3 simple and engaging sentences as answer suggestions to the question which is asked for chat app"
    questions_response = openai.completions.create(
        model=engine_name,
        prompt=questions_prompt,
        max_tokens=300,
        temperature=0.7
    )

    # Extract generated questions
    generated_questions = [choice.text for choice in questions_response.choices]
    questions = re.findall(r'"([^"]*)"', generated_questions[0])        # Translate the generated questions to the selected language
    translated_questions = []
    for question in questions:
        translation_prompt = f"translate this text to {language}: {question}"
        translation_response = openai.completions.create(
            model=engine_name,
            prompt=translation_prompt,
            max_tokens=350,
            temperature=0.5
        )
        translated_question = translation_response.choices[0].text

        translated_questions.append(translated_question)

    return questions,translated_questions


@app.route('/audio_processing',methods=['POST'])
def generate_text():
    client = openai.OpenAI(api_key=api_key)
    audio_file = request.files['audio_data']
    language = request.form.get('language')

    audio_file.save('f.mp3')
    with open('f.mp3', "rb") as f:
        transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=f
    )
    text=transcript.text
    print(language)
    questions,translated_questions=generate_engaging(text=text,language=language)
    print(translated_questions)
    return jsonify({'questions':questions,'translated_questions': translated_questions})


@app.route('/generate_new_questions',methods=['POST'])
def generate_new_questions():
    data = request.json
    clicked_question = data.get('clickedQuestion')
    language=data.get('language')
    questions,translated_questions=generate_engaging(text=clicked_question,language=language)
    return jsonify({'questions':questions,'translated_questions': translated_questions})

@app.route('/temp',methods=['POST'])
def tempp():
    checkpoint_path = 'Wav2lip/checkpoints/wav2lip_gan.pth'
    video_path = 'Wav2lip/image.jpg'
    audio_source = 'Wav2lip/adio.wav'

    # Build the command string
    command = f"python Wav2lip/inference.py --checkpoint_path {checkpoint_path} --face {video_path} --audio {audio_source}"

    # Use subprocess to run the command
    try:
        subprocess.run(command, shell=True, check=True)
        source_file_path = 'Wav2lip/results/result_voice.mp4'

        # Specify the destination directory path
        destination_directory = 'static/'

        # Move the file
        shutil.move(source_file_path, destination_directory)

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return 'hello'
if __name__ == '__main__':
    app.run(debug=True)
