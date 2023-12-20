from flask import Flask, render_template, request,jsonify, Response
import openai
import re
from openai import OpenAI
import requests
import time

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
        questions_prompt = f"generate short child like sentences starting with 'I want to talk about' regarding {selected_topic}"
        questions_response = openai.completions.create(
            model=engine_name,
            prompt=questions_prompt,
            max_tokens=300,
            temperature=0.7
        )

        # Extract generated questions
        generated_questions = [choice.text for choice in questions_response.choices]
        questions = re.findall(r'\d+\.\s(.+)', generated_questions[0])        # Translate the generated questions to the selected language
        translated_questions = []
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

        print(translated_questions)
        return render_template('questions.html', selected_language=selected_language, selected_topic=selected_topic, generated_questions=questions, translated_questions=translated_questions)

@app.route('/generate_audio',methods=['POST'])
def generate_audio():
    your_text=request.json.get('question')
    your_openai_key = 'sk-...'
    client = openai.OpenAI(api_key=api_key)

    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",  # other voices: 'echo', 'fable', 'onyx', 'nova', 'shimmer'
        input=your_text
    )
    filename='file.mp3'
    response.stream_to_file('file.mp3')
    with open(filename, "rb") as f:
        file_data = f.read()
    api_endpoint = 'https://filebin.net/xwgr3m8ib19cpxze/file.mp3'

    # Set the headers, including the content type as 'application/octet-stream'
    headers = {'Content-Type': 'application/octet-stream'}

    # Make the POST request with the file content as the request body
    response = requests.post(api_endpoint, data=file_data, headers=headers)


    # Check the response
    if response.status_code == 200:
        print('File uploaded successfully.')
    url = 'https://api.d-id.com/talks'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic b3dhaXNvcmFremFpNDg3N0BnbWFpbC5jb20:qMXpU3eSf03OJGDVShI1a'  # Replace with your actual authorization token
    }

    data = {
        "source_url": "https://create-images-results.d-id.com/google-oauth2%7C105476171628858848735/upl_xL40AqNRGuJnMfbwya0q_/image.jpeg",
        "script": {
            "type": "audio",
            "audio_url": "https://filebin.net/xwgr3m8ib19cpxze/file.mp3"
        }
    }

    response = requests.post(url, json=data, headers=headers)
    response = response.json()
    id=response['id']
    max_retries = 30
    retry_delay_seconds = 3
    print(id)
    for attempt in range(1, max_retries + 1):
        url='https://api.d-id.com/talks/'+id
        response=requests.get(url=url,headers=headers)

        if response.status_code == 200:
            response_json = response.json()
            pending_result = response_json.get('pending_result')

            if pending_result:
                print(f"Attempt {attempt}: Processing in progress. Sleeping...")
                time.sleep(retry_delay_seconds)
            else:
                result_url = response_json.get('result_url')

                if result_url:

                    print(f"Processing completed. Result URL: {result_url}")
                    return jsonify({'video_url': result_url})

                else:
                    print(f"Attempt {attempt}: Result URL not yet available. Current result URL: {result_url}")
        else:
            print(f"Attempt {attempt}: Failed to retrieve status. Status code: {response.status_code}")
            return Response('Error')


    return Response(response)

def generate_engaging(text,language):
    engine_name = 'gpt-3.5-turbo-instruct'

    # Generate questions based on the selected topic
    questions_prompt = f"generate engaging questions for a chat app using this context '{text}' to keep conversation going"
    questions_response = openai.completions.create(
        model=engine_name,
        prompt=questions_prompt,
        max_tokens=300,
        temperature=0.7
    )

    # Extract generated questions
    generated_questions = [choice.text for choice in questions_response.choices]
    questions = re.findall(r'\d+\.\s(.+)', generated_questions[0])        # Translate the generated questions to the selected language
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
    audio_file = request.files['file']
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



if __name__ == '__main__':
    app.run(debug=True)
