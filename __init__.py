# -*- coding: utf-8 -*-
"""
Email Composer Pro - NVDA Add-on
Write complete emails instantly with AI!
Author: Kasturi Bhosale

Shortcuts:
- NVDA+Shift+G: Copy instructions to clipboard + generate subject (pastes in field)
- NVDA+Shift+H: Generate email from clipboard instructions (auto-pastes to body)
- NVDA+Shift+T: Translate selected text (shows in window with copy button)
- NVDA+Shift+J: Refine selected text
- NVDA+Shift+K: Open email composer dialog
"""

import sys
import os

# Add lib directory to Python path for external libraries (qrcode, PIL)
lib_path = os.path.join(os.path.dirname(__file__), "lib")
if os.path.exists(lib_path) and lib_path not in sys.path:
    sys.path.insert(0, lib_path)

import json
import threading
import logging
import re
import time
import wx
from urllib import request, error, parse

import addonHandler
import languageHandler
import globalPluginHandler
import globalVars
import config
import gui
import ui
import api
import textInfos
import tones
import NVDAObjects.behaviors
import scriptHandler
import winUser

log = logging.getLogger(__name__)
addonHandler.initTranslation()

ADDON_NAME = addonHandler.getCodeAddon().manifest["summary"]

# ============================================================================
# Constants and Configuration
# ============================================================================

EMAIL_TONES = {
    "professional": "Professional",
    "friendly": "Friendly",
    "formal": "Formal",
    "casual": "Casual",
    "persuasive": "Persuasive",
    "apologetic": "Apologetic",
    "thankful": "Thankful",
}

EMAIL_LENGTHS = {
    "short": _("Short (50-100 words)"),
    "medium": _("Medium (100-200 words)"),
    "long": _("Long (200-300 words)"),
    "detailed": _("Detailed (300-500 words)"),
}

LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "zh": "Chinese",
    "ja": "Japanese",
    "ar": "Arabic",
    "ru": "Russian",
    "pt": "Portuguese",
    "it": "Italian",
    "tr": "Turkish",
    "ko": "Korean",
    "nl": "Dutch",
    "pl": "Polish",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
}

confspec = {
    "target_language": "string(default='en')",
    "email_tone": "string(default='professional')",
    "email_length": "string(default='medium')",
    "include_signature": "boolean(default=False)",
    "signature_text": "string(default='Best regards,\\n[Your Name]')",
    "auto_paste": "boolean(default=True)",
    "translation_language": "string(default='en')",
}

config.conf.spec["EmailComposer"] = confspec

# ============================================================================
# Helper Functions
# ============================================================================

def send_ctrl_v():
    """Send Ctrl+V keystroke correctly."""
    try:
        winUser.keybd_event(0x11, 0, 0, 0)
        time.sleep(0.01)
        winUser.keybd_event(0x56, 0, 0, 0)
        time.sleep(0.01)
        winUser.keybd_event(0x56, 0, 2, 0)
        time.sleep(0.01)
        winUser.keybd_event(0x11, 0, 2, 0)
    except Exception as e:
        log.error(f"send_ctrl_v failed: {e}")


def send_ctrl_a():
    """Send Ctrl+A to select all text."""
    try:
        winUser.keybd_event(0x11, 0, 0, 0)
        time.sleep(0.01)
        winUser.keybd_event(0x41, 0, 0, 0)
        time.sleep(0.01)
        winUser.keybd_event(0x41, 0, 2, 0)
        time.sleep(0.01)
        winUser.keybd_event(0x11, 0, 2, 0)
    except:
        pass


