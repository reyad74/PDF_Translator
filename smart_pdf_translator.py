import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image
import io, os

# ---------------- Function: Translate while keeping layout ----------------
def translate_pdf_preserve_layout(input_pdf, source_lang, target_lang, output_pdf):
    doc = fitz.open(input_pdf)
    output = fitz.open()

    translator = GoogleTranslator(source=source_lang, target=target_lang)

    for page_num, page in enumerate(doc, start=1):
        text_blocks = page.get_text("blocks")  # text + layout blocks
        image_list = page.get_images(full=True)

        # Create blank page same size
        new_page = output.new_page(width=page.rect.width, height=page.rect.height)

        # Draw background image
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img_stream = io.BytesIO()
        img.save(img_stream, format="PNG")
        new_page.insert_image(page.rect, stream=img_stream.getvalue())

        # Translate text blocks on top
        for block in text_blocks:
            x0, y0, x1, y1, text, *_ = block
            if text.strip():
                try:
                    translated_text = translator.translate(text)
                except:
                    translated_text = text

                rect = fitz.Rect(x0, y0, x1, y1)
                new_page.insert_textbox(rect, translated_text, fontsize=10, color=(0, 0, 0))

        print(f"✅ Page {page_num} translated")

    output.save(output_pdf)
    output.close()
    doc.close()

# ---------------- GUI Section ----------------
def open_pdf():
    file_path = filedialog.askopenfilename(
        title="Select a PDF File",
        filetypes=[("PDF files", "*.pdf")]
    )
    if file_path:
        entry_pdf_path.delete(0, END)
        entry_pdf_path.insert(0, file_path)

def process_translation():
    input_path = entry_pdf_path.get()
    src_lang = entry_source_lang.get()
    tgt_lang = entry_target_lang.get()

    if not input_path or not src_lang or not tgt_lang:
        messagebox.showerror("Error", "⚠️ Please select file and language codes first!")
        return

    output_path = filedialog.asksaveasfilename(
        title="Save Translated PDF As",
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")]
    )

    if not output_path:
        return

    try:
        messagebox.showinfo("Processing", "Translation started... This may take some time ⏳")
        translate_pdf_preserve_layout(input_path, src_lang, tgt_lang, output_path)
        messagebox.showinfo("Success", f"✅ Translation complete!\nSaved to:\n{output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong!\n\n{e}")

# ---------------- UI ----------------
root = Tk()
root.title("🌍 Smart PDF Translator (Preserve Layout)")
root.geometry("600x420")
root.resizable(False, False)
root.config(bg="#f0f4ff")

Label(root, text="🌍 Smart PDF Translator", font=("Helvetica", 18, "bold"), bg="#f0f4ff", fg="#2a4d9b").pack(pady=15)

frame = Frame(root, bg="#f0f4ff")
frame.pack(pady=10)

Label(frame, text="Select PDF File:", font=("Helvetica", 11), bg="#f0f4ff").grid(row=0, column=0, padx=5, pady=5, sticky=E)
entry_pdf_path = Entry(frame, width=40)
entry_pdf_path.grid(row=0, column=1, padx=5, pady=5)
Button(frame, text="Browse", command=open_pdf, bg="#3f83f8", fg="white").grid(row=0, column=2, padx=5)

Label(frame, text="Source Language Code:", font=("Helvetica", 11), bg="#f0f4ff").grid(row=1, column=0, padx=5, pady=5, sticky=E)
entry_source_lang = Entry(frame, width=20)
entry_source_lang.grid(row=1, column=1, padx=5, pady=5)
entry_source_lang.insert(0, "auto")

Label(frame, text="Target Language Code:", font=("Helvetica", 11), bg="#f0f4ff").grid(row=2, column=0, padx=5, pady=5, sticky=E)
entry_target_lang = Entry(frame, width=20)
entry_target_lang.grid(row=2, column=1, padx=5, pady=5)
entry_target_lang.insert(0, "bn")  # Default Bangla

Button(root, text="🚀 Translate & Save PDF", command=process_translation, bg="#2196F3", fg="white", font=("Helvetica", 12, "bold")).pack(pady=25)

Label(root, text="Supports unlimited pages | Keeps format & images intact", font=("Helvetica", 9), bg="#f0f4ff", fg="#666").pack()

root.mainloop()
