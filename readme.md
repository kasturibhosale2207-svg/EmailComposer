# AI Email Composer Pro

**Write complete emails instantly with AI!**  
A free, no‑API‑key‑required NVDA add‑on that turns your plain‑language instructions into professional emails.

[![NVDA Add‑on Store](https://img.shields.io/badge/NVDA-Add‑on%20Store-blue)](https://www.nvaccess.org/addonStore/)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

---

## ✨ Features

- **Instant email generation** – type simple instructions, press `NVDA+Shift+G` to copy them and generate a subject, then `NVDA+Shift+H` to produce a complete email.
- **22+ languages** – English, Hindi, Marathi, Spanish, French, German, Chinese, Japanese, Arabic, Russian, Portuguese, Italian, Turkish, Korean, Dutch, Polish, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam.
- **Multiple tones** – Professional, Friendly, Formal, Casual, Persuasive, Apologetic, Thankful.
- **Customisable length** – Short (50‑100 words), Medium (100‑200), Long (200‑300), Detailed (300‑500).
- **Translation** – select any text and press `NVDA+Shift+T` to translate it to your chosen language.
- **Text refinement** – select text, press `NVDA+Shift+J`, and choose to Summarise, Fix Grammar, or Explain.
- **Composer dialog** – open a full‑featured email composer with `NVDA+Shift+K`.
- **Built‑in donation dialog** – support the developer via UPI with a generated QR code (requires qrcode library).
- **100% free AI service** – powered by Pollinations.AI – no account, no API key, no hidden costs.

---

## 📦 Installation

1. Download the latest `.nvda-addon` file from the [Releases](https://github.com/yourusername/emailComposer/releases) page.
2. Open the file, or use NVDA's **Tools → Manage Add‑ons → Install**.
3. Follow the prompts and restart NVDA.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `NVDA+Shift+G` | Copy current instructions to clipboard **and** generate a subject line (auto‑pasted). |
| `NVDA+Shift+H` | Generate a full email from the instructions in your clipboard (auto‑pasted to the message body). |
| `NVDA+Shift+T` | Translate the selected text (shows result in a window with copy button). |
| `NVDA+Shift+J` | Refine selected text – summarise, fix grammar, or explain. |
| `NVDA+Shift+K` | Open the Email Composer dialog for more control (language, tone, length, signature). |

---

## 🚀 Quick Start

1. **In your email client (Outlook, Thunderbird, Gmail, etc.):**
2. Type your instructions in the **Subject** field, e.g.:  
   *“write a polite email to my manager Priya requesting leave for tomorrow”*
3. Press `NVDA+Shift+G` – the instructions are copied to clipboard and a subject is generated.
4. Press `Tab` to move to the message body.
5. Press `NVDA+Shift+H` – a full email is generated and pasted directly!

---

## 🌐 Supported Languages

| Language | Code | Language | Code |
|----------|------|----------|------|
| English | `en` | Hindi | `hi` |
| Marathi | `mr` | Spanish | `es` |
| French | `fr` | German | `de` |
| Chinese | `zh` | Japanese | `ja` |
| Arabic | `ar` | Russian | `ru` |
| Portuguese | `pt` | Italian | `it` |
| Turkish | `tr` | Korean | `ko` |
| Dutch | `nl` | Polish | `pl` |
| Bengali | `bn` | Tamil | `ta` |
| Telugu | `te` | Gujarati | `gu` |
| Kannada | `kn` | Malayalam | `ml` |

---

## 🎨 Email Length & Tone Options

### Length
- **Short** – 50–100 words  
- **Medium** – 100–200 words  
- **Long** – 200–300 words  
- **Detailed** – 300–500 words  

### Tone
- Professional  
- Friendly  
- Formal  
- Casual  
- Persuasive  
- Apologetic  
- Thankful  

---

## ❤️ Support Development

This add‑on is **completely free** and always will be.  
If you find it useful, consider supporting the development:

- **UPI ID**: `bhosalekasturi694@oksbi`  
- **QR Code**: available inside the add‑on (Tools → AI Email Composer → Donate/Support).

Your support helps me add new features, fix bugs, and keep the add‑on accessible to everyone.

---

## ⚙️ Requirements

- NVDA **2023.1** or later.
- Windows 10 / 11.
- An active internet connection (the AI service is cloud‑based).

---

## 🛠️ Development & Building

### Prerequisites
- Python 3.10+ (for build tools).
- SCons (optional, for official add‑on packaging).
- qrcode and Pillow (if you want to test QR generation locally).

### Build steps

#### Option 1 – SCons (recommended for release)
```cmd
cd emailComposer
scons