# @title Install EPI (v2.6.0 with Gemini Support) { display-mode: "form" }
import sys, os, subprocess
from IPython.display import clear_output, display, HTML

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--upgrade",
                       "epi-recorder", "google-generativeai"])
clear_output()

print("=" * 70)
display(HTML('<h2 style="color: #10b981;">EPI v2.6.0 Installed (Gemini-Ready)</h2>'))
print("=" * 70)

api_key = None
try:
    from google.colab import userdata
    api_key = userdata.get('GOOGLE_API_KEY')
except:
    pass

if not api_key:
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    display(HTML('<p style="color: #10b981; font-weight: bold;">API Key Found</p>'))
else:
    display(HTML('''
    <div style="background: #fef3c7; border: 2px solid #f59e0b; padding: 20px; border-radius: 12px; margin: 20px 0;">
        <h3 style="color: #92400e; margin: 0 0 10px 0;">API Key Optional</h3>
        <p style="color: #78350f; margin: 0;">Demo mode runs without a key. For live Gemini calls:</p>
        <ol style="color: #78350f; margin: 10px 0;">
            <li>Get a free key at: <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
            <li>Click the <b>Key</b> icon in the Colab sidebar</li>
            <li>Add a secret named <code>GOOGLE_API_KEY</code></li>
            <li><b>Enable notebook access</b></li>
        </ol>
    </div>
    '''))
