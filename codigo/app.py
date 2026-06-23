# -*- coding: utf-8 -*-
"""
Mockups DISECOD — interfaz para el vendedor.
Pestaña 1: Mockups — logo + nombre + (opcional) color → catálogo de modelos en PDF.
Pestaña 2: Renombrar Cotizaciones (usa renombrador.py).
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, font as tkfont, messagebox, ttk

import motor

LILA = "#9987F7"
LILA_OSCURO = "#7A66E8"
GRIS = "#383838"
FONDO = "#FFFFFF"


def _version():
    """Lee version.txt (se actualiza solo por auto-update) para mostrarla en la
    interfaz: así el vendedor confirma de un vistazo si el programa ya se actualizó."""
    try:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")
        with open(ruta, encoding="utf-8") as f:
            return "v" + f.read().strip()
    except Exception:
        return "v?"


class App:
    def __init__(self, raiz):
        self.raiz = raiz
        self.ruta_logo = None
        self.color = None          # None = color automático del logo; "#RRGGBB" = manual
        raiz.title("Mockups DISECOD — %s" % _version())
        raiz.configure(bg=FONDO)
        raiz.geometry("820x600")
        raiz.resizable(False, False)
        try:
            raiz.iconbitmap(os.path.join(motor.RUTA_RECURSOS, "icono.ico"))
        except Exception:
            pass

        # --- Notebook con dos pestañas ---
        nb = ttk.Notebook(raiz)
        nb.pack(fill="both", expand=True)

        frame_mockups = tk.Frame(nb, bg=FONDO)
        frame_renombrar = tk.Frame(nb, bg=FONDO)
        nb.add(frame_mockups, text="Mockups")
        nb.add(frame_renombrar, text="Renombrar Cotizaciones")

        # --- Pestaña 1: Mockups (catálogo de modelos con la marca del cliente) ---
        f_titulo = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        f_normal = tkfont.Font(family="Segoe UI", size=11)
        f_boton = tkfont.Font(family="Segoe UI", size=13, weight="bold")

        tk.Label(frame_mockups, text="Mockups de fotochecks", font=f_titulo, bg=FONDO, fg=GRIS).pack(pady=(24, 2))
        tk.Label(frame_mockups, text="Logo del cliente  →  catálogo de modelos con su marca (PDF)",
                 font=f_normal, bg=FONDO, fg="#777").pack(pady=(0, 18))

        marco = tk.Frame(frame_mockups, bg=FONDO)
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

        fila_color = tk.Frame(marco, bg=FONDO)
        fila_color.pack(fill="x", pady=(12, 0))
        self.boton_color = tk.Button(fila_color, text="Cambiar color…", font=f_normal, command=self.elegir_color,
                                     bg="#EEEAFE", fg=GRIS, activebackground="#E2DBFD", relief="flat", padx=14, pady=6)
        self.boton_color.pack(side="left")
        self.muestra_color = tk.Label(fila_color, text="   ", bg=FONDO, relief="solid", bd=1)
        self.muestra_color.pack(side="left", padx=(10, 6))
        self.etiqueta_color = tk.Label(fila_color, text="automático del logo", font=f_normal, bg=FONDO, fg="#999")
        self.etiqueta_color.pack(side="left")

        self.boton_generar = tk.Button(frame_mockups, text="Generar catálogo", font=f_boton, command=self.generar,
                                       bg=LILA, fg="white", activebackground=LILA_OSCURO,
                                       activeforeground="white", relief="flat", padx=24, pady=10,
                                       cursor="hand2")
        self.boton_generar.pack(pady=22)

        self.estado = tk.Label(frame_mockups, text="", font=f_normal, bg=FONDO, fg=GRIS)
        self.estado.pack()

        tk.Label(frame_mockups, text="DISECOD · www.fotochecks.pe · %s" % _version(),
                 font=f_normal, bg=FONDO, fg="#BBB").pack(side="bottom", pady=10)

        # --- Pestaña 2: Renombrar Cotizaciones ---
        self._construir_renombrar(frame_renombrar)

    # ------------------------------------------------------------------ #
    # Métodos de la pestaña Mockups (catálogo + color)
    # ------------------------------------------------------------------ #

    def elegir_logo(self):
        ruta = filedialog.askopenfilename(
            title="Elige el logo del cliente",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos", "*.*")])
        if ruta:
            self.ruta_logo = ruta
            self.etiqueta_logo.config(text=os.path.basename(ruta), fg=GRIS)

    def elegir_color(self):
        res = colorchooser.askcolor(title="Elige el color del catálogo",
                                    color=self.color or "#1f7a3d")
        if res and res[1]:
            self.color = res[1]
            self.muestra_color.config(bg=self.color)
            self.etiqueta_color.config(text=self.color, fg=GRIS)

    def generar(self):
        cliente = self.entrada_cliente.get().strip()
        if not self.ruta_logo:
            messagebox.showwarning("Falta el logo", "Primero elige el logo del cliente.")
            return
        if not cliente:
            messagebox.showwarning("Falta el nombre", "Escribe el nombre de la empresa cliente.")
            return
        self.boton_generar.config(state="disabled", text="Generando…")
        self.estado.config(text="Creando el catálogo, dame unos segundos…")
        threading.Thread(target=self._trabajo, args=(cliente,), daemon=True).start()

    def _trabajo(self, cliente):
        try:
            carpeta, _ = motor.generar(self.ruta_logo, cliente, color=self.color)
            self.raiz.after(0, self._listo, carpeta)
        except Exception as e:
            self.raiz.after(0, self._error, str(e))

    def _listo(self, carpeta):
        self.boton_generar.config(state="normal", text="Generar catálogo")
        self.estado.config(text="¡Listo! Se abrió la carpeta con el catálogo. ✓")
        os.startfile(carpeta)

    def _error(self, mensaje):
        self.boton_generar.config(state="normal", text="Generar catálogo")
        self.estado.config(text="")
        messagebox.showerror("No se pudo generar",
                             f"Revisa que el logo sea una imagen válida.\n\nDetalle: {mensaje}")

    # ------------------------------------------------------------------ #
    # Métodos de la pestaña Renombrar Cotizaciones
    # ------------------------------------------------------------------ #

    def _construir_renombrar(self, panel):
        import renombrador
        self._renom = renombrador
        self._items = []
        barra = tk.Frame(panel, bg=FONDO)
        barra.pack(fill="x", padx=16, pady=12)
        tk.Button(barra, text="Elegir carpeta…", command=self._renom_elegir).pack(side="left")
        self._renom_ruta = tk.Label(barra, text="(ninguna)", bg=FONDO, fg="#777")
        self._renom_ruta.pack(side="left", padx=10)

        cols = ("archivo", "categoria", "cliente", "fecha", "numero")
        self._tabla = ttk.Treeview(panel, columns=cols, show="headings", height=12)
        for c, txt, w in [("archivo", "Archivo", 240), ("categoria", "Categoría", 150),
                           ("cliente", "Cliente", 230), ("fecha", "Fecha", 60), ("numero", "N° (ref)", 120)]:
            self._tabla.heading(c, text=txt)
            self._tabla.column(c, width=w)
        self._tabla.tag_configure("revisar", background="#FFF3CD")  # ambar
        self._tabla.tag_configure("alta", background="#E6F4EA")      # verde
        self._tabla.pack(fill="both", expand=True, padx=16)
        self._tabla.bind("<Double-1>", self._renom_editar_celda)

        pie = tk.Frame(panel, bg=FONDO)
        pie.pack(fill="x", padx=16, pady=12)
        self._renom_estado = tk.Label(pie, text="", bg=FONDO, fg="#555")
        self._renom_estado.pack(side="left")
        tk.Button(pie, text="Renombrar todo", command=self._renom_aplicar).pack(side="right")

    def _renom_elegir(self):
        carpeta = filedialog.askdirectory(title="Carpeta con cotizaciones PDF")
        if not carpeta:
            return
        self._renom_carpeta = carpeta
        self._renom_ruta.config(text=carpeta)
        self._items = self._renom.planificar_carpeta(carpeta)
        self._renom_poblar_tabla()
        self._renom_estado.config(text=f"{len(self._items)} cotizaciones leídas.")

    def _renom_poblar_tabla(self):
        from pathlib import Path
        self._tabla.delete(*self._tabla.get_children())
        for it in self._items:
            iid = self._tabla.insert("", "end", tags=(it["confianza"],), values=(
                Path(it["archivo"]).name, it["categoria"], it.get("cliente", ""),
                it.get("fecha") or "", it.get("numero") or ""))
            it["_iid"] = iid

    def _renom_editar_celda(self, event):
        from tkinter import simpledialog
        iid = self._tabla.focus()
        col = self._tabla.identify_column(event.x)
        if not iid:
            return
        idx = {"#1": "archivo", "#2": "categoria", "#3": "cliente", "#4": "fecha", "#5": "numero"}.get(col)
        it = next((x for x in self._items if x.get("_iid") == iid), None)
        if it is None or idx in (None, "archivo", "numero"):
            return
        if idx == "categoria":
            # menu con vocabulario completo
            top = tk.Toplevel(self._tabla)
            top.title("Categoría")
            var = tk.StringVar(value=it["categoria"])
            combo = ttk.Combobox(top, values=self._renom.VOCABULARIO, textvariable=var, state="readonly")
            combo.pack(padx=12, pady=12)

            def ok():
                it["categoria"] = var.get()
                self._tabla.set(iid, "categoria", var.get())
                top.destroy()

            tk.Button(top, text="OK", command=ok).pack(pady=(0, 12))
        else:
            actual = it.get(idx) or ""
            nuevo = simpledialog.askstring("Editar", idx, initialvalue=actual, parent=self._tabla)
            if nuevo is not None:
                it[idx] = nuevo
                self._tabla.set(iid, idx, nuevo)

    def _renom_aplicar(self):
        if not self._items or not getattr(self, "_renom_carpeta", None):
            return  # nada que renombrar si no se eligió carpeta
        for it in self._items:  # recomputar nombre con lo editado
            if it.get("error"):  # PDF ilegible: conservar el nombre original (aplicar lo salta)
                continue
            it["nombre_final"] = self._renom.nombre_destino(
                it["categoria"], it.get("cliente") or "SIN CLIENTE", it.get("fecha"))
        res = self._renom.aplicar(self._items, self._renom_carpeta)
        messagebox.showinfo("Listo",
            f"{res['renombrados']} renombrados · {res['revisar']} marcados para revisar."
            + (f"\nErrores: {len(res['errores'])}" if res['errores'] else ""))
        if getattr(self, "_renom_carpeta", None):  # recargar mostrando los nuevos nombres
            self._items = self._renom.planificar_carpeta(self._renom_carpeta)
            self._renom_poblar_tabla()


def main():
    # modo consola opcional: MockupsDISECOD.exe logo.png "Cliente" [#RRGGBB]
    if len(sys.argv) >= 3:
        color = sys.argv[3] if len(sys.argv) >= 4 else None
        carpeta, _ = motor.generar(sys.argv[1], sys.argv[2], color=color)
        print(carpeta)
        return
    raiz = tk.Tk()
    App(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
