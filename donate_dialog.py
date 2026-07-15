# -*- coding: utf-8 -*-
"""
Donation Dialog for Email Composer Pro
Supports UPI payments with QR code
"""

import os
import sys
import webbrowser
import addonHandler
import gui
import wx
import threading
import io
import tempfile
import logging

# Add lib directory to path for external libraries
lib_path = os.path.join(os.path.dirname(__file__), "lib")
if os.path.exists(lib_path) and lib_path not in sys.path:
    sys.path.insert(0, lib_path)

log = logging.getLogger(__name__)

# Try to import qrcode from lib folder
try:
    import qrcode
    from PIL import Image as PILImage
    QRCODE_AVAILABLE = True
    log.info("QRCode libraries loaded successfully")
except ImportError as e:
    log.error(f"QRCode import error: {e}")
    QRCODE_AVAILABLE = False

addonHandler.initTranslation()

# Your UPI details
UPI_ID = "bhosalekasturi694@oksbi"
UPI_NAME = "Kasturi Bhosale"


class QRCodeDialog(wx.Dialog):
    """Dialog to display UPI QR code for scanning, with full-screen option."""
    
    def __init__(self, parent, upi_id, upi_name, amount=None):
        title = _("UPI QR Code - Scan to Pay")
        # Start with a large dialog; user can resize or go full screen
        super().__init__(parent, title=title, size=(700, 750),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        self.upi_id = upi_id
        self.upi_name = upi_name
        self.amount = amount
        self.full_screen = False
        self._setup_ui()
        self.Centre()
    
    def _setup_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Info text
        info_text = _("Scan this QR code with any UPI app\n(Google Pay, PhonePe, Paytm, etc.)")
        info = wx.StaticText(panel, label=info_text)
        info.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        sizer.Add(info, 0, wx.ALL | wx.CENTER, 10)
        
        # Amount info
        if self.amount:
            amount_text = _("Amount: ₹{amount}").format(amount=int(self.amount))
            amount_lbl = wx.StaticText(panel, label=amount_text)
            amount_lbl.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
            amount_lbl.SetForegroundColour(wx.Colour(0, 128, 0))
            sizer.Add(amount_lbl, 0, wx.ALL | wx.CENTER, 5)
        
        # QR Code image area - will expand to fill available space
        self.qr_static = wx.StaticBitmap(panel, size=(500, 500))
        sizer.Add(self.qr_static, 1, wx.ALL | wx.CENTER | wx.EXPAND, 10)
        
        # Loading text (will be replaced by QR code)
        self.loading_text = wx.StaticText(panel, label=_("Generating QR code..."))
        self.loading_text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        sizer.Add(self.loading_text, 0, wx.ALL | wx.CENTER, 5)
        
        # UPI ID display
        upi_id_text = wx.StaticText(panel, label=_("UPI ID: {upi}").format(upi=self.upi_id))
        upi_id_text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        sizer.Add(upi_id_text, 0, wx.ALL | wx.CENTER, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        copy_btn = wx.Button(panel, label=_("Copy UPI ID"))
        copy_btn.Bind(wx.EVT_BUTTON, self.on_copy_upi)
        btn_sizer.Add(copy_btn, 0, wx.ALL, 5)
        
        fullscreen_btn = wx.Button(panel, label=_("Full Screen"))
        fullscreen_btn.Bind(wx.EVT_BUTTON, self.on_toggle_fullscreen)
        btn_sizer.Add(fullscreen_btn, 0, wx.ALL, 5)
        
        close_btn = wx.Button(panel, label=_("Close"))
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        btn_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        
        # Generate QR code
        if QRCODE_AVAILABLE:
            self._generate_qr()
        else:
            self.loading_text.SetLabel(
                _("QR code library not available.\nPlease copy UPI ID manually."))
    
    def _generate_qr(self):
        """Generate QR code with high quality and large size."""
        def generate():
            try:
                # Ensure amount is integer
                amount_param = ""
                if self.amount:
                    try:
                        amt = int(float(self.amount))
                        amount_param = f"&am={amt}&cu=INR"
                    except:
                        pass
                
                # Create UPI payment URI
                upi_uri = f"upi://pay?pa={self.upi_id}&pn={self.upi_name}{amount_param}"
                log.info(f"Generating QR for: {upi_uri}")
                
                # Generate QR with high density and error correction
                qr = qrcode.QRCode(
                    version=12,                     # High capacity for dense data
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=14,                    # Large modules
                    border=4,
                )
                qr.add_data(upi_uri)
                qr.make(fit=True)
                
                # Create high-resolution image
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Save to a temporary file for reliable wx loading
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                img.save(temp_file, format='PNG', quality=100)
                temp_file.close()
                
                # Load image with wx
                wx_image = wx.Image(temp_file.name, wx.BITMAP_TYPE_PNG)
                
                # Clean up temp file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                
                if wx_image.IsOk():
                    # Scale to a large size (will be stretched by the StaticBitmap)
                    # We scale to 500x500 so it's sharp even when expanded
                    wx_image = wx_image.Scale(600, 600, wx.IMAGE_QUALITY_HIGH)
                    bitmap = wx.Bitmap(wx_image)
                    
                    # Update UI
                    wx.CallAfter(self.qr_static.SetBitmap, bitmap)
                    wx.CallAfter(self.loading_text.Hide)
                    wx.CallAfter(self.Layout)
                    log.info("QR code generated successfully")
                else:
                    raise Exception("Failed to create wx.Image")
                    
            except Exception as e:
                error_text = _("Failed to generate QR code: {error}").format(error=str(e))
                wx.CallAfter(self.loading_text.SetLabel, error_text)
                log.error(f"QR generation error: {e}")
        
        threading.Thread(target=generate, daemon=True).start()
    
    def on_toggle_fullscreen(self, event):
        """Toggle full-screen mode."""
        self.full_screen = not self.full_screen
        self.ShowFullScreen(self.full_screen)
        # Update button label
        btn = event.GetEventObject()
        if self.full_screen:
            btn.SetLabel(_("Exit Full Screen"))
        else:
            btn.SetLabel(_("Full Screen"))
        # Refresh layout
        self.Layout()
    
    def on_copy_upi(self, event):
        """Copy UPI ID to clipboard."""
        try:
            import api
            api.copyToClip(self.upi_id)
            wx.MessageBox(_("UPI ID copied to clipboard! You can now paste it in any UPI app."), 
                         _("Success"), wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(_("Failed to copy: {error}").format(error=str(e)), 
                         _("Error"), wx.OK | wx.ICON_ERROR)


# The rest of the file (DonationDialog and requestDonations) remains unchanged.
# For completeness, I'll include them below, but they are the same as before.
# ...

class DonationDialog(wx.Dialog):
    """Donation dialog with UPI payment options."""
    
    def __init__(self, parent):
        addon = addonHandler.getCodeAddon()
        addon_summary = addon.manifest['summary']
        
        title = _("Support {name}").format(name=addon_summary)
        super().__init__(parent, title=title, size=(550, 600))
        
        self.addon_summary = addon_summary
        self._setup_ui()
        self.Centre()
    
    def _setup_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title_text = wx.StaticText(panel, label=_("Support the Development of {name}").format(name=self.addon_summary))
        title_text.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        main_sizer.Add(title_text, 0, wx.ALL | wx.CENTER, 15)
        
        # Message
        message = _(
            "Thank you for using AI Email Composer Pro!\n\n"
            "This addon is completely FREE and always will be.\n"
            "However, if you find it useful, your support is greatly appreciated.\n\n"
            "Your support helps me:\n"
            "• Add new features\n"
            "• Fix bugs faster\n"
            "• Keep the addon free for everyone\n\n"
            "Choose your payment method below:"
        )
        msg_text = wx.StaticText(panel, label=message)
        msg_text.Wrap(500)
        main_sizer.Add(msg_text, 0, wx.ALL | wx.EXPAND, 15)
        
        # Separator
        line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
        main_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # UPI Section Title
        upi_title = wx.StaticText(panel, label=_("📱 UPI Payment (India)"))
        upi_title.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        main_sizer.Add(upi_title, 0, wx.ALL, 10)
        
        # UPI ID display
        upi_id_text = wx.StaticText(panel, label=_("UPI ID: {upi}").format(upi=UPI_ID))
        upi_id_text.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        upi_id_text.SetForegroundColour(wx.Colour(0, 0, 255))
        main_sizer.Add(upi_id_text, 0, wx.LEFT | wx.RIGHT, 15)
        
        # UPI Buttons Grid
        upi_grid = wx.GridSizer(rows=2, cols=2, vgap=10, hgap=10)
        
        # Copy UPI ID button
        copy_btn = wx.Button(panel, label=_("Copy UPI ID"), size=(180, 45))
        copy_btn.Bind(wx.EVT_BUTTON, self.on_copy_upi)
        upi_grid.Add(copy_btn, 0, wx.ALIGN_CENTER)
        
        # Show QR Code button
        qr_btn = wx.Button(panel, label=_("Show QR Code"), size=(180, 45))
        qr_btn.Bind(wx.EVT_BUTTON, self.on_show_qr)
        upi_grid.Add(qr_btn, 0, wx.ALIGN_CENTER)
        
        # Google Pay button
        gpay_btn = wx.Button(panel, label=_("Google Pay"), size=(180, 45))
        gpay_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_upi_app("gpay"))
        upi_grid.Add(gpay_btn, 0, wx.ALIGN_CENTER)
        
        # PhonePe button
        phonepe_btn = wx.Button(panel, label=_("PhonePe"), size=(180, 45))
        phonepe_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_upi_app("phonepe"))
        upi_grid.Add(phonepe_btn, 0, wx.ALIGN_CENTER)
        
        main_sizer.Add(upi_grid, 0, wx.ALL | wx.CENTER, 15)
        
        # Suggested amounts
        amount_text = wx.StaticText(panel, label=_("Suggested amounts: ₹50, ₹100, ₹200, ₹500 (or any amount you wish)"))
        amount_text.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        main_sizer.Add(amount_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        
        # Separator
        line2 = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
        main_sizer.Add(line2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # Thank you message
        thanks_text = wx.StaticText(panel, label=_("🙏 Thank you for your support! Every contribution helps keep this project alive."))
        thanks_text.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        thanks_text.SetForegroundColour(wx.Colour(0, 128, 0))
        main_sizer.Add(thanks_text, 0, wx.ALL | wx.CENTER, 15)
        
        # Close button
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        close_btn = wx.Button(panel, label=_("Close"))
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        btn_sizer.Add(close_btn, 0, wx.ALL, 10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)
        
        panel.SetSizer(main_sizer)
    
    def on_copy_upi(self, event):
        """Copy UPI ID to clipboard."""
        try:
            import api
            api.copyToClip(UPI_ID)
            wx.MessageBox(_("UPI ID copied to clipboard! You can now paste it in any UPI app."), 
                         _("Success"), wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(_("Failed to copy: {error}").format(error=str(e)), 
                         _("Error"), wx.OK | wx.ICON_ERROR)
    
    def on_show_qr(self, event):
        """Show QR code dialog."""
        if not QRCODE_AVAILABLE:
            wx.MessageBox(
                _("QR code generation is not available.\n\n"
                  "Please use the UPI ID directly: {upi}\n\n"
                  "To enable QR codes, install qrcode and Pillow:\n"
                  "pip install qrcode[pil] Pillow -t lib").format(upi=UPI_ID),
                _("QR Code Unavailable"),
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Ask for amount
        amount_dlg = wx.TextEntryDialog(self, 
            _("Enter amount in INR (₹) or leave empty for any amount:"),
            _("Payment Amount"), "")
        
        amount = None
        if amount_dlg.ShowModal() == wx.ID_OK:
            amount_text = amount_dlg.GetValue().strip()
            if amount_text:
                try:
                    amount = int(amount_text)
                    if amount <= 0:
                        amount = None
                except:
                    amount = None
        amount_dlg.Destroy()
        
        qr_dlg = QRCodeDialog(self, UPI_ID, UPI_NAME, amount)
        qr_dlg.ShowModal()
        qr_dlg.Destroy()
    
    def on_upi_app(self, app_name):
        """Open specific UPI app."""
        try:
            upi_uri = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&cu=INR"
            app_packages = {
                "gpay": "com.google.android.apps.nbu.pay",
                "phonepe": "com.phonepe.app",
                "paytm": "net.one97.paytm"
            }
            if app_name in app_packages:
                intent_uri = f"intent://pay?pa={UPI_ID}&pn={UPI_NAME}&cu=INR#Intent;scheme=upi;package={app_packages[app_name]};end"
                webbrowser.open(intent_uri)
            else:
                webbrowser.open(upi_uri)
            wx.MessageBox(
                _("If the app didn't open automatically, please:\n\n"
                  "1. Open {app_name} manually\n"
                  "2. Go to Send Money / Scan & Pay\n"
                  "3. Enter UPI ID: {upi}\n"
                  "4. Or scan the QR code from the main donation dialog").format(
                      app_name=app_name.upper(), upi=UPI_ID),
                _("Instructions"),
                wx.OK | wx.ICON_INFORMATION
            )
        except Exception as e:
            wx.MessageBox(
                _("Could not open {app_name} automatically.\n\n"
                  "Please open the app manually and use UPI ID: {upi}\n\n"
                  "Error: {error}").format(app_name=app_name.upper(), upi=UPI_ID, error=str(e)),
                _("Error"),
                wx.OK | wx.ICON_ERROR
            )


def requestDonations(parentWindow):
    """Main function to show donation dialog."""
    try:
        dlg = DonationDialog(parentWindow)
        result = dlg.ShowModal()
        dlg.Destroy()
        return result
    except Exception as e:
        wx.MessageBox(_("Error opening donation dialog: {error}").format(error=str(e)), 
                     _("Error"), wx.OK | wx.ICON_ERROR)
        return wx.CANCEL