import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz  # PyMuPDF
from googletrans import Translator, LANGUAGES
import os
import threading
import time
import sys

# --- FONT & REPORTLAB SETUP ---
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ফন্ট ভেরিয়েবল (এগুলি কেবল অ-ল্যাটিন ভাষার জন্য ব্যবহৃত হবে)
BENGALI_FONT_NAME = 'NotoSansBengali'
TARGET_FONT_FILENAME = 'NotoSansBengali-Regular.ttf' 
FALLBACK_FONT_NAME = 'Times-Roman'

def is_latin_script(lang_code):
    """চেক করে ভাষাটি ল্যাটিন স্ক্রিপ্ট ব্যবহার করে কিনা"""
    # কিছু সাধারণ নন-ল্যাটিন স্ক্রিপ্ট
    non_latin_scripts = ['ar', 'zh', 'ja', 'ko', 'bn', 'hi', 'ru', 'th', 'el']
    return lang_code not in non_latin_scripts

def find_and_register_font(target_lang_code):
    """টার্গেট ভাষার জন্য উপযুক্ত ফন্ট খুঁজে বের করে এবং রিপোর্টল্যাব-এ রেজিস্টার করে"""
    
    # যদি ল্যাটিন স্ক্রিপ্ট হয়, তবে ডিফল্ট ReportLab ফন্ট ব্যবহার করা হয়
    if is_latin_script(target_lang_code):
        return FALLBACK_FONT_NAME
        
    # নন-ল্যাটিন স্ক্রিপ্ট হলে, ফন্ট খোঁজা হয় (বিশেষ করে বাংলার জন্য)
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    windows_fonts_dir = 'C:\\Windows\\Fonts'
    
    # সম্ভাব্য বাংলা ফন্ট পাথ (অন্যান্য ভাষার জন্য এই তালিকা বাড়ানো যেতে পারে)
    possible_paths = [
        os.path.join(current_dir, TARGET_FONT_FILENAME),
        os.path.join(windows_fonts_dir, TARGET_FONT_FILENAME),
        os.path.join(windows_fonts_dir, 'solaimanlipi.ttf'),
        os.path.join(windows_fonts_dir, 'kalpurush.ttf'),
    ]
    
    found_font_path = None
    for path in possible_paths:
        if os.path.exists(path):
            found_font_path = path
            break

    if found_font_path:
        try:
            # ইউনিকোড ফন্ট রেজিস্টার করা
            pdfmetrics.registerFont(TTFont(BENGALI_FONT_NAME, found_font_path))
            return BENGALI_FONT_NAME
        except Exception as e:
            print(f"Error registering font at {found_font_path}: {e}")
            return FALLBACK_FONT_NAME # ফলব্যাক
    else:
        return FALLBACK_FONT_NAME # ফলব্যাক


# --- Global Variables & Constants ---
PDF_FILE_PATH = ""
CHUNK_SIZE = 4000 
SOURCE_LANG_CODE = ""

# --- Core Functions ---

def get_text_from_pdf(pdf_path):
    """PDF ফাইল থেকে টেক্সট এক্সট্রাক্ট করে এবং মোটামুটি প্যারাগ্রাফ ব্রেক সংরক্ষণ করে"""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            # অতিরিক্ত নতুন লাইন যোগ করা যাতে প্যারাগ্রাফ ব্রেকগুলি সংরক্ষিত হয়
            text += page.get_text() + "\n\n" 
        doc.close()
        return text
    except Exception as e:
        messagebox.showerror("PDF Error", f"Failed to read PDF: {e}")
        return None

def split_text_into_chunks(text, size):
    """টেক্সটকে একটি নির্দিষ্ট আকারের ছোট ছোট অংশে ভাগ করে (Splits text into smaller chunks)"""
    chunks = []
    for i in range(0, len(text), size):
        chunks.append(text[i:i + size])
    return chunks

