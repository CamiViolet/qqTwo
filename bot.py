# Script: bot.py
# Description: Bot Telegram.


# import dynamic_context
# import google.genai as genai
import argparse
import json
import os
import re
import sys
from dotenv import load_dotenv
from mistralai.client import Mistral
# from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters


config = None
ai_model = 'Mistral'
args = None

what = "(.+)"
spaces = r"\s+"

container = "(lista della spesa|shopping list|spesa)"
verb = "(aggiungi|metti|inserisci|segna|annota|includi|integra|scrivi|appunta" \
                   + "|aggiungere|mettere|inserire|segnare|annotare|includere|integrare|scrivere|appuntare)"
prep = "(nella|alla|sulla)"
regexes_str = []
regexes_str.append(["^" + spaces.join([verb, what, prep, container]) + "$", 1])  # "Aggiungi il latte alla lista della spesa"
regexes_str.append(["^" + spaces.join([prep, container, verb, what]) + "$", 3])  # "Alla lista della spesa aggiungi il latte"
regexes_str.append(["^" + spaces.join([verb, prep, container, what]) + "$", 3])  # "Aggiungi alla lista della spesa il latte"

regex_add_shopping = [[re.compile(p[0], re.IGNORECASE), p[1]] for p in regexes_str]

verb = "(togli|rimuovi|elimina|cancella|leva|depenna" \
     + "|togliere|rimuovere|eliminare|cancellare|levare|depennare)"
prep = "(dalla)"
regexes_str = []
regexes_str.append(["^" + spaces.join([verb, what, prep, container]) + "$", 1])  # "Togli il latte dalla lista della spesa"|
regexes_str.append(["^" + spaces.join([prep, container, verb, what]) + "$", 3])  # "Dalla lista della spesa togli il latte"|
regexes_str.append(["^" + spaces.join([verb, prep, container, what]) + "$", 3])  # "Togli dalla lista della spesa il latte"|

regex_remove_shopping = [[re.compile(p[0], re.IGNORECASE), p[1]] for p in regexes_str]


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


# async def command_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     msg = "VPS Bot Connected"
#     print(msg)
#     await update.message.reply_text(msg)
# 
# 
# async def command_quit(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     msg = "Stopping ..."
#     print(msg)
#     await update.message.reply_text(msg)
#     sys.exit(0)


async def async_msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Da usare quando connesso al bot Telegram '''
    
    user_text = update.message.text

    reply = msg_handler(user_text)

    await update.message.reply_text(reply)

    if user_text=="/quit":
        sys.exit(0)


def msg_handler(user_text):
    global ai_model, args

    # Commands -----------------------------------------------------------------

    # /check
    if user_text=="/check":
        if args.chat:
            reply = "Chat in modalità locale."
        else:
            reply = "VPS Bot Connected"

        return reply
    
    # /quit
    if user_text=="/quit" or user_text=="q":
        return "Stopping ..."
    
    # /help
    if user_text=="/help":
        reply = "Comandi disponibili:\n"
        reply += "/check - Verifica la connessione al bot\n"
        reply += "/quit o q - Ferma il bot\n"
        reply += "/ctx - Attiva l'uso del contesto dinamico\n"
        reply += "/gemini - Usa il modello Gemini\n"
        reply += "/openai - Usa il modello OpenAI\n"
        reply += "/mistral - Usa il modello Mistral\n"
        return reply

    # Shopping list ------------------------------------------------------------
  
    # Show the shopping list
    match = re.match(r"^lista della spesa$", user_text, re.IGNORECASE)
    if match:
        with open("shopping_list.txt", "r", encoding="utf-8") as f:
            items = f.readlines()
        if items:
            return "Lista della spesa:\n" + "".join(items)
        else:
            return "La lista della spesa è vuota."
     
    # Add to shopping list
    # user_text = "Aggiungi il latte alla lista della spesa"
    # import pdb; pdb.set_trace()
    for regex, group_index in regex_add_shopping:
        match = regex.match(user_text)
        if match:
            what = match.group(1+group_index)
            with open("shopping_list.txt", "a", encoding="utf-8") as f:
                f.write(f"- {what}\n")
            return f"Elemento aggiunto alla lista della spesa: {what}"
        
    # Remove from shopping list
    for regex, group_index in regex_remove_shopping:
        match = regex.match(user_text)
        if match:
            what = match.group(1+group_index)
            with open("shopping_list.txt", "r", encoding="utf-8") as f:
                items = f.readlines()
            with open("shopping_list.txt", "w", encoding="utf-8") as f:
                for item in items:
                    if item.strip() != f"- {what}":
                        f.write(item)
            return f"Elemento rimosso dalla lista della spesa: {what}"
    
    return "Comando non riconosciuto. Digita /help per vedere i comandi disponibili."

    # LLM ----------------------------------------------------------------------

    use_context = False
    if "/ctx" in user_text:
        user_text = user_text.replace("/ctx", "")
        use_context = True
    
    if "/gemini" in user_text:
        user_text = user_text.replace("/gemini", "")
        ai_model = "Gemini"
    
    if "/openai" in user_text:
        user_text = user_text.replace("/openai", "")
        ai_model = "OpenAI"
    
    if "/mistral" in user_text:
        user_text = user_text.replace("/mistral", "")
        ai_model = "Mistral"
        
    if use_context:
        sys.argv = ['dynamic_context.py', '-v', "what is the feature about restructuring the CDs?", '-p', "biolog"]
        dynamic_context.main()
        context_text = load_context()
        import pdb; pdb.set_trace()

    if ai_model == "OpenAI":
        if use_context:
            prompt = f"Domanda: {user_text}\n\nContesto: {CONTEXT_TEXT}"
        else:
            prompt = f"Domanda: {user_text}"
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_reply = response.choices[0].message.content

        return ai_reply
    
    elif ai_model == "Gemini":
        # TODO: this will be discontinued by 01/06/2026: gemini-2.0-flash, gemini-2.0-flash-001, gemini-2.0-flash-lite, gemini-2.0-flash-lite-001
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

    elif ai_model == "Mistral":

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

        return ai_reply


def parse_arguments():
    parser = argparse.ArgumentParser(description="Bot Telegram.")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Activate chat mode instead of bot mode (default is bot mode)."
    )
    return parser.parse_args()


if __name__ == '__main__':
    sys.excepthook = excepthook

    args = parse_arguments()

    # Load environment variables from .env file
    load_dotenv()

    # Initialize the Mistral client
    mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    # Inizializza il client Gemini
    # gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Inizializza il client OpenAI
    # openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if args.chat:
        # Chat mode
        while True:
            user_text = input("Inserisci la tua domanda (o 'q' per uscire): ")
            reply = msg_handler(user_text)
            print(f"{reply}")
            if user_text.lower() in ["/quit", "quit", "q"]:
                sys.exit(0)


    # Bot mode (default)
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    # app.add_handler(CommandHandler("check", command_check))
    # app.add_handler(CommandHandler("quit", command_quit))
    app.add_handler(MessageHandler(filters.TEXT, async_msg_handler))
    print("Bot collegato, in ascolto...")
    app.run_polling()

# import pdb; pdb.set_trace()
