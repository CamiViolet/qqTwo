# Script: chat.py
# Description: Create a dynamic context (1bf - One Big File).
# Usage: python dynamic_context.py pattern
#
# Parameters:
#   pattern - String to be searched (regex)
#
# Examples:
#   python chat.py "smoke tests" -p "smoke.?tests" 

import argparse
import json
import os
import glob
import pyperclip
import re
import sys
from collections import defaultdict
from patterns import get_patterns
from dotenv import load_dotenv
import tempfile
from mistralai import Mistral
from openai import OpenAI
from google.genai import Client


common_words_to_ignore = ['shall', 'none', 'document', 'documentation', 'describe', 'described', 'describes']

config = None


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def load_json(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config





# Carica il contesto dal file
def load_context():
    context_file = os.path.join(TEMPORARY_DIR, 'dynamic_context', 'dynamic_context.1bf.txt')
    with open(context_file, 'r', encoding='utf-8') as f:
        content = f.read()
        return content


async def command_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "VPS Bot Connected"
    print(msg)
    await update.message.reply_text(msg)


async def command_quit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Stopping ..."
    print(msg)
    await update.message.reply_text(msg)
    sys.exit(0)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user_text = update.message.text
    
    use_context = False
    if "/ctx" in user_text:
        user_text = user_text.replace("/ctx", "")
        use_context = True
    
    use_gemini = False
    if "/gemini" in user_text:
        user_text = user_text.replace("/gemini", "")
        use_gemini = True
    
    use_openai = False
    if "/openai" in user_text:
        user_text = user_text.replace("/openai", "")
        use_openai = True
        
    if use_context:
        sys.argv = ['dynamic_context.py', '-v', "what is the feature about restructuring the CDs?", '-p', "biolog"]
        dynamic_context.main()
        context_text = load_context()
        import pdb; pdb.set_trace()

    if use_openai:
        if use_context:
            prompt = f"Domanda: {user_text}\n\nContesto: {CONTEXT_TEXT}"
        else:
            prompt = f"Domanda: {user_text}"
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_reply = response.choices[0].message.content
    elif use_gemini:
        if use_context:
            prompt = f"Domanda: {user_text}\n\nContesto: {CONTEXT_TEXT}"
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
        else:
            prompt = f"Domanda: {user_text}"
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
        
        ai_reply = response.text
    else:

        if use_context:
            chat_response = mistral_client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": f"Domanda: {user_text}\n\nContesto: {CONTEXT_TEXT}"}]
            )
        else:
            chat_response = mistral_client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": f"Domanda: {user_text}"}]
            )
        
        ai_reply = chat_response.choices[0].message.content

    await update.message.reply_text(ai_reply)



def parse_arguments():
    parser = argparse.ArgumentParser(description="Create a dynamic context by using the input parameter.")

    return parser.parse_args()


if __name__ == "__main__":

    sys.excepthook = excepthook

    args = parse_arguments()

    # Load environment variables from .env file
    load_dotenv()

    # Initialize the Mistral client
    mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    while True:
        user_question = input("Inserisci la tua domanda (o 'q' per uscire): ")
        if user_question.lower() == "q":
            print("Uscita dal programma.")
            break

        chat_response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": f"Domanda: {user_question}"}]
        )

        ai_reply = chat_response.choices[0].message.content

        print(f"Risposta AI: {ai_reply}")