def detect_source_language(text):
    """টেক্সট-এর সোর্স ভাষা স্বয়ংক্রিয়ভাবে চিহ্নিত করে (Automatically detects the source language)"""
    try:
        translator = Translator()
        # শুধু প্রথম ২০০০ অক্ষর ব্যবহার করা হয় ডিটেকশনের জন্য
        detection = translator.detect(text[:2000])
        return detection.lang
    except Exception as e:
        print(f"Language detection failed: {e}")
        return 'en' # ফলব্যাক হিসেবে ইংরেজি

def translate_in_chunks(text, target_lang_code, max_retries=3):
    """টেক্সটকে ছোট ছোট অংশে ভাগ করে অনুবাদ করে এবং পুনঃসংযোগ করে (Translates text in chunks)"""
    
    global SOURCE_LANG_CODE
    
    # 0. সোর্স ভাষা চিহ্নিত করা
    SOURCE_LANG_CODE = detect_source_language(text)
    source_lang_name = LANGUAGES_MAPPING.get(SOURCE_LANG_CODE, SOURCE_LANG_CODE).capitalize()
    
    root.after(0, pdf_path_label.config, {'text': f"File: {os.path.basename(PDF_FILE_PATH)} | Source: {source_lang_name}", 'style': 'Blue.Italic.TLabel'})
    
    chunks = split_text_into_chunks(text, CHUNK_SIZE)
    translated_chunks = []
    
    for i, chunk in enumerate(chunks):
        
        # UI স্ট্যাটাস আপডেট করা
        root.after(0, status_label.config, {'text': f"Status: Translating {i + 1} of {len(chunks)} chunks from {source_lang_name}...", 'style': 'Orange.Status.TLabel'})
        
        translated_chunk = None
        for attempt in range(max_retries):
            try:
                translator = Translator()
                if attempt > 0:
                    time.sleep(3) 
                
                translated_chunk = translator.translate(chunk, src=SOURCE_LANG_CODE, dest=target_lang_code).text
                break
            
            except Exception as e:
                print(f"Chunk {i + 1} failed (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    root.after(0, messagebox.showerror, "Translation Error", f"Translation of chunk {i + 1} failed after {max_retries} attempts. Original error: {e}")
                    return None
        
        if translated_chunk is None:
            return None 

        translated_chunks.append(translated_chunk)
        time.sleep(1) 
        
    return "".join(translated_chunks)

def save_translated_text_as_pdf(translated_text, target_lang_code):
    """অনুবাদিত টেক্সট ফাইলটিকে একটি নতুন PDF ফাইল হিসেবে সেভ করে (Saves translated text as a new PDF file)"""
    if not REPORTLAB_AVAILABLE:
        messagebox.showerror("Dependency Error", "Cannot save as PDF. Please run 'pip install reportlab' first.")
        root.after(0, reset_ui_after_process)
        return
    
    if not translated_text:
        messagebox.showwarning("Save Error", "No translated text to save.")
        root.after(0, reset_ui_after_process)
        return
        
    # টার্গেট ফন্ট নির্ধারণ করা
    final_font_to_use = find_and_register_font(target_lang_code)

    if final_font_to_use != FALLBACK_FONT_NAME and final_font_to_use != BENGALI_FONT_NAME:
         messagebox.showwarning("Font Warning", "Could not register appropriate font for the target language. Output PDF might show incorrect characters.")

    # PDF ফাইলের নাম জানতে asksaveasfilename ব্যবহার করা হয়েছে
    filename = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=(("PDF Files", "*.pdf"), ("All files", "*.*")),
        title="Save Translated PDF File"
    )
    
    if not filename:
        root.after(0, reset_ui_after_process)
        return

    try:
        # ReportLab ব্যবহার করে PDF তৈরি
        c = pdf_canvas.Canvas(filename, pagesize=letter)
        
        # ফন্ট সেট করা
        c.setFont(final_font_to_use, 12)
        
        width, height = letter # 612x792
        margin = 72 # 1 inch margin

        textobject = c.beginText(margin, height - margin)
        textobject.setFont(final_font_to_use, 12)
        
        lines = translated_text.split('\n')
        line_height = 16
        current_y = height - margin

        for line in lines:
            if current_y < margin + line_height:
                c.drawText(textobject)
                c.showPage()
                textobject = c.beginText(margin, height - margin)
                textobject.setFont(final_font_to_use, 12)
                current_y = height - margin
            
            # লাইনটি লেখা
            textobject.textLine(line)
            current_y -= line_height

        c.drawText(textobject)
        c.save()
        
        messagebox.showinfo("Success", f"Translated PDF saved successfully to:\n{filename}")
    
    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save PDF: {e}")
    
    finally:
        root.after(0, reset_ui_after_process)