def clean_markdown(text):
    """Clean markdown formatting from text."""
    if not text:
        return ""
    text = re.sub(r'\*\*|__|[*_]', '', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    return text.strip()


def get_focused_text():
    """Get text from currently focused element."""
    try:
        focus_obj = api.getFocusObject()
        if not focus_obj:
            return None
        
        if hasattr(focus_obj, 'value') and focus_obj.value:
            text = str(focus_obj.value).strip()
            if text:
                return text
        
        if hasattr(focus_obj, 'name') and focus_obj.name:
            text = str(focus_obj.name).strip()
            if text and text not in ["Subject", "To", "From", "CC", "BCC"]:
                return text
        
        try:
            info = focus_obj.makeTextInfo(textInfos.POSITION_ALL)
            if info and info.text:
                text = info.text.strip()
                if text:
                    return text
        except:
            pass
        
        return None
    except Exception as e:
        log.error(f"Error getting focused text: {e}")
        return None


def get_selected_text():
    """Get selected text for translation/refinement."""
    try:
        focus_obj = api.getFocusObject()
        if not focus_obj:
            return None
        
        # Try to get selected text
        try:
            info = focus_obj.makeTextInfo(textInfos.POSITION_SELECTION)
            if info and info.text:
                text = info.text.strip()
                if len(text) > 0:
                    return text
        except:
            pass
        
        # Fallback to all text
        try:
            info = focus_obj.makeTextInfo(textInfos.POSITION_ALL)
            if info and info.text:
                text = info.text.strip()
                if len(text) > 0:
                    return text
        except:
            pass
        
        return None
    except Exception as e:
        log.error(f"Error getting selected text: {e}")
        return None


def set_focused_text(text):
    """Set text in focused element (select all and paste)."""
    try:
        time.sleep(0.1)
        send_ctrl_a()
        time.sleep(0.1)
        api.copyToClip(text)
        time.sleep(0.1)
        send_ctrl_v()
        time.sleep(0.05)
        return True
    except Exception as e:
        log.error(f"Error setting focused text: {e}")
        return False


def copy_to_clipboard(text):
    """Copy text to clipboard only."""
    try:
        api.copyToClip(text)
        return True
    except Exception as e:
        log.error(f"Error copying to clipboard: {e}")
        return False


def show_result_window(title, content):
    """Show a window with the result and copy button."""
    try:
        dialog = wx.Dialog(None, title=title, size=(600, 450),
                          style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        
        panel = wx.Panel(dialog)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Text area
        text_ctrl = wx.TextCtrl(panel, value=content, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 350))
        sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        # Button sizer
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        copy_btn = wx.Button(panel, label="Copy to Clipboard")
        copy_btn.Bind(wx.EVT_BUTTON, lambda e: (api.copyToClip(content), ui.message("Copied to clipboard!")))
        btn_sizer.Add(copy_btn, 0, wx.ALL, 5)
        
        close_btn = wx.Button(panel, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: dialog.Close())
        btn_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        dialog.Centre()
        dialog.ShowModal()
        dialog.Destroy()
    except Exception as e:
        log.error(f"Error showing result window: {e}")
        ui.message(f"Result: {content[:200]}...")


def announce_and_beep(message, success=True):
    """Announce message and play beep."""
    wx.CallAfter(ui.message, message)
    if success:
        wx.CallAfter(tones.beep, 1000, 200)
    else:
        wx.CallAfter(tones.beep, 400, 300)

# ============================================================================
# AI Handler - Free Pollinations API
# ============================================================================

class FreeAIHandler:
    """Handles all AI operations using free Pollinations API."""
    
    @staticmethod
    def _call_api(prompt, max_retries=2):
        """Call Pollinations.AI API."""
        for attempt in range(max_retries):
            try:
                encoded_prompt = parse.quote(prompt[:2000])
                url = f"https://text.pollinations.ai/{encoded_prompt}"
                
                req = request.Request(url, method="GET")
                req.add_header("User-Agent", "EmailComposerPro/2.0")
                req.add_header("Accept", "text/plain")
                
                with request.urlopen(req, timeout=45) as response:
                    result = response.read().decode('utf-8')
                    if result and len(result) > 10:
                        return result.strip()
                    elif attempt == max_retries - 1:
                        return "ERROR: Empty response"
                    time.sleep(2)
                        
            except error.HTTPError as e:
                if e.code == 429 and attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                elif attempt == max_retries - 1:
                    return f"ERROR: Service unavailable (HTTP {e.code})"
            except error.URLError:
                if attempt == max_retries - 1:
                    return "ERROR: Cannot connect to AI service"
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"ERROR: {str(e)}"
        
        return "ERROR: All retries failed"
    
    @staticmethod
    def generate_subject_only(instructions):
        """Generate ONLY a subject line from instructions."""
        prompt = f"""Generate ONLY a professional email subject line based on these instructions.
Do NOT write an email. Do NOT add any extra text. Output ONLY the subject line.

Instructions: {instructions}

Subject:"""
        
        result = FreeAIHandler._call_api(prompt, max_retries=2)
        
        if result and not result.startswith("ERROR:"):
            result = clean_markdown(result)
            result = re.sub(r'^["\']|["\']$', '', result)
            result = re.sub(r'^(Subject:|Here is|Generated subject:|Subject line:)\s*', '', result, flags=re.IGNORECASE)
            result = result.split('\n\n')[0]
            result = result[:200]
            return result.strip()
        
        return "ERROR: Failed to generate subject"
    
    @staticmethod
    def generate_email_from_instructions(instructions):
        """Generate a complete email based on instructions."""
        if not instructions or len(instructions.strip()) < 10:
            return "ERROR: No valid instructions provided"
        
        lang_code = config.conf["EmailComposer"]["target_language"]
        language = LANGUAGES.get(lang_code, "English")
        
        tone = config.conf["EmailComposer"]["email_tone"]
        tone_name = EMAIL_TONES.get(tone, "Professional")
        
        length = config.conf["EmailComposer"]["email_length"]
        length_name = EMAIL_LENGTHS.get(length, "Medium (100-200 words)")
        
        signature = config.conf["EmailComposer"]["signature_text"] if \
                    config.conf["EmailComposer"]["include_signature"] else ""
        
        prompt = f"""Based on these instructions, write a complete email.

Instructions: {instructions}

Language: {language}
Tone: {tone_name}
Length: {length_name}

Requirements:
1. Follow the instructions carefully
2. Start with appropriate greeting
3. Write relevant body content
4. End with proper closing
5. Use professional language
6. Match the specified length

{signature}

Write ONLY the email content. Start directly with greeting.

Email:"""
        
        result = FreeAIHandler._call_api(prompt)
        
        if result and not result.startswith("ERROR:"):
            result = clean_markdown(result)
            result = re.sub(r'^Email:\s*', '', result, flags=re.IGNORECASE)
            
            # Ensure it starts with a greeting
            greetings = ["Dear", "Hello", "Hi", "Greetings", "To", "नमस्कार", "प्रिय"]
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if any(line.strip().startswith(g) for g in greetings):
                    if i > 0:
                        result = '\n'.join(lines[i:])
                    break
            
            return result
        
        return result if result else "ERROR: Failed to generate email"
    
    @staticmethod
    def translate_text(text):
        """Translate text to user's configured target language."""
        target_lang_code = config.conf["EmailComposer"]["translation_language"]
        target_lang_name = LANGUAGES.get(target_lang_code, "English")
        
        prompt = f"""Translate the following text to {target_lang_name} language.
Output ONLY the translation, nothing else.

Text to translate: {text[:1500]}

Translation:"""
        
        result = FreeAIHandler._call_api(prompt, max_retries=2)
        
        if result and not result.startswith("ERROR:"):
            result = clean_markdown(result)
            result = re.sub(r'^Translation:\s*', '', result, flags=re.IGNORECASE)
            return result.strip()
        
        return result if result else "ERROR: Failed to translate"
    
    @staticmethod
    def refine_text(text, action):
        """Refine text: summarize, fix grammar, or explain."""
        prompts = {
            "summarize": f"Summarize this text concisely. Output ONLY summary.\n\nText: {text[:1500]}\n\nSummary:",
            "fix_grammar": f"Fix grammar and spelling. Output ONLY corrected version.\n\nText: {text[:1500]}\n\nCorrected:",
            "explain": f"Explain this text simply. Output ONLY explanation.\n\nText: {text[:1500]}\n\nExplanation:"
        }
        
        prompt = prompts.get(action, prompts["summarize"])
        result = FreeAIHandler._call_api(prompt, max_retries=1)
        
        if result and not result.startswith("ERROR:"):
            result = clean_markdown(result)
            prefixes = ["Summary:", "Corrected:", "Explanation:"]
            for prefix in prefixes:
                if result.lower().startswith(prefix.lower()):
                    result = result[len(prefix):].strip()
            return result
        
        return result if result else "ERROR: Failed to refine text"
    
    @staticmethod
    def test_connection():
        """Test if the AI service is accessible."""
        try:
            # Use a simple test prompt
            url = "https://text.pollinations.ai/Hello"
            req = request.Request(url, method="GET")
            req.add_header("User-Agent", "EmailComposerPro/2.0")
            req.add_header("Accept", "text/plain")
            
            with request.urlopen(req, timeout=15) as response:
                result = response.read().decode('utf-8')
                # Check if we got a valid response
                if result and len(result) > 0:
                    return True
                return False
        except error.HTTPError as e:
            # Sometimes 200 OK is fine
            if e.code == 200:
                return True
            log.error(f"Connection test HTTP error: {e.code}")
            return False
        except error.URLError as e:
            log.error(f"Connection test URL error: {e.reason}")
            return False
        except Exception as e:
            log.error(f"Connection test error: {e}")
            return False

# ============================================================================
# Compose Dialog
# ============================================================================

class ComposeDialog(wx.Dialog):
    """Email composition dialog."""
    
    def __init__(self, parent):
        super().__init__(parent, title="Compose Email", size=(650, 620))
        self._setup_ui()
        self.Centre()
    
    def _setup_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Subject
        sizer.Add(wx.StaticText(panel, label="Subject:"), 0, wx.ALL, 5)
        self.subject = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 60))
        sizer.Add(self.subject, 0, wx.EXPAND | wx.ALL, 5)
        
        # Language
        lang_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lang_sizer.Add(wx.StaticText(panel, label="Language:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.language = wx.Choice(panel, choices=list(LANGUAGES.values()))
        current_lang = config.conf["EmailComposer"]["target_language"]
        lang_list = list(LANGUAGES.keys())
        self.language.SetSelection(lang_list.index(current_lang) if current_lang in lang_list else 0)
        lang_sizer.Add(self.language, 1, wx.EXPAND)
        sizer.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Tone
        tone_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tone_sizer.Add(wx.StaticText(panel, label="Tone:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.tone = wx.Choice(panel, choices=list(EMAIL_TONES.values()))
        current_tone = config.conf["EmailComposer"]["email_tone"]
        tone_list = list(EMAIL_TONES.keys())
        self.tone.SetSelection(tone_list.index(current_tone) if current_tone in tone_list else 0)
        tone_sizer.Add(self.tone, 1, wx.EXPAND)
        sizer.Add(tone_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Length
        length_sizer = wx.BoxSizer(wx.HORIZONTAL)
        length_sizer.Add(wx.StaticText(panel, label="Length:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.length = wx.Choice(panel, choices=list(EMAIL_LENGTHS.values()))
        current_length = config.conf["EmailComposer"]["email_length"]
        length_list = list(EMAIL_LENGTHS.keys())
        self.length.SetSelection(length_list.index(current_length) if current_length in length_list else 1)
        length_sizer.Add(self.length, 1, wx.EXPAND)
        sizer.Add(length_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Signature
        self.signature_check = wx.CheckBox(panel, label="Include Signature")
        self.signature_check.SetValue(config.conf["EmailComposer"]["include_signature"])
        sizer.Add(self.signature_check, 0, wx.ALL, 5)
        
        self.signature_text = wx.TextCtrl(panel, value=config.conf["EmailComposer"]["signature_text"],
                                         style=wx.TE_MULTILINE, size=(-1, 80))
        self.signature_text.Enable(self.signature_check.GetValue())
        sizer.Add(self.signature_text, 0, wx.EXPAND | wx.ALL, 5)
        self.signature_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_sig)
        
        # Info
        info = wx.StaticText(panel, label="✓ Free AI Service - No API Key Required")
        info.SetForegroundColour(wx.Colour(0, 128, 0))
        sizer.Add(info, 0, wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.generate_btn = wx.Button(panel, label="Generate Email")
        self.generate_btn.Bind(wx.EVT_BUTTON, self.on_generate)
        btn_sizer.Add(self.generate_btn, 0, wx.ALL, 5)
        
        close_btn = wx.Button(panel, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        btn_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(sizer)
    
    def on_toggle_sig(self, event):
        self.signature_text.Enable(self.signature_check.GetValue())
    
    def on_generate(self, event):
        subject = self.subject.GetValue().strip()
        if not subject:
            ui.message("Please enter a subject")
            return
        
        self.generate_btn.Enable(False)
        ui.message("Generating email...")
        threading.Thread(target=self._generate, args=(subject,), daemon=True).start()
    
    def _generate(self, subject):
        try:
            tone_key = list(EMAIL_TONES.keys())[self.tone.GetSelection()]
            length_key = list(EMAIL_LENGTHS.keys())[self.length.GetSelection()]
            signature = self.signature_text.GetValue().strip() if self.signature_check.GetValue() else ""
            
            old_tone = config.conf["EmailComposer"]["email_tone"]
            old_length = config.conf["EmailComposer"]["email_length"]
            old_sig = config.conf["EmailComposer"]["include_signature"]
            old_sig_text = config.conf["EmailComposer"]["signature_text"]
            
            config.conf["EmailComposer"]["email_tone"] = tone_key
            config.conf["EmailComposer"]["email_length"] = length_key
            config.conf["EmailComposer"]["include_signature"] = self.signature_check.GetValue()
            config.conf["EmailComposer"]["signature_text"] = signature
            
            instructions = f"write an email with subject: {subject}"
            email = FreeAIHandler.generate_email_from_instructions(instructions)
            
            config.conf["EmailComposer"]["email_tone"] = old_tone
            config.conf["EmailComposer"]["email_length"] = old_length
            config.conf["EmailComposer"]["include_signature"] = old_sig
            config.conf["EmailComposer"]["signature_text"] = old_sig_text
            
            if email and not email.startswith("ERROR:"):
                copy_to_clipboard(email)
                wx.CallAfter(ui.message, "Email copied to clipboard! Press Ctrl+V to paste.")
                wx.CallAfter(tones.beep, 1000, 200)
                wx.CallAfter(self.Close)
            else:
                wx.CallAfter(ui.message, email[:100] if email else "Failed to generate email")
                wx.CallAfter(tones.beep, 400, 300)
        except Exception as e:
            wx.CallAfter(ui.message, f"Error: {str(e)[:50]}")
        finally:
            wx.CallAfter(self.generate_btn.Enable, True)

# ============================================================================
# Donation Dialog Handler
# ============================================================================

def show_donation_dialog():
    """Show the donation dialog."""
    try:
        from .donate_dialog import requestDonations
        requestDonations(gui.mainFrame)
    except ImportError:
        wx.MessageBox(
            _("Donation dialog not available.\n\nYou can support the development via UPI: bhosalekasturi694@oksbi"),
            _("Support Development"),
            wx.OK | wx.ICON_INFORMATION
        )
    except Exception as e:
        log.error(f"Error showing donation dialog: {e}")
        wx.MessageBox(
            _("Error opening donation dialog: {error}\n\nYou can support via UPI: bhosalekasturi694@oksbi").format(error=str(e)),
            _("Error"),
            wx.OK | wx.ICON_ERROR
        )

# ============================================================================
# Settings Panel
# ============================================================================

class SettingsPanel(gui.settingsDialogs.SettingsPanel):
    """Settings panel."""
    
    title = "AI Email Composer"
    
    def makeSettings(self, settingsSizer):
        sizerHelper = gui.guiHelper.BoxSizerHelper(self, wx.VERTICAL)
        
        info_text = (
            "✓ Free AI Service - No API Key Required!\n"
            "✓ Uses Pollinations.AI - completely free\n\n"
            "Workflow:\n"
            "1. Type natural instructions in subject field\n"
            "   Example: 'write email to manager Priya about sick leave'\n"
            "2. NVDA+Shift+G → Instructions copied + subject generated\n"
            "3. Press Tab to message body\n"
            "4. NVDA+Shift+H → Full email generated from instructions!\n\n"
            "Shortcuts:\n"
            "• NVDA+Shift+G - Copy instructions + generate subject\n"
            "• NVDA+Shift+H - Generate email from clipboard instructions\n"
            "• NVDA+Shift+T - Translate selected text\n"
            "• NVDA+Shift+J - Refine selected text\n"
            "• NVDA+Shift+K - Open email composer"
        )
        info = wx.StaticText(self, label=info_text)
        info.SetForegroundColour(wx.Colour(0, 128, 0))
        sizerHelper.addItem(info)
        
        sizerHelper.addItem(wx.StaticText(self, label=""))
        
        # Email tone
        self.tone = sizerHelper.addLabeledControl("Default Email Tone:", wx.Choice, choices=list(EMAIL_TONES.values()))
        current_tone = config.conf["EmailComposer"]["email_tone"]
        tone_list = list(EMAIL_TONES.keys())
        self.tone.SetSelection(tone_list.index(current_tone) if current_tone in tone_list else 0)
        
        # Email length
        self.length = sizerHelper.addLabeledControl("Default Email Length:", wx.Choice, choices=list(EMAIL_LENGTHS.values()))
        current_length = config.conf["EmailComposer"]["email_length"]
        length_list = list(EMAIL_LENGTHS.keys())
        self.length.SetSelection(length_list.index(current_length) if current_length in length_list else 1)
        
        # Email language
        self.language = sizerHelper.addLabeledControl("Default Language for Emails:", wx.Choice, choices=list(LANGUAGES.values()))
        current_lang = config.conf["EmailComposer"]["target_language"]
        lang_list = list(LANGUAGES.keys())
        self.language.SetSelection(lang_list.index(current_lang) if current_lang in lang_list else 0)
        
        sizerHelper.addItem(wx.StaticText(self, label=""))
        
        # Translation language
        self.translation_lang = sizerHelper.addLabeledControl("Translate To Language:", wx.Choice, choices=list(LANGUAGES.values()))
        current_trans_lang = config.conf["EmailComposer"]["translation_language"]
        self.translation_lang.SetSelection(lang_list.index(current_trans_lang) if current_trans_lang in lang_list else 0)
        
        sizerHelper.addItem(wx.StaticText(self, label=""))
        
        # Signature
        self.signature_check = wx.CheckBox(self, label="Include Signature by Default")
        self.signature_check.SetValue(config.conf["EmailComposer"]["include_signature"])
        sizerHelper.addItem(self.signature_check)
        
        self.signature_text = sizerHelper.addLabeledControl("Signature:", wx.TextCtrl, style=wx.TE_MULTILINE, size=(-1, 80))
        self.signature_text.SetValue(config.conf["EmailComposer"]["signature_text"])
        self.signature_text.Enable(self.signature_check.GetValue())
        self.signature_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_sig)
        
        sizerHelper.addItem(wx.StaticText(self, label=""))
        
        # Auto paste
        self.auto_paste = wx.CheckBox(self, label="Auto-paste after generation")
        self.auto_paste.SetValue(config.conf["EmailComposer"]["auto_paste"])
        sizerHelper.addItem(self.auto_paste)
        
        sizerHelper.addItem(wx.StaticText(self, label=""))
        
        # Test button
        self.test_btn = wx.Button(self, label="Test AI Service Connection")
        self.test_btn.Bind(wx.EVT_BUTTON, self.on_test)
        sizerHelper.addItem(self.test_btn)
        
        settingsSizer.Add(sizerHelper.sizer, 1, wx.EXPAND)
    
    def on_toggle_sig(self, event):
        self.signature_text.Enable(self.signature_check.GetValue())
    
    def on_test(self, event):
        ui.message("Testing connection...")
        self.test_btn.Enable(False)
        
        def test():
            if FreeAIHandler.test_connection():
                wx.CallAfter(wx.MessageBox, "✓ Connection successful!\n\nAI service is working properly.", "Test Result", wx.OK)
                wx.CallAfter(ui.message, "Connection successful!")
            else:
                wx.CallAfter(wx.MessageBox, "✗ Connection failed!\n\nPlease check your internet connection.\n\nThe addon may still work, but some features might be slow.", "Test Result", wx.OK | wx.ICON_WARNING)
                wx.CallAfter(ui.message, "Connection failed! Check internet.")
            wx.CallAfter(self.test_btn.Enable, True)
        
        threading.Thread(target=test, daemon=True).start()
    
    def onSave(self):
        tone_list = list(EMAIL_TONES.keys())
        if self.tone.GetSelection() != -1:
            config.conf["EmailComposer"]["email_tone"] = tone_list[self.tone.GetSelection()]
        
        length_list = list(EMAIL_LENGTHS.keys())
        if self.length.GetSelection() != -1:
            config.conf["EmailComposer"]["email_length"] = length_list[self.length.GetSelection()]
        
        lang_list = list(LANGUAGES.keys())
        if self.language.GetSelection() != -1:
            config.conf["EmailComposer"]["target_language"] = lang_list[self.language.GetSelection()]
        
        if self.translation_lang.GetSelection() != -1:
            config.conf["EmailComposer"]["translation_language"] = lang_list[self.translation_lang.GetSelection()]
        
        config.conf["EmailComposer"]["include_signature"] = self.signature_check.GetValue()
        config.conf["EmailComposer"]["signature_text"] = self.signature_text.GetValue()
        config.conf["EmailComposer"]["auto_paste"] = self.auto_paste.GetValue()
        config.conf.save()
        ui.message("Settings saved")

# ============================================================================
# Main Plugin Class
# ============================================================================

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """Main plugin class."""
    
    scriptCategory = "AI Email Composer"
    
    def __init__(self):
        super(GlobalPlugin, self).__init__()
        
        if not globalVars.appArgs.secure:
            # Register settings panel - ONLY ONCE
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SettingsPanel)
            self._create_menu()
    
    def _create_menu(self):
        """Create tools menu entry."""
        try:
            self.email_menu = wx.Menu()
            
            gen_subject = self.email_menu.Append(wx.ID_ANY, "Generate Subject (Copies Instructions)")
            self.email_menu.Bind(wx.EVT_MENU, lambda e: self.script_generate_subject(None), gen_subject)
            
            gen_email = self.email_menu.Append(wx.ID_ANY, "Generate Email from Clipboard Instructions")
            self.email_menu.Bind(wx.EVT_MENU, lambda e: self.script_generate_email(None), gen_email)
            
            self.email_menu.AppendSeparator()
            
            translate_item = self.email_menu.Append(wx.ID_ANY, "Translate Selected Text")
            self.email_menu.Bind(wx.EVT_MENU, lambda e: self.script_translate(None), translate_item)
            
            refine_item = self.email_menu.Append(wx.ID_ANY, "Refine Selected Text")
            self.email_menu.Bind(wx.EVT_MENU, lambda e: self.script_refine_text(None), refine_item)
            
            compose_item = self.email_menu.Append(wx.ID_ANY, "Open Compose Dialog")
            self.email_menu.Bind(wx.EVT_MENU, lambda e: self.script_open_composer(None), compose_item)
            
            self.email_menu.AppendSeparator()
            
            # Donation menu item
            donation_item = self.email_menu.Append(wx.ID_ANY, _("&Donate / Support"))
            self.email_menu.Bind(wx.EVT_MENU, self.on_donation, donation_item)
            
            settings_item = self.email_menu.Append(wx.ID_ANY, "Settings...")
            self.email_menu.Bind(wx.EVT_MENU, self.on_settings, settings_item)
            
            about_item = self.email_menu.Append(wx.ID_ANY, "About")
            self.email_menu.Bind(wx.EVT_MENU, self.on_about, about_item)
            
            self.tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
            self.tools_menu.AppendSubMenu(self.email_menu, "AI Email Composer")
        except Exception as e:
            log.error(f"Error creating menu: {e}")
    
    def terminate(self):
        try:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SettingsPanel)
        except:
            pass
    
    def on_settings(self, event):
        try:
            dlg = gui.settingsDialogs.NVDASettingsDialog(gui.mainFrame, SettingsPanel)
            dlg.Show()
        except:
            pass
    
    def on_donation(self, event):
        """Open donation dialog."""
        show_donation_dialog()
    
    def on_about(self, event):
        message = (
            "AI Email Composer Pro\nVersion 2.0\n\n"
            "How to use:\n"
            "1. Type natural instructions in subject field\n"
            "2. NVDA+Shift+G → Instructions copied + subject generated\n"
            "3. Tab to message body\n"
            "4. NVDA+Shift+H → Email generated from instructions!\n\n"
            "Shortcuts:\n"
            "• NVDA+Shift+G - Copy instructions + generate subject\n"
            "• NVDA+Shift+H - Generate email from clipboard\n"
            "• NVDA+Shift+T - Translate text\n"
            "• NVDA+Shift+J - Refine text\n"
            "• NVDA+Shift+K - Open composer\n\n"
            "Supported Languages:\n"
            "English, Hindi, Marathi, Spanish, French, German, Chinese,\n"
            "Japanese, Arabic, Russian, Portuguese, Italian, Turkish,\n"
            "Korean, Dutch, Polish, Bengali, Tamil, Telugu, Gujarati,\n"
            "Kannada, Malayalam\n\n"
            "Email Length Options:\n"
            "• Short (50-100 words)\n"
            "• Medium (100-200 words)\n"
            "• Long (200-300 words)\n"
            "• Detailed (300-500 words)\n\n"
            "Free AI service - No API key required!\n\n"
            "Support Development: bhosalekasturi694@oksbi"
        )
        wx.MessageBox(message, "About", wx.OK)
    
    # ========================================================================
    # Script: Generate Subject (Copies instructions to clipboard + generates subject)
    # ========================================================================
    
    @scriptHandler.script(
        description="Copy instructions to clipboard and generate subject",
        gesture="kb:NVDA+Shift+G"
    )
    def script_generate_subject(self, gesture):
        """Copy instructions to clipboard, then generate and paste subject."""
        instructions = get_focused_text()
        
        if not instructions:
            ui.message("No instructions found. Type your request in the subject field.")
            tones.beep(400, 200)
            return
        
        # First, copy instructions to clipboard
        copy_to_clipboard(instructions)
        
        ui.message("Instructions copied to clipboard. Generating subject...")
        tones.beep(800, 100)
        
        threading.Thread(target=self._do_generate_subject, args=(instructions,), daemon=True).start()
    
    def _do_generate_subject(self, instructions):
        try:
            subject = FreeAIHandler.generate_subject_only(instructions)
            
            if subject and not subject.startswith("ERROR:"):
                if set_focused_text(subject):
                    announce_and_beep("Subject generated and pasted! Instructions are in clipboard.", True)
                else:
                    announce_and_beep("Subject copied to clipboard! Press Ctrl+V to paste.", True)
            else:
                announce_and_beep(subject[:100] if subject else "Failed to generate subject", False)
        except Exception as e:
            announce_and_beep(f"Error: {str(e)[:50]}", False)
    
    # ========================================================================
    # Script: Generate Email from Clipboard Instructions
    # ========================================================================
    
    @scriptHandler.script(
        description="Generate email from instructions in clipboard",
        gesture="kb:NVDA+Shift+H"
    )
    def script_generate_email(self, gesture):
        """Generate email based on instructions from clipboard."""
        # Get instructions from clipboard
        instructions = api.getClipData()
        
        if not instructions or len(instructions.strip()) < 10:
            ui.message("No valid instructions in clipboard. First press NVDA+Shift+G to copy instructions.")
            tones.beep(400, 200)
            return
        
        ui.message("Generating email based on your instructions...")
        tones.beep(800, 100)
        
        threading.Thread(target=self._do_generate_email, args=(instructions,), daemon=True).start()
    
    def _do_generate_email(self, instructions):
        try:
            email = FreeAIHandler.generate_email_from_instructions(instructions)
            
            if email and not email.startswith("ERROR:"):
                if config.conf["EmailComposer"]["auto_paste"]:
                    copy_to_clipboard(email)
                    time.sleep(0.2)
                    send_ctrl_v()
                    announce_and_beep("Email generated and pasted!", True)
                else:
                    copy_to_clipboard(email)
                    announce_and_beep("Email copied to clipboard! Press Ctrl+V to paste.", True)
            else:
                announce_and_beep(email[:100] if email else "Failed to generate email", False)
        except Exception as e:
            announce_and_beep(f"Error: {str(e)[:50]}", False)
    
    # ========================================================================
    # Script: Translate Text
    # ========================================================================
    
    @scriptHandler.script(
        description="Translate selected text",
        gesture="kb:NVDA+Shift+T"
    )
    def script_translate(self, gesture):
        """Translate selected text."""
        selected = get_selected_text()
        
        if not selected or len(selected.strip()) < 3:
            ui.message("No text selected. Select some text to translate.")
            tones.beep(400, 200)
            return
        
        ui.message("Translating...")
        tones.beep(800, 100)
        
        threading.Thread(target=self._do_translate, args=(selected,), daemon=True).start()
    
    def _do_translate(self, text):
        try:
            translated = FreeAIHandler.translate_text(text)
            
            if translated and not translated.startswith("ERROR:"):
                wx.CallAfter(show_result_window, "Translation Result", translated)
                wx.CallAfter(tones.beep, 1000, 200)
            else:
                wx.CallAfter(ui.message, translated[:100] if translated else "Failed to translate")
                wx.CallAfter(tones.beep, 400, 300)
        except Exception as e:
            wx.CallAfter(ui.message, f"Error: {str(e)[:50]}")
            wx.CallAfter(tones.beep, 400, 300)
    
    # ========================================================================
    # Script: Open Composer
    # ========================================================================
    
    @scriptHandler.script(
        description="Open email composer",
        gesture="kb:NVDA+Shift+K"
    )
    def script_open_composer(self, gesture):
        """Open composer dialog."""
        try:
            gui.mainFrame.prePopup()
            dlg = ComposeDialog(gui.mainFrame)
            dlg.ShowModal()
            dlg.Destroy()
        except Exception as e:
            ui.message(f"Error: {str(e)[:50]}")
        finally:
            gui.mainFrame.postPopup()
    
    # ========================================================================
    # Script: Refine Text
    # ========================================================================
    
    @scriptHandler.script(
        description="Refine selected text",
        gesture="kb:NVDA+Shift+J"
    )
    def script_refine_text(self, gesture):
        """Refine selected text."""
        selected = get_selected_text()
        
        if not selected or len(selected.strip()) < 5:
            ui.message("No text selected. Select some text first.")
            tones.beep(400, 200)
            return
        
        wx.CallAfter(self._show_refine_menu, selected)
    
    def _show_refine_menu(self, text):
        try:
            gui.mainFrame.prePopup()
            choices = ["Summarize", "Fix Grammar", "Explain"]
            dlg = wx.SingleChoiceDialog(gui.mainFrame, "Choose action:", "Refine Text", choices)
            
            if dlg.ShowModal() == wx.ID_OK:
                idx = dlg.GetSelection()
                actions = ["summarize", "fix_grammar", "explain"]
                action = actions[idx]
                action_name = choices[idx]
                dlg.Destroy()
                gui.mainFrame.postPopup()
                
                ui.message(f"{action_name}ing...")
                tones.beep(800, 100)
                threading.Thread(target=self._do_refine, args=(text, action, action_name), daemon=True).start()
                return
            dlg.Destroy()
        except Exception as e:
            log.error(f"Refine menu error: {e}")
        finally:
            gui.mainFrame.postPopup()
    
    def _do_refine(self, text, action, action_name):
        try:
            result = FreeAIHandler.refine_text(text, action)
            
            if result and not result.startswith("ERROR:"):
                if config.conf["EmailComposer"]["auto_paste"]:
                    copy_to_clipboard(result)
                    time.sleep(0.1)
                    send_ctrl_v()
                    announce_and_beep(f"{action_name} completed and pasted!", True)
                else:
                    copy_to_clipboard(result)
                    announce_and_beep(f"{action_name} copied to clipboard! Press Ctrl+V to paste.", True)
            else:
                announce_and_beep(f"Failed to {action_name.lower()} text", False)
        except Exception as e:
            announce_and_beep(f"Error: {str(e)[:50]}", False)


# ============================================================================
# Note: SettingsPanel is registered in GlobalPlugin.__init__ - NOT here!
# This prevents duplicate entries in NVDA Settings dialog.
# ============================================================================