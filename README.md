# 🖱️ MouseChat Desktop

**MouseChat Desktop** is a lightweight, always-available AI assistant for Windows that lets you **select any text from any application**, press a hotkey, and instantly query your preferred AI model.  

Inspired by the "Ask ChatGPT" selection popup on the web, but designed to work **system-wide**.

---

## ✨ Features

- **System-wide text selection** → popup via hotkey (default: `Alt+Q` or `Ctrl+Q`, configurable)
- **Frameless floating chat window** with rounded corners & translucent background
- **Dark / Light theme toggle** 🌙 / ☀️ (persists across sessions)
- **Model dropdown** to select from multiple AI models (e.g., `gpt-4o`, `chatgpt-5`, `claude-3.5`, `gemini`, etc.)
- **Prompt history** recall with ↑ / ↓ keys
- **Copy button** to quickly copy AI responses
- **Clear input** button
- **Markdown-ready output area** (plain text for now, extensible)
- **Auto-focus and fade effect** when active/inactive
- **Movable floating panel** (click & drag anywhere in the frame)
- **Persistent window size, position, theme, and history** (via `QSettings`)
- **Custom API backend support** (OpenAI, OpenRouter, etc.)
- **No automatic popup** — hotkey-activated for minimal distraction

---

## 📦 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/MouseChat.git
cd MouseChat
```

### 2️⃣ Create a virtual environment
```bash
python -m venv .venv
```

### 3️⃣ Activate the environment
- **Windows PowerShell**
```powershell
.venv\Scripts\activate
```
- **Command Prompt**
```cmd
.venv\Scripts\activate.bat
```

### 4️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

Example `requirements.txt`:
```
PyQt6
pyperclip
keyboard
openai
requests
python-dotenv
```

---

## ⚙️ Configuration

### API Key

MouseChat can work with **OpenAI** or **OpenRouter**.

- **OpenAI**
```powershell
setx OPENAI_API_KEY "your_openai_api_key"
```

- **OpenRouter**
```powershell
setx OPENROUTER_API_KEY "your_openrouter_api_key"
```

Restart your terminal after setting the key.

---

### Default Model
Default model is set in `main.py`:
```python
DEFAULT_MODEL = "chatgpt-5"
```
Change to any model your backend supports.

---

## 🖥️ Usage

1. **Select text** anywhere (browser, Word, PDF, code editor…)
2. Press **Alt+Q** (or your chosen hotkey)
3. A small **Ask ChatGPT** chip appears near the cursor
4. Click the chip → floating **chat window** opens with your selection pre-filled
5. Add extra context if needed, then:
   - Press **Ctrl+Enter** or click **Send**
   - Output appears below
6. Use:
   - **↑ / ↓ keys** to navigate past prompts
   - **Copy** to copy AI response
   - **Clear** to clear the input field
   - **Theme toggle** 🌙 / ☀️ to switch themes
   - **Model dropdown** to switch AI model

---

## 🎛️ UI Overview

| Component         | Function |
|-------------------|----------|
| **Model dropdown** | Select active AI model |
| **Theme toggle** 🌙/☀️ | Switch between dark and light mode |
| **Close** ✕ | Hide window |
| **Input box** | Add prompt or edit selected text |
| **Send** | Send to AI |
| **Copy** | Copy AI response |
| **Clear input** | Clear the input text box |
| **Output box** | Shows model response |

---

## ⌨️ Hotkeys

| Hotkey | Action |
|--------|--------|
| `Alt+Q` / `Ctrl+Q` | Show/hide Ask chip |
| `Ctrl+Enter` | Send prompt |
| `Ctrl+C` | Copy AI response |
| `↑ / ↓` | Navigate prompt history |
| `Esc` | Close chat window |

---

## 🛠️ Development

### Project structure:
```
MouseChat/
│
├── mousechat/
│   ├── main.py        # Entry point / hotkey listener
│   ├── overlay.py     # Small popup chip near cursor
│   ├── chatwin.py     # Chat window UI
│   ├── selection.py   # Selected text extraction
│   ├── llm.py         # API calls (OpenAI/OpenRouter)
│
├── requirements.txt
├── README.md
```

Run in development mode:
```bash
python -m mousechat.main
```

---

## 🚀 Roadmap

- [ ] **Markdown rendering** with syntax highlighting in responses
- [ ] **Multi-turn conversations** with context carry-over
- [ ] **Quick-actions** (Summarize, Translate, Explain, etc.)
- [ ] **Configurable hotkeys** from UI
- [ ] **Linux & MacOS support** (current selection code is Windows-specific)

---

## 📝 License
MIT License – do whatever you want, just credit the project.

---

## 💡 Tip
Best for:
- Quickly rewording sentences in Word or PDF
- Asking programming questions while coding
- Translating text in any app
- Getting explanations for selected error messages

---

Made with GPT 5