# --- UI Functions ---

def browse_pdf_file():
    """ফাইল সিলেক্ট করার ডায়ালগ দেখায় এবং নির্বাচিত ফাইল পাথ আপডেট করে (Shows file dialog and updates path)"""
    global PDF_FILE_PATH
    filename = filedialog.askopenfilename(
        title="Select a PDF Book File",
        filetypes=(("PDF Files", "*.pdf"), ("All Files", "*.*"))
    )
    if filename:
        PDF_FILE_PATH = filename
        pdf_path_label.config(text=f"File: {os.path.basename(filename)}", style='Blue.Italic.TLabel')
        process_button.config(state=tk.NORMAL)
    else:
        PDF_FILE_PATH = ""
        pdf_path_label.config(text="No file selected.", style='Red.Italic.TLabel')
        process_button.config(state=tk.DISABLED)

def start_translation_process():
    """অনুবাদ প্রক্রিয়া শুরু করে এবং প্রোগ্রেস দেখায় (Starts translation and shows progress)"""
    if not PDF_FILE_PATH:
        messagebox.showwarning("Input Missing", "Please select a PDF file first.")
        return

    target_lang_name = lang_combo.get()
    if target_lang_name in ["Select Language", ""]:
        messagebox.showwarning("Input Missing", "Please select a target language.")
        return
    
    if not REPORTLAB_AVAILABLE:
        messagebox.showerror("Dependency Error", "Cannot start. Please run 'pip install reportlab' first.")
        return

    # UI উপাদানগুলি ডিজেবল করা
    process_button.config(state=tk.DISABLED, text="Processing...")
    browse_button.config(state=tk.DISABLED)
    progress_bar.config(mode='indeterminate')
    progress_bar.start()

    # ভাষা কোড খোঁজা
    target_lang_code = next((code for code, name in LANGUAGES_MAPPING.items() if name == target_lang_name), None)
    
    # ব্যাকগ্রাউন্ড থ্রেডে পুরো প্রক্রিয়াটি চালু করা (যাতে UI ফ্রিজ না হয়)
    threading.Thread(target=perform_full_process, args=(PDF_FILE_PATH, target_lang_code)).start()

def perform_full_process(pdf_path, target_lang_code):
    """ব্যাকগ্রাউন্ডে এক্সট্রাকশন, অনুবাদ এবং সেভ করার প্রক্রিয়াটি সম্পন্ন করে (Performs extraction, translation, and save)"""
    
    # 1. PDF থেকে টেক্সট এক্সট্রাক্ট
    root.after(0, status_label.config, {'text': "Status: Extracting text from PDF...", 'style': 'Orange.Status.TLabel'})
    extracted_text = get_text_from_pdf(pdf_path)
    if extracted_text is None:
        root.after(0, reset_ui_after_process)
        return

    # 2. টেক্সট অনুবাদ 
    translated_text = translate_in_chunks(extracted_text, target_lang_code)
    
    if translated_text is None:
        root.after(0, reset_ui_after_process)
        return

    # 3. ফাইল সেভ করার ডায়ালগ খোলা (PDF হিসেবে)
    root.after(0, status_label.config, {'text': "Status: Translation complete! Ready to save PDF.", 'style': 'Green.Status.TLabel'})
    # tkinter ফাংশনগুলি মেইন থ্রেডে চালানো হয়
    root.after(0, lambda: save_translated_text_as_pdf(translated_text, target_lang_code))

def reset_ui_after_process():
    """প্রক্রিয়া শেষে UI উপাদানগুলি স্বাভাবিক অবস্থায় ফিরিয়ে আনে (Resets UI after process)"""
    progress_bar.stop()
    progress_bar.config(mode='determinate', value=0)
    process_button.config(state=tk.NORMAL, text="Start Translation")
    browse_button.config(state=tk.NORMAL)
    status_label.config(text="Status: Idle", style='Gray.Status.TLabel')


# --- Main Application Setup ---

# ভাষা কোডগুলিকে সুন্দর নামে পরিবর্তন করা
LANGUAGES_MAPPING = {code: name.capitalize() for code, name in LANGUAGES.items()}

# UI তৈরি
root = tk.Tk()
root.title("Universal PDF Translator 🌐")
root.geometry("600x350")
root.resizable(False, False)

# স্টাইল সেট করা (ttk ব্যবহার করে আধুনিক লুক)
style = ttk.Style()
style.theme_use('clam')

# *** স্টাইল কনফিগারেশন ***
style.configure('Bold.TLabel', font=('Helvetica', 12, 'bold'))
style.configure('Red.Italic.TLabel', foreground='red', font=('Helvetica', 10, 'italic'))
style.configure('Blue.Italic.TLabel', foreground='blue', font=('Helvetica', 10, 'italic'))
style.configure('Gray.Status.TLabel', foreground='gray', font=('Helvetica', 10))
style.configure('Orange.Status.TLabel', foreground='orange', font=('Helvetica', 10))
style.configure('Green.Status.TLabel', foreground='green', font=('Helvetica', 10))
style.configure('Accent.TButton', font=('Helvetica', 10, 'bold'), padding=5)

# ফ্রেম তৈরি
main_frame = ttk.Frame(root, padding="20 20 20 20")
main_frame.pack(fill=tk.BOTH, expand=True)

## ১. ফাইল ইনপুট সেকশন
ttk.Label(main_frame, text="1. Import PDF Book:", style='Bold.TLabel').grid(row=0, column=0, sticky=tk.W, pady=10)

browse_button = ttk.Button(main_frame, text="Browse PDF", command=browse_pdf_file)
browse_button.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)

pdf_path_label = ttk.Label(main_frame, text="No file selected.", style='Red.Italic.TLabel')
pdf_path_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

## ২. ভাষা নির্বাচন সেকশন
ttk.Label(main_frame, text="2. Choose Target Language:", style='Bold.TLabel').grid(row=3, column=0, sticky=tk.W, pady=10)

language_names = sorted(LANGUAGES_MAPPING.values())
lang_combo = ttk.Combobox(main_frame, values=language_names, width=30, state="readonly")
lang_combo.set("Select Language") # ডিফল্ট ভ্যালু পরিবর্তন করা হয়েছে
lang_combo.grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)

ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

## ৩. প্রসেস বাটন এবং স্ট্যাটাস
process_button = ttk.Button(main_frame, text="Start Translation", command=start_translation_process, state=tk.DISABLED)
process_button.grid(row=6, column=0, columnspan=2, pady=15)

# প্রোগ্রেস বার
progress_bar = ttk.Progressbar(main_frame, orient='horizontal', length=550, mode='determinate')
progress_bar.grid(row=7, column=0, columnspan=2, pady=10)

# স্ট্যাটাস লেবেল
status_label = ttk.Label(main_frame, text="Status: Idle", style='Gray.Status.TLabel')
status_label.grid(row=8, column=0, columnspan=2, pady=5)


# গ্রিড লেআউটের জন্য কলামের ওজন সেট করা
main_frame.grid_columnconfigure(1, weight=1)

root.mainloop()
