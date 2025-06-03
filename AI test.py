import tkinter as tk
from tkinter import ttk, messagebox
import requests
import datetime
from dotenv import load_dotenv
import os
from jarvisrecognizeandconvert import *
import jarvispeak

load_dotenv()

API_KEYS = {
    "Express": os.getenv("OPENROUTER_API_KEY"),
    "Advanced": os.getenv("OPENROUTER_API_KEY")
}

def call_api(model_key, prompt):
    headers = {}
    api_key = API_KEYS.get(model_key)
    classify = """You have to split the following text into the following categories in this format:
1st category is the intro or mostly the first line of the text and it is to be spoken
2nd category is the program or code content in the text
3rd category is to give all other content in the text that is not spoken or code content
and all these categories should be given in the following format (EXACTLY THIS FORMAT):
<INTRO>*&$<CODE>!@^<OTHER>
Text: """

    if model_key in API_KEYS:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Organization": "openrouter"
        }
        data = {
            "model": "google/gemma-3-27b-it:free",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=15)
            response.raise_for_status()
            result = response.json()

            # Now classify the response
            classify_data = {
                "model": "google/gemma-3-27b-it:free",
                "messages": [{"role": "user", "content": classify + result['choices'][0]['message']['content'].strip()}]
            }
            classify_response = requests.post(url, json=classify_data, headers=headers, timeout=15)
            classify_response.raise_for_status()
            classify_result = classify_response.json()
            return classify_result['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"API call failed: {str(e)}"
    else:
        return "Invalid model selected."

def log_interaction(user_input, output):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("ai_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp}\nINPUT:\n{user_input}\nOUTPUT:\n{output}\n{'-'*40}\n")

class AIApp:
    def __init__(self, root):
        self.root = root
        root.title("J.A.R.V.I.S. AI System")
        root.geometry("1920x1080")
        root.configure(bg="#0f1117")

        # Left-most program output box (like a code console)
        self.code_output_frame = tk.Frame(root, bg="#1a1a1a", width=384)
        self.code_output_frame.pack(side="left", fill="y")
        self.code_output_frame.pack_propagate(False)

        self.code_output_text = tk.Text(self.code_output_frame, bg="#000000", fg="#00ff99", insertbackground="#00ff99",
                                        font=("Consolas", 11), wrap="word")
        self.code_output_text.pack(fill="both", expand=True)

        # Center written text area (invisible if empty)
        self.main_output_text = tk.Text(root, bg="#111a22", fg="#f0f0f0", insertbackground="#00ffe0",
                                        font=("Courier New", 12), wrap="word")
        self.main_output_text.pack(side="left", fill="both", expand=True)
        self.main_output_text.pack_forget()  # Initially invisible

        # Right sidebar
        self.sidebar = tk.Frame(root, bg="#141924", width=384)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(self.sidebar, textvariable=self.model_var, state="readonly", values=list(API_KEYS.keys()))
        self.model_combo.current(0)
        self.model_combo.pack(pady=10, padx=20, fill="x")

        self.speech_var = tk.StringVar(value="text")
        self.speech_radio_frame = tk.Frame(self.sidebar, bg="#141924")
        self.speech_radio_frame.pack(pady=(10, 5), padx=20, anchor="w")
        ttk.Radiobutton(self.speech_radio_frame, text="Text", variable=self.speech_var, value="text").pack(side="left")
        ttk.Radiobutton(self.speech_radio_frame, text="Speech", variable=self.speech_var, value="speech").pack(side="left")

        self.input_label = tk.Label(self.sidebar, text="Enter your query:", fg="#00ffe0", bg="#141924", font=("Consolas", 12, "bold"))
        self.input_label.pack(pady=(30, 5), padx=20, anchor="w")

        self.input_text = tk.Text(self.sidebar, height=5, bg="#2b2b2b", fg="#ffffff", insertbackground="#00ffe0", font=("Consolas", 11))
        self.input_text.pack(padx=20, fill="x")

        self.submit_button = ttk.Button(self.sidebar, text="Submit", command=self.process_input)
        self.submit_button.pack(pady=10, padx=20, fill="x")

        self.intro_label = tk.Label(self.sidebar, text="Spoken Intro:", fg="#00ffe0", bg="#141924", font=("Consolas", 12, "bold"))
        self.intro_label.pack(pady=(20, 5), padx=20, anchor="w")

        self.spoken_intro_text = tk.Text(self.sidebar, height=5, bg="#0f0f0f", fg="#00ffcc", insertbackground="#00ffcc",
                                         font=("Courier New", 10), wrap="word", state="disabled")
        self.spoken_intro_text.pack(padx=20, fill="both", expand=True)

    def process_input(self):
        mode = self.speech_var.get()
        user_input = self.input_text.get("1.0", "end").strip()
        if mode == "speech":
            user_input = Recognize()
            if user_input.lower() == "none":
                messagebox.showwarning("Speech Error", "No input recognized. Please try again.")
                return

        if not user_input:
            messagebox.showwarning("Input Error", "Please enter or speak some text!")
            return

        model_key = self.model_var.get()
        result = call_api(model_key, user_input)

        if "*&$" in result and "!@^" in result:
            intro, remainder = result.split("*&$", 1)
            code, other = remainder.split("!@^", 1)
        else:
            intro, code, other = "Could not parse result.", "", result

        # Update intro and speak
        self.spoken_intro_text.configure(state="normal")
        self.spoken_intro_text.delete("1.0", "end")
        self.spoken_intro_text.insert("end", intro.strip())
        self.spoken_intro_text.configure(state="disabled")
        jarvispeak.speak(intro.strip())

        # Update code
        self.code_output_text.delete("1.0", "end")
        self.code_output_text.insert("end", code.strip())

        # Update main written text
        if other.strip():
            self.main_output_text.pack(side="left", fill="both", expand=True)
            self.main_output_text.delete("1.0", "end")
            self.main_output_text.insert("end", other.strip())
            self.main_output_text.see("end")
        else:
            self.main_output_text.pack_forget()

        log_interaction(user_input, result)

if __name__ == "__main__":
    root = tk.Tk()
    app = AIApp(root)
    root.mainloop()

# create exe (pyinstaller --onefile --windowed your_script_name.py)
"""
Optinal Debugging:-
for k, v in API_KEYS.items():
    if not v:
        print(f"Warning: API key for {k} not found! Check your .env file.")
"""