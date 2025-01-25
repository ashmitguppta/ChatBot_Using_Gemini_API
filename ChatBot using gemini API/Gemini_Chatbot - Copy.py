"""
Prequisite:- Go to the google API and click on create new Project.
Link:- https://aistudio.google.com/prompts/
Get an Gemini API Key and save into your device.
install all the Libraries using pip install <Library_name>
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import google.generativeai as genai
import os
from datetime import datetime
from PIL import Image, ImageTk
import json  # Import json for saving/loading chats
from threading import Thread
import time
import uuid
from tkinter import font

# download this file given link in folder 
CHAT_HISTORY_FILE = "gemini_chat_history.json"

#This is the class for Gemini API with a small framework
class GeminiChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Chat")
        self.root.geometry("900x700")  # Increased window size
        self.root.minsize(800, 600)

        # Initialize Gemini
        self.api_key = self._get_api_key()
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.chat = None
        self.chat_history = self._load_chat_history()
        self.current_chat_id = None
        self.selected_chat = None
        self.chat_id_to_message_ids = {}

        self.create_styles()
        self.create_widgets()

    def _get_api_key(self):
        api_key = os.getenv("API_KEY") #enter Your API Key
        if not api_key:
            api_key = simpledialog.askstring(
                "API Key", "Please enter your Google API Key:", show="*"
            )
            if not api_key:
                messagebox.showerror("Error", "API Key is required.")
                self.root.destroy()
                return None

        return api_key

    def create_styles(self):
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TButton", font=("Arial", 12))
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("Chat.TFrame", background="#FFFFFF")
        self.style.configure(
            "Chat.TLabel", font=("Arial", 12), background="#FFFFFF", wraplength=500
        )
        self.style.configure("Send.TButton", font=("Arial", 12), background="#d9ead3")
        self.style.configure("ChatList.TFrame", background="#f8f8f8")
        self.style.configure("ChatList.TLabel", font=("Arial", 11))
        self.style.configure(
            "History.TLabel", font=("Arial", 12), background="#e8f5e9"
        )

        self.style.configure("Transparent.TButton", font=("Arial", 12))

    def create_widgets(self):
        # Main layout using grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Left Pane - Chat List
        self.chat_list_frame = ttk.Frame(self.root, style="ChatList.TFrame")
        self.chat_list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.chat_list_frame.grid_rowconfigure(0, weight=0)  # Make the title occupy its space
        self.chat_list_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        self.chat_list_title = ttk.Label(
            self.chat_list_frame, text="Chats", font=("Arial", 16, "bold")
        )
        self.chat_list_title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")


        self.chat_list_canvas = tk.Canvas(self.chat_list_frame, bg="#f8f8f8", highlightthickness=0)
        self.chat_list_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Scrollbar for Chat list
        chat_list_scrollbar = ttk.Scrollbar(self.chat_list_frame, orient=tk.VERTICAL, command=self.chat_list_canvas.yview)
        chat_list_scrollbar.grid(row=1, column=1, sticky="ns")
        
        self.chat_list_canvas.config(yscrollcommand=chat_list_scrollbar.set)
        self.chat_list_frame.grid_rowconfigure(1, weight=1)
        
        self.chat_list_inner_frame = ttk.Frame(self.chat_list_canvas, style="ChatList.TFrame")
        self.chat_list_canvas.create_window((0, 0), window=self.chat_list_inner_frame, anchor="nw", tags="inner_frame")

        self.chat_list_inner_frame.bind("<Configure>", lambda e: self.chat_list_canvas.config(scrollregion=self.chat_list_canvas.bbox("all")))
        self.chat_list_canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.chat_list_canvas.bind('<Leave>', self._unbound_to_mousewheel)
        self.load_chat_list()
        
        # New Chat Button
        new_chat_button = ttk.Button(
            self.chat_list_frame, text="New Chat", command=self.new_chat, style="TButton"
        )
        new_chat_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # Right Pane - Chat Area
        self.chat_area_frame = ttk.Frame(self.root, style="Chat.TFrame")
        self.chat_area_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.chat_area_frame.grid_columnconfigure(0, weight=1)
        self.chat_area_frame.grid_rowconfigure(0, weight=1)

        # Chat display area
        self.chat_display_canvas = tk.Canvas(self.chat_area_frame, bg="#FFFFFF", highlightthickness=0)
        self.chat_display_canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.chat_area_frame, orient=tk.VERTICAL, command=self.chat_display_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.chat_display_canvas.config(yscrollcommand=self.scrollbar.set)
        
        self.chat_inner_frame = ttk.Frame(self.chat_display_canvas, style="Chat.TFrame")
        self.chat_display_canvas.create_window((0, 0), window=self.chat_inner_frame, anchor="nw", tags="inner_frame")
        self.chat_inner_frame.bind("<Configure>", lambda e: self.chat_display_canvas.config(scrollregion=self.chat_display_canvas.bbox("all")))
        self.chat_display_canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.chat_display_canvas.bind('<Leave>', self._unbound_to_mousewheel)


        # Input frame at the bottom of the chat area
        self.input_frame = ttk.Frame(self.chat_area_frame, style="Chat.TFrame")
        self.input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=0)


        self.input_text = tk.Text(
            self.input_frame,
            height=3,
            wrap="word",
            font=("Arial", 12),
            highlightbackground="#CCCCCC",
            highlightthickness=1,
            borderwidth=1,
        )
        self.input_text.grid(row=0, column=0, sticky="ew", padx=5)

        # Send Button
        self.send_button = ttk.Button(
            self.input_frame, text="Send", command=self.send_message, style="Send.TButton"
        )
        self.send_button.grid(row=0, column=1, padx=5)
        
    def _bound_to_mousewheel(self, event):
        self.chat_display_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.chat_display_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.chat_display_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _load_chat_history(self):
        try:
            if os.path.exists(CHAT_HISTORY_FILE):
                with open(CHAT_HISTORY_FILE, "r") as f:
                    return json.load(f)
            else:
                return {}  # Return an empty dict if file does not exist
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return {}

    def _save_chat_history(self):
        try:
            with open(CHAT_HISTORY_FILE, "w") as f:
                json.dump(self.chat_history, f, indent=4)
        except Exception as e:
            print(f"Error saving chat history: {e}")

    def load_chat_list(self):
        # Clear existing chat buttons first
        for widget in self.chat_list_inner_frame.winfo_children():
            widget.destroy()

        if not self.chat_history:
            ttk.Label(self.chat_list_inner_frame, text="No chats yet.").grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            return
            
        for i, chat_id in enumerate(reversed(self.chat_history.keys())):
            chat_data = self.chat_history[chat_id]
            chat_title = chat_data.get("title", f"Chat {i + 1}")  # Provide a default title
            if len(chat_title) > 30:
                chat_title = chat_title[:30] + "..."

            chat_button = ttk.Button(
                self.chat_list_inner_frame,
                text=chat_title,
                command=lambda id=chat_id: self.load_chat(id),
                style="Transparent.TButton"
            )
            chat_button.grid(row=i, column=0, sticky="ew", padx=10, pady=5)

            # Make the buttons expand to take up horizontal space
            self.chat_list_inner_frame.grid_columnconfigure(0, weight=1)


    def load_chat(self, chat_id):
        self.current_chat_id = chat_id
        self.selected_chat = self.chat_history[chat_id]  # Store the current selected chat

        # Clear the chat display before loading new chat
        for widget in self.chat_inner_frame.winfo_children():
            widget.destroy()

        if self.selected_chat and "messages" in self.selected_chat:
            for message_id, message in self.selected_chat["messages"].items():
                self.add_message_to_chat(message["text"], message["sender"])
        self.scroll_chat_to_bottom()  # Scroll to the latest message

    def new_chat(self):
        self.current_chat_id = str(uuid.uuid4())
        self.chat_history[self.current_chat_id] = {
            "title": f"New Chat",
            "messages": {},
            "created_at": datetime.now().isoformat(),
            }
        self._save_chat_history()
        self.load_chat_list()
        self.load_chat(self.current_chat_id)

    def _get_chat_title_from_messages(self):
            if self.current_chat_id and self.chat_history[self.current_chat_id].get("messages", {}):
                first_message = next(iter(self.chat_history[self.current_chat_id]["messages"].values()))
                if first_message:
                    first_message_text = first_message["text"]
                    title_end_index = min(40, len(first_message_text))
                    return f"{first_message_text[:title_end_index]}..."
            return "New Chat"

    def send_message(self):
        if not self.current_chat_id:
            messagebox.showinfo("Info", "Please start a new chat or select an existing one.")
            return

        user_message = self.input_text.get("1.0", tk.END).strip()
        if not user_message:
            return
        
        self.add_message_to_chat(user_message, "user")
        self.input_text.delete("1.0", tk.END)

        Thread(target=self.get_gemini_response, args=(user_message,)).start()

    def add_message_to_chat(self, text, sender):
        
        if not self.current_chat_id:
            return
        
        
        message_id = str(uuid.uuid4())  # Generate a unique message ID

        if self.current_chat_id not in self.chat_id_to_message_ids:
            self.chat_id_to_message_ids[self.current_chat_id] = []

        self.chat_id_to_message_ids[self.current_chat_id].append(message_id)


        if sender == "user":
            frame_style = "Chat.TFrame"
            label_style = "Chat.TLabel"
            color = "#d9ead3"  # User message color
            text_start = "You: \n"

        else:
            frame_style = "Chat.TFrame"
            label_style = "Chat.TLabel"
            color = "#f0f0f0"  # Gemini response color
            text_start = "Gemini: \n"

        message_frame = ttk.Frame(self.chat_inner_frame, style=frame_style)
        message_frame.pack(pady=5, padx=10, fill=tk.X, anchor='w' if sender == 'user' else 'e')

        message_label = ttk.Label(
            message_frame, text=f"{text_start}{text}", style=label_style, background=color, wraplength=500
        )
        message_label.pack(pady=5, padx=10, fill=tk.X)
        
        # Append the message to chat history. create a new message
        if self.current_chat_id not in self.chat_history:
           self.chat_history[self.current_chat_id] = {
              "title": f"New Chat",
              "messages": {},
              "created_at": datetime.now().isoformat(),
           }

        if "messages" not in self.chat_history[self.current_chat_id]:
              self.chat_history[self.current_chat_id]["messages"] = {}
           
        self.chat_history[self.current_chat_id]["messages"][message_id] = {"text": text, "sender": sender, "created_at": datetime.now().isoformat()}
        self._save_chat_history()
        self.scroll_chat_to_bottom()
        self.update_chat_title()

    def update_chat_title(self):
        if self.current_chat_id:
            new_title = self._get_chat_title_from_messages()
            self.chat_history[self.current_chat_id]["title"] = new_title
            self._save_chat_history()
            self.load_chat_list()
    

    def get_gemini_response(self, user_message):
        try:
            if not self.chat:
                self.chat = self.model.start_chat()

            response = self.chat.send_message(user_message)
            self.add_message_to_chat(response.text, "gemini")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get response: {e}")

    def scroll_chat_to_bottom(self):
        self.chat_display_canvas.update_idletasks()  # Wait for updates
        self.chat_display_canvas.yview_moveto(1)


if __name__ == "__main__":
    root = tk.Tk()
    app = GeminiChatApp(root)
    root.mainloop()