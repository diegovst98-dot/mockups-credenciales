# -*- coding: utf-8 -*-
"""
Mockups DISECOD — interfaz para el vendedor.
Elegir logo + nombre del cliente + Generar. Los resultados se abren solos.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox

import motor

LILA = "#9987F7"
LILA_OSCURO = "#7A66E8"
GRIS = "#383838"
FONDO = "#FFFFFF"


class App:
    def __init__(self, raiz):
        self.raiz = raiz
        self.ruta_logo = None
        raiz.title("Mockups DISECOD")
        raiz.configure(bg=FONDO)
        raiz.geometry("560x420")
        raiz.resizable(False, False)
        try:
            raiz.iconbitmap(os.path.join(motor.RUTA_RECURSOS, "icono.ico"))
        except Exception:
            pass

        f_titulo = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        f_normal = tkfont.Font(family="Segoe UI", size=11)
        f_boton = tkfont.Font(family="Segoe UI", size=13, weight="bold")

        tk.Label(raiz, text="Mockups de fotochecks", font=f_titulo, bg=FONDO, fg=GRIS).pack(pady=(28, 2))
        tk.Label(raiz, text="Logo del cliente  →  3 propuestas listas para WhatsApp",
                 font=f_normal, bg=FONDO, fg="#777").pack(pady=(0, 20))

        marco = tk.Frame(raiz, bg=FONDO)
        marco.pack(fill="x", padx=48)

        tk.Label(marco, text="Nombre de la empresa cliente", font=f_normal, bg=FONDO, fg=GRIS, anchor="w").pack(fill="x")
        self.entrada_cliente = tk.Entry(marco, font=f_normal, relief="solid", bd=1)
        self.entrada_cliente.pack(fill="x", ipady=6, pady=(4, 14))

        fila = tk.Frame(marco, bg=FONDO)
        fila.pack(fill="x")
        self.boton_logo = tk.Button(fila, text="Elegir logo…", font=f_normal, command=self.elegir_logo,
                                    bg="#EEEAFE", fg=GRIS, activebackground="#E2DBFD", relief="flat", padx=14, pady=6)
        self.boton_logo.pack(side="left")
        self.etiqueta_logo = tk.Label(fila, text="ningún archivo elegido", font=f_normal, bg=FONDO, fg="#999")
        self.etiqueta_logo.pack(side="left", padx=10)

        self.boton_generar = tk.Button(raiz, text="Generar mockups", font=f_boton, command=self.generar,
                                       bg=LILA, fg="white", activebackground=LILA_OSCURO,
                                       activeforeground="white", relief="flat", padx=24, pady=10,
                                       cursor="hand2")
        self.boton_generar.pack(pady=26)

        self.estado = tk.Label(raiz, text="", font=f_normal, bg=FONDO, fg=GRIS)
        self.estado.pack()

        tk.Label(raiz, text="DISECOD · www.fotochecks.pe", font=f_normal, bg=FONDO, fg="#BBB").pack(side="bottom", pady=10)

    def elegir_logo(self):
        ruta = filedialog.askopenfilename(
            title="Elige el logo del cliente",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos", "*.*")])
        if ruta:
            self.ruta_logo = ruta
            self.etiqueta_logo.config(text=os.path.basename(ruta), fg=GRIS)

    def generar(self):
        cliente = self.entrada_cliente.get().strip()
        if not self.ruta_logo:
            messagebox.showwarning("Falta el logo", "Primero elige el logo del cliente.")
            return
        if not cliente:
            messagebox.showwarning("Falta el nombre", "Escribe el nombre de la empresa cliente.")
            return
        self.boton_generar.config(state="disabled", text="Generando…")
        self.estado.config(text="Creando las 3 propuestas, dame unos segundos…")
        threading.Thread(target=self._trabajo, args=(cliente,), daemon=True).start()

    def _trabajo(self, cliente):
        try:
            carpeta, _ = motor.generar(self.ruta_logo, cliente)
            self.raiz.after(0, self._listo, carpeta)
        except Exception as e:
            self.raiz.after(0, self._error, str(e))

    def _listo(self, carpeta):
        self.boton_generar.config(state="normal", text="Generar mockups")
        self.estado.config(text="¡Listo! Se abrió la carpeta con los mockups. ✓")
        os.startfile(carpeta)

    def _error(self, mensaje):
        self.boton_generar.config(state="normal", text="Generar mockups")
        self.estado.config(text="")
        messagebox.showerror("No se pudo generar",
                             f"Revisa que el logo sea una imagen válida.\n\nDetalle: {mensaje}")


def main():
    # modo consola opcional: MockupsDISECOD.exe logo.png "Cliente"
    if len(sys.argv) >= 3:
        carpeta, _ = motor.generar(sys.argv[1], sys.argv[2])
        print(carpeta)
        return
    raiz = tk.Tk()
    App(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
