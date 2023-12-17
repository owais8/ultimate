from flask import Flask, render_template, request, Response
import openai
import re
from openai import OpenAI


app = Flask(__name__)

# Replace 'YOUR_API_KEY' with your actual GPT-3 API key
api_key = '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'
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

@app.route('/generate_audio')
def generate_audio():
    your_openai_key = 'sk-...'
    your_text = 'Finxter helps you stay on the right side of change!'

    client = openai.OpenAI(api_key=api_key)

    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",  # other voices: 'echo', 'fable', 'onyx', 'nova', 'shimmer'
        input=your_text
    )

    def generate():
        yield response.content

    return Response(generate(), content_type='audio/mp3')


if __name__ == '__main__':
    app.run(debug=True)
