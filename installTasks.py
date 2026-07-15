# -*- coding: UTF-8 -*-

import addonHandler
import gui
import wx
import webbrowser

addonHandler.initTranslation()

# Your UPI donation link (you can create a webpage or keep the dialog)
DONATION_MESSAGE = "UPI: bhosalekasturi694@oksbi"


def showDonationDialog(parent):
    """Show donation dialog after installation."""
    message = _(
        "Thank you for installing AI Email Composer Pro!\n\n"
        "This add-on helps you write professional emails using FREE AI.\n"
        "No API key required! Works immediately after installation.\n\n"
        "Quick Start:\n"
        "• Type instructions in subject field (e.g., 'write email to manager about sick leave')\n"
        "• Press NVDA+Shift+G → Instructions copied, subject generated\n"
        "• Press Tab to message body\n"
        "• Press NVDA+Shift+H → Complete email generated and pasted!\n\n"
        "Other Shortcuts:\n"
        "• NVDA+Shift+T - Translate selected text\n"
        "• NVDA+Shift+J - Refine selected text\n"
        "• NVDA+Shift+K - Open email composer\n\n"
        "Support Development:\n"
        "If you find this add-on useful, please consider supporting its development.\n"
        "UPI ID: bhosalekasturi694@oksbi\n\n"
        "Would you like to copy the UPI ID to clipboard?"
    )
    title = _("Support Development")
    
    dlg = wx.MessageDialog(parent, message, title, wx.YES_NO | wx.ICON_QUESTION)
    result = dlg.ShowModal()
    dlg.Destroy()
    
    if result == wx.ID_YES:
        try:
            import api
            api.copyToClip("bhosalekasturi694@oksbi")
            wx.MessageBox(
                _("UPI ID copied to clipboard!\n\nYou can now paste it in any UPI app to donate."),
                _("Success"),
                wx.OK | wx.ICON_INFORMATION
            )
        except:
            wx.MessageBox(
                _("UPI ID: bhosalekasturi694@oksbi\n\nPlease copy it manually."),
                _("UPI ID"),
                wx.OK | wx.ICON_INFORMATION
            )


def showInstallCompleteDialog(parent):
    """Show installation complete dialog."""
    message = _(
        "AI Email Composer Pro has been successfully installed!\n\n"
        "✨ COMPLETELY FREE - No API key required!\n\n"
        "Quick Start:\n"
        "1. In Gmail/Outlook, focus on the subject field\n"
        "2. Type: 'write email to manager about sick leave'\n"
        "3. Press NVDA+Shift+G → Subject generated\n"
        "4. Press Tab to message body\n"
        "5. Press NVDA+Shift+H → Complete email generated!\n\n"
        "Shortcuts:\n"
        "• NVDA+Shift+G - Generate subject\n"
        "• NVDA+Shift+H - Generate email\n"
        "• NVDA+Shift+T - Translate text\n"
        "• NVDA+Shift+J - Refine text\n"
        "• NVDA+Shift+K - Open composer\n\n"
        "Supported Languages:\n"
        "English, Hindi, Marathi, Spanish, French, German, Chinese,\n"
        "Japanese, Arabic, Russian, Portuguese, Italian, and more!\n\n"
        "For help, press NVDA+N → Tools → AI Email Composer → About"
    )
    title = _("Installation Complete")
    dlg = wx.MessageDialog(parent, message, title, wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()


def onInstall():
    """Called when addon is installed."""
    def doPostInstall():
        # Safeguard to ensure gui.mainFrame exists before trying to present popups
        if not getattr(gui, "mainFrame", None):
            return
        gui.mainFrame.prePopup()
        try:
            showInstallCompleteDialog(gui.mainFrame)
            showDonationDialog(gui.mainFrame)
        finally:
            gui.mainFrame.postPopup()
    wx.CallAfter(doPostInstall)


def onUninstall():
    """Called when addon is uninstalled."""
    pass