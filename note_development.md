
### GitHub
    https://github.com/login
    carlo.camicia@gmail.com / CamiViolet

### Ionos (VPS provider)
    https://login.ionos.de/  
    camica@live.co.uk

### VPS
    putty.exe (Windows)
    ssh root@82.165.149.195
    root
    sudo apt update && sudo apt upgrade -y

### bash
    nano ~/.bashrc
    source ~/.bashrc

### venv
    python -m venv venv # per crearlo
    source venv/bin/activate    # su bash
    venv\Scripts\activate       # su Windows
    
### bot - debug
    source venv/bin/activate    # su bash
    venv\Scripts\activate       # su Windows
    python bot.py     # Avvio manuale, per test
    
### Telegram
    name: kb1_bot
    user name: @kb139_bot
    Comandi:
    /start
    
### Mistral
    carlo.camicia@gmail.com / <pwd by google>
    
### Gemini
    https://aistudio.google.com/

### OpenAI
    https://platform.openai.com/

### Per l'esecuzione automatica
    pm2 start chat.py --interpreter python3 --name qqone_bot
    pm2 list
    pm2 restart qqone_bot
    pm2 stop qqone_bot
    pm2 logs

### Per il trasferimento dei file
    pscp C:\Dev_TTT\DTech-20251226T145049Z-3-001\DTech_1bf\DTech.1bf.txt root@82.165.149.195:/qqone/DTech.1bf.txt
    pscp C:\Dev_TTT\qqOne\.env root@82.165.149.195:/qqone/.env
    pscp C:\Dev_TTT\qqOne\qqone_bot.py root@82.165.149.195:/qqone/qqone_bot.py

### Shortcuts
    opt+cmd up/down: seleziona per colonne
    cmd-K V: Preview Markdown