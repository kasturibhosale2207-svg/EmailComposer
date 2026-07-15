# -*- coding: utf-8 -*-

addon_info = {
    "addon_name": "emailComposer",
    "addon_summary": "AI Email Composer Pro",
    "addon_description": "Write complete emails instantly with AI!",
    "addon_version": "2.0.0",
    "addon_author": "Kasturi Bhosale",
    "addon_url": "https://github.com/yourusername/emailComposer",
    "addon_docFileName": "readme",
    "addon_minimumNVDAVersion": "2023.1.0",
    "addon_lastTestedNVDAVersion": "2026.1.0",
    "addon_updateChannel": "stable",
    "addon_license": "GPL v2",
    "addon_copyright": "Copyright (C) 2024 Kasturi Bhosale",
    "versionNumber": "2.0.0",
    "addon_changelog": ""  # ← ADD THIS LINE
}

baseLanguage = "en"
markdownExtensions = ["toc", "smarty", "nl2br", "sane_lists"]
excludedFiles = [".git*", ".sconsign.dblite", "*.pyc", "*.pyo", "__pycache__", "*.nvda-addon"]
pythonSources = ["globalPlugins/*.py", "globalPlugins/**/*.py"]
i18nSources = ["globalPlugins/*.py", "globalPlugins/**/*.py"]
brailleTables = []
symbolDictionaries = []
speechDictionaries = []