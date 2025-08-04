import os
import fitz  # PyMuPDF
from PIL import Image, ImageChops
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import shutil
import customtkinter as ctk

CONFIG_FILE = 'config.json'

# ------------------ CONFIG ------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"input_folder": "", "output_folder": ""}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

# ------------------ CONVERSIÓN ------------------
def is_blank_image(image, threshold=10):
    bg = Image.new(image.mode, image.size, 255)
    diff = ImageChops.difference(image, bg)
    extrema = diff.getextrema()
    if extrema is None:
        return True
    if isinstance(extrema[0], int):
        return extrema[1] < threshold
    return extrema[0][1] < threshold

def process_file(file_path, output_folder):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(output_folder, f"{filename}_VUCEM.pdf")
    original_removed = False

    if file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)
        new_doc = fitz.open()
        for page in doc:
            pix = page.get_pixmap(dpi=300, colorspace=fitz.csGRAY, alpha=False)
            if pix.width <= 0 or pix.height <= 0:
                continue
            img = Image.frombytes("L", [pix.width, pix.height], pix.samples)
            if is_blank_image(img):
                continue
            img_pdf = fitz.open()
            img_pdf.insert_page(0, width=pix.width, height=pix.height)
            img_pdf[0].insert_image(img_pdf[0].rect, pixmap=pix, overlay=True)
            new_doc.insert_pdf(img_pdf)
        if new_doc.page_count > 0:
            new_doc.save(output_path, deflate=True)
            original_removed = True
        new_doc.close()
        doc.close()

    elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
        img = Image.open(file_path).convert('L')
        if img.width <= 0 or img.height <= 0:
            return
        if is_blank_image(img):
            return
        dpi = img.info.get('dpi', (72, 72))
        img = img.resize((int(img.width * 300 / dpi[0]), int(img.height * 300 / dpi[1])))
        img.save(output_path, dpi=(300, 300))
        original_removed = True

    if original_removed:
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"No se pudo eliminar el archivo original {file_path}: {e}")

# ------------------ INTERFAZ ------------------
class VUCEMConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Convertidor PDF/Imagen a formato VUCEM")
        self.geometry("600x360")
        self.resizable(False, False)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.config = load_config()

        self.input_var = tk.StringVar(value=self.config.get("input_folder", ""))
        self.output_var = tk.StringVar(value=self.config.get("output_folder", ""))

        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Carpeta de entrada:").pack(pady=(20, 5))
        ctk.CTkEntry(self, textvariable=self.input_var, width=400).pack()
        ctk.CTkButton(self, text="Seleccionar", command=self.select_input_folder).pack(pady=5)

        ctk.CTkLabel(self, text="Carpeta de salida:").pack(pady=(20, 5))
        ctk.CTkEntry(self, textvariable=self.output_var, width=400).pack()
        ctk.CTkButton(self, text="Seleccionar", command=self.select_output_folder).pack(pady=5)

        ctk.CTkButton(self, text="Procesar Archivos", command=self.process_files).pack(pady=10)
        ctk.CTkButton(self, text="Borrar Archivos de Salida", command=self.clear_output_folder).pack(pady=5)
        ctk.CTkButton(self, text="Cerrar", command=self.quit).pack(pady=10)

    def select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_var.set(folder)
            self.config["input_folder"] = folder
            save_config(self.config)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_var.set(folder)
            self.config["output_folder"] = folder
            save_config(self.config)

    def process_files(self):
        input_folder = self.input_var.get()
        output_folder = self.output_var.get()
        if not os.path.isdir(input_folder) or not os.path.isdir(output_folder):
            messagebox.showerror("Error", "Verifica las carpetas seleccionadas")
            return

        files = [f for f in os.listdir(input_folder) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))]
        if not files:
            messagebox.showinfo("Sin archivos", "No se encontraron archivos válidos en la carpeta de entrada.")
            return

        for file in files:
            try:
                process_file(os.path.join(input_folder, file), output_folder)
            except Exception as e:
                print(f"Error procesando {file}: {e}")

        messagebox.showinfo("Completado", "Conversión finalizada.")

    def clear_output_folder(self):
        folder = self.output_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Selecciona una carpeta de salida válida")
            return
        for file in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, file))
            except:
                pass
        messagebox.showinfo("Listo", "Archivos eliminados.")

if __name__ == '__main__':
    app = VUCEMConverterApp()
    app.mainloop()


