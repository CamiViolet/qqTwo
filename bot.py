# Script: qqone_bot.py
# Description: bot.


import dynamic_context
import google.genai as genai
import os
import sys
from dotenv import load_dotenv
from mistralai import Mistral
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters




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


if __name__ == '__main__':


# Load environment variables from .env file
load_dotenv()


# Inizializza il client Mistral
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# Inizializza il client Gemini
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Inizializza il client OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("check", command_check))
    app.add_handler(CommandHandler("quit", command_quit))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot collegato, in ascolto...")
    app.run_polling()

# import pdb; pdb.set_trace()
