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

import estado
import lienzo
from PIL import Image
# ImageTk se importa DIFERIDO (en _p_mostrar): el exe v22 no lo trae empaquetado, y un
# import al cargar tumbaría toda la app tras el auto-update. Así el exe viejo sigue
# funcionando (Mockups/Renombrar/editar/exportar) y solo el preview pide actualizar.

LILA = "#9987F7"
LILA_OSCURO = "#7A66E8"
GRIS = "#383838"
FONDO = "#FFFFFF"


def motor_catalogo():
    """[(clave, nombre)] de los modelos, para el selector — sin filtrar tipos a la GUI."""
    from plantillas import catalogo
    return [(m.clave, m.nombre) for m in catalogo()]


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
        raiz.geometry("1100x840")
        raiz.minsize(900, 680)         # redimensionable: el preview escala con la ventana
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

        frame_personalizar = tk.Frame(nb, bg=FONDO)
        nb.add(frame_personalizar, text="Personalizar")

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

        # --- Pestaña 3: Personalizar (v2) ---
        self._construir_personalizar(frame_personalizar)

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

    # ------------------------------------------------------------------ #
    # Pestaña Personalizar (v2): editar UN modelo por chat + controles
    # ------------------------------------------------------------------ #

    def _construir_personalizar(self, panel):
        self.p_logo = None
        self.p_logo_ruta = None
        self._p_preview_img = None         # referencia viva del ImageTk
        self._p_gen = 0                    # contador de re-render (descarta renders viejos)
        self._modelos = motor_catalogo()   # [(clave, nombre)] — los 18
        self.p_ajustes = estado.ajustes_inicial(self._modelos[0][0])

        # --- barra superior: logo + cliente + modelo ---
        top = tk.Frame(panel, bg=FONDO)
        top.pack(fill="x", padx=16, pady=10)
        tk.Button(top, text="Elegir logo…", command=self._p_elegir_logo).pack(side="left")
        self.p_logo_lbl = tk.Label(top, text="(ningún logo)", bg=FONDO, fg="#999")
        self.p_logo_lbl.pack(side="left", padx=8)
        tk.Label(top, text="Empresa:", bg=FONDO, fg=GRIS).pack(side="left", padx=(12, 4))
        self.p_cliente = tk.Entry(top, width=18)
        self.p_cliente.pack(side="left")
        self.p_cliente.bind("<KeyRelease>", lambda _e: self._p_schedule_render())
        tk.Label(top, text="Modelo:", bg=FONDO, fg=GRIS).pack(side="left", padx=(12, 4))
        self.p_modelo_var = tk.StringVar(value=self._modelos[0][1])
        self.p_modelo_combo = ttk.Combobox(
            top, width=22, state="readonly", textvariable=self.p_modelo_var,
            values=[n for _c, n in self._modelos])
        self.p_modelo_combo.pack(side="left")
        self.p_modelo_combo.bind("<<ComboboxSelected>>", self._p_cambiar_modelo)

        # --- cuerpo: preview (izq) + panel chat/controles (der) ---
        cuerpo = tk.Frame(panel, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        izq = tk.Frame(cuerpo, bg="#F4F4F6", width=560)
        izq.pack(side="left", fill="both", expand=True)
        izq.pack_propagate(False)
        self._p_izq = izq
        izq.bind("<Configure>", lambda _e: self._p_fit_preview_debounced())
        self.p_canvas = tk.Canvas(izq, bg="#F4F4F6", highlightthickness=0, cursor="hand2")
        self.p_canvas.pack(expand=True, fill="both")
        self.p_canvas.bind("<Button-1>", self._p_canvas_down)
        self.p_canvas.bind("<B1-Motion>", self._p_canvas_drag)
        self.p_canvas.bind("<ButtonRelease-1>", self._p_canvas_up)
        self._p_canvas_geo = None      # (offx, offy, w, h) de la imagen mostrada
        self._p_capa_sel = None        # capa seleccionada / arrastrándose
        self._p_modo = None            # "mover" | "estirar"
        self._p_drag0 = None

        der = tk.Frame(cuerpo, bg=FONDO, width=370)
        der.pack(side="right", fill="y")
        der.pack_propagate(False)
        self._p_panel_der = der
        self._p_construir_campos(der)
        self._p_controles = tk.Frame(der, bg=FONDO)
        self._p_controles.pack(fill="x", pady=(8, 0))
        self._p_rebuild_controles()

        # --- pie: actualizar + guardar/reabrir + exportar ---
        pie = tk.Frame(panel, bg=FONDO)
        pie.pack(fill="x", padx=16, pady=(0, 12))
        tk.Button(pie, text="Actualizar preview", command=self._p_rerender,
                  bg=LILA, fg="white", relief="flat", padx=14, pady=6).pack(side="left")
        tk.Button(pie, text="Guardar", command=self._p_guardar,
                  bg="#EEEAFE", fg=GRIS, relief="flat", padx=10, pady=6).pack(side="left", padx=(6, 0))
        tk.Button(pie, text="Reabrir", command=self._p_reabrir,
                  bg="#EEEAFE", fg=GRIS, relief="flat", padx=10, pady=6).pack(side="left", padx=(6, 0))
        self.p_estado = tk.Label(pie, text="", bg=FONDO, fg="#555")
        self.p_estado.pack(side="left", padx=10)
        tk.Button(pie, text="Exportar para WhatsApp", command=self._p_exportar,
                  bg="#25D366", fg="white", relief="flat", padx=14, pady=6).pack(side="right")

    def _p_elegir_logo(self):
        ruta = filedialog.askopenfilename(
            title="Logo del cliente",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos", "*.*")])
        if ruta:
            self.p_logo_ruta = ruta
            self.p_logo = motor.cargar_logo(ruta)
            self.p_logo_lbl.config(text=os.path.basename(ruta), fg=GRIS)
            self._p_schedule_render()          # muestra el preview sin pedir "Actualizar"

    def _modelo_actual(self):
        from plantillas import catalogo
        clave = self.p_ajustes["modelo"]
        return next(m for m in catalogo() if m.clave == clave)

    def _p_cambiar_modelo(self, _evt=None):
        nombre = self.p_modelo_var.get()
        clave = next(c for c, n in self._modelos if n == nombre)
        # conserva color, textos y los CAMPOS que el vendedor ya armó; resetea logo_pos
        nuevo = estado.ajustes_inicial(clave)
        nuevo["color"] = self.p_ajustes["color"]
        nuevo["textos"] = dict(self.p_ajustes["textos"])
        nuevo["filas"] = [dict(f) for f in self.p_ajustes.get("filas", [])]
        self.p_ajustes = nuevo
        self._p_rebuild_controles()
        self._p_schedule_render()

    def _p_construir_campos(self, panel):
        """Editor de datos: Nombre/Cargo (texto héroe) + lista de campos etiqueta:valor."""
        from plantillas import DATOS
        self._p_texto_entries = {}
        for campo, etiq in (("nombre", "Nombre"), ("cargo", "Cargo")):
            f = tk.Frame(panel, bg=FONDO)
            f.pack(fill="x", pady=1)
            tk.Label(f, text=etiq, width=7, anchor="w", bg=FONDO, fg="#666").pack(side="left")
            e = tk.Entry(f)
            e.insert(0, self.p_ajustes["textos"].get(campo) or DATOS[campo])
            e.pack(side="left", fill="x", expand=True)
            e.bind("<KeyRelease>", lambda _e, c=campo: self._p_on_texto(c))
            self._p_texto_entries[campo] = e

        tk.Label(panel, text="Campos (etiqueta : valor):", bg=FONDO, fg=GRIS,
                 anchor="w").pack(fill="x", pady=(10, 2))
        tk.Label(panel, text="Empresa, Nombre y Cargo ya están arriba; aquí agrega los demás.",
                 bg=FONDO, fg="#999", anchor="w", font=("Segoe UI", 8)).pack(fill="x")
        self._p_filas_cont = tk.Frame(panel, bg=FONDO)
        self._p_filas_cont.pack(fill="x", pady=(2, 0))
        tk.Button(panel, text="+ Agregar campo", command=self._p_agregar_fila,
                  bg="#EEEAFE", fg=GRIS, relief="flat", padx=10, pady=3).pack(anchor="w", pady=(5, 0))
        self._p_render_filas_editor()

    def _p_render_filas_editor(self):
        for w in self._p_filas_cont.winfo_children():
            w.destroy()
        self._p_fila_rows = []
        for i, fila in enumerate(self.p_ajustes.get("filas", [])):
            f = tk.Frame(self._p_filas_cont, bg=FONDO)
            f.pack(fill="x", pady=1)
            etq = tk.Entry(f, width=12)
            etq.insert(0, fila.get("etiqueta", ""))
            etq.pack(side="left")
            val = tk.Entry(f, width=12)
            val.insert(0, fila.get("valor", ""))
            val.pack(side="left", padx=3, fill="x", expand=True)
            etq.bind("<KeyRelease>", lambda _e: self._p_on_filas())
            val.bind("<KeyRelease>", lambda _e: self._p_on_filas())
            tk.Button(f, text="✕", command=lambda idx=i: self._p_quitar_fila(idx),
                      relief="flat", padx=4, fg="#a33", bg=FONDO).pack(side="left")
            self._p_fila_rows.append((etq, val))

    def _p_filas_actuales(self):
        return [{"etiqueta": e.get(), "valor": v.get()} for e, v in self._p_fila_rows]

    def _p_on_filas(self):
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"filas": self._p_filas_actuales()})
        self._p_schedule_render()

    def _p_agregar_fila(self):
        filas = self._p_filas_actuales() + [{"etiqueta": "", "valor": ""}]
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"filas": filas})
        self._p_render_filas_editor()

    def _p_quitar_fila(self, idx):
        filas = self._p_filas_actuales()
        if 0 <= idx < len(filas):
            filas.pop(idx)
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"filas": filas})
        self._p_render_filas_editor()
        self._p_schedule_render()

    def _p_rebuild_controles(self):
        """Color + posición de logo (lo demás vive en el editor de campos de arriba)."""
        for w in self._p_controles.winfo_children():
            w.destroy()
        m = self._modelo_actual()
        cont = self._p_controles
        # color
        filc = tk.Frame(cont, bg=FONDO)
        filc.pack(fill="x", pady=(10, 0))
        tk.Label(filc, text="Color:", bg=FONDO, fg=GRIS).pack(side="left")
        tk.Button(filc, text="Elegir…", command=self._p_elegir_color).pack(side="left", padx=4)
        tk.Button(filc, text="Auto (del logo)", command=self._p_color_auto).pack(side="left")
        # posición del logo (radios) si el modelo soporta más de "default"
        if len(m.logo_posiciones) > 1:
            fl = tk.Frame(cont, bg=FONDO)
            fl.pack(fill="x", pady=(6, 0))
            tk.Label(fl, text="Logo:", bg=FONDO, fg=GRIS).pack(side="left")
            self._p_logo_var = tk.StringVar(value=self.p_ajustes["logo_pos"])
            txt = {"default": "Centro", "izq": "Izq.", "der": "Der.", "centro": "Centro"}
            for pos in m.logo_posiciones:
                tk.Radiobutton(fl, text=txt.get(pos, pos), value=pos, variable=self._p_logo_var,
                               bg=FONDO, command=self._p_set_logo_pos).pack(side="left")

    def _p_schedule_render(self, delay=350):
        """Re-render DIFERIDO (debounce): junta tipeos/clicks rápidos en un solo render
        para no abrir Edge en cada tecla."""
        if not self.p_logo:
            self.p_estado.config(text="Elige un logo para ver el preview.")
            return
        if getattr(self, "_p_render_job", None):
            try:
                self.raiz.after_cancel(self._p_render_job)
            except Exception:
                pass
        self.p_estado.config(text="Actualizando…")
        self._p_render_job = self.raiz.after(delay, self._p_rerender)

    def _p_set_logo_pos(self):
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"logo_pos": self._p_logo_var.get()})
        self._p_schedule_render()

    def _p_elegir_color(self):
        res = colorchooser.askcolor(title="Color del modelo", color=self.p_ajustes["color"] or "#1f7a3d")
        if res and res[1]:
            self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"color": res[1]})
            self._p_schedule_render()

    def _p_color_auto(self):
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"color": None})
        self._p_schedule_render()

    def _p_on_texto(self, campo):
        valor = self._p_texto_entries[campo].get().strip()
        self.p_ajustes = estado.aplicar_cambios(self.p_ajustes, {"textos": {campo: valor}})
        self._p_schedule_render()

    def _p_rerender(self):
        if not self.p_logo:
            self.p_estado.config(text="Primero elige un logo.")
            return
        cliente = self.p_cliente.get().strip() or "Cliente"
        self._p_gen += 1
        gen = self._p_gen
        self.p_estado.config(text="Actualizando…")
        ajustes = estado.aplicar_cambios(self.p_ajustes, {})   # copia inmutable para el hilo

        def trabajo():
            try:
                img = motor.render_modelo(self.p_logo, cliente, ajustes)
                self.raiz.after(0, self._p_mostrar, gen, img)
            except Exception as e:
                self.raiz.after(0, self._p_error, str(e))

        threading.Thread(target=trabajo, daemon=True).start()

    def _p_mostrar(self, gen, img):
        if gen != self._p_gen:
            return                       # llegó un render viejo: descártalo
        self._p_last_full = img          # imagen completa; el fit la escala a la ventana
        self._p_fit_preview()
        self.p_estado.config(text="Listo ✓")

    def _p_fit_preview(self):
        """Pinta el preview compuesto en el canvas + las cajas de capa (arrastrables);
        crece con la ventana."""
        img = getattr(self, "_p_last_full", None)
        if img is None:
            return
        try:
            from PIL import ImageTk       # diferido: exe viejo (v22) no lo trae
        except Exception:
            self.p_estado.config(
                text="Cierra y vuelve a abrir la app para activar el preview. (Exportar ya funciona.)")
            return
        cw = max(160, self.p_canvas.winfo_width())
        ch = max(160, self.p_canvas.winfo_height())
        disp = img.copy()
        disp.thumbnail((cw - 16, ch - 16), Image.LANCZOS)
        self._p_preview_img = ImageTk.PhotoImage(disp)
        offx = (cw - disp.width) // 2
        offy = (ch - disp.height) // 2
        self._p_canvas_geo = (offx, offy, disp.width, disp.height)
        self.p_canvas.delete("all")
        self.p_canvas.create_image(offx, offy, anchor="nw", image=self._p_preview_img, tags=("fondo",))
        self._p_dibujar_cajas()

    def _p_dibujar_cajas(self):
        """(Re)dibuja SOLO los recuadros de capa + asas, sin re-escalar la imagen (suave
        al arrastrar). La imagen recién se recompone al soltar."""
        if not self._p_canvas_geo:
            return
        self.p_canvas.delete("capa")
        offx, offy, w, h = self._p_canvas_geo
        for cid, c in self.p_ajustes.get("capas", {}).items():
            x0 = offx + c["x"] * w
            y0 = offy + c["y"] * h
            x1 = offx + (c["x"] + c["w"]) * w
            y1 = offy + (c["y"] + c["h"]) * h
            sel = (cid == self._p_capa_sel)
            self.p_canvas.create_rectangle(
                x0, y0, x1, y1, outline=("#378ADD" if sel else "#B9B9C9"),
                dash=(4, 3), width=(2 if sel else 1), tags=("capa",))
            self.p_canvas.create_rectangle(
                x1 - 5, y1 - 5, x1 + 5, y1 + 5, fill="#ffffff", outline="#378ADD", tags=("capa",))

    def _p_xy_a_norm(self, ex, ey):
        offx, offy, w, h = self._p_canvas_geo
        return ((ex - offx) / max(1, w), (ey - offy) / max(1, h))

    def _p_canvas_down(self, e):
        if not self._p_canvas_geo:
            return
        nx, ny = self._p_xy_a_norm(e.x, e.y)
        self._p_capa_sel = None
        self._p_modo = None
        for cid, c in self.p_ajustes.get("capas", {}).items():
            cerca_asa = abs(nx - (c["x"] + c["w"])) < 0.03 and abs(ny - (c["y"] + c["h"])) < 0.04
            dentro = c["x"] <= nx <= c["x"] + c["w"] and c["y"] <= ny <= c["y"] + c["h"]
            if cerca_asa:
                self._p_capa_sel = cid
                self._p_modo = "estirar"
                break
            if dentro:
                self._p_capa_sel = cid
                self._p_modo = "mover"
        self._p_drag0 = (nx, ny)
        self._p_dibujar_cajas()

    def _p_canvas_drag(self, e):
        if not (self._p_capa_sel and self._p_canvas_geo and self._p_drag0):
            return
        nx, ny = self._p_xy_a_norm(e.x, e.y)
        dx = nx - self._p_drag0[0]
        dy = ny - self._p_drag0[1]
        c = self.p_ajustes["capas"][self._p_capa_sel]
        if self._p_modo == "mover":
            self.p_ajustes = estado.mover_capa(self.p_ajustes, self._p_capa_sel,
                                               x=c["x"] + dx, y=c["y"] + dy)
        else:
            self.p_ajustes = estado.mover_capa(self.p_ajustes, self._p_capa_sel,
                                               w=max(0.05, c["w"] + dx), h=max(0.05, c["h"] + dy))
        self._p_drag0 = (nx, ny)
        self._p_dibujar_cajas()

    def _p_canvas_up(self, e):
        if not self._p_capa_sel:
            return
        c = self.p_ajustes["capas"][self._p_capa_sel]
        self.p_ajustes = estado.mover_capa(self.p_ajustes, self._p_capa_sel,
                                           x=lienzo.snap(c["x"]), y=lienzo.snap(c["y"]))
        self._p_modo = None
        if self.p_logo:
            self._p_schedule_render(120)   # recompone la imagen con la capa en su nuevo sitio
        else:
            self._p_dibujar_cajas()

    def _p_fit_preview_debounced(self):
        if getattr(self, "_p_fit_job", None):
            try:
                self.raiz.after_cancel(self._p_fit_job)
            except Exception:
                pass
        self._p_fit_job = self.raiz.after(120, self._p_fit_preview)

    def _p_error(self, msg):
        self.p_estado.config(text="")
        messagebox.showerror("No se pudo generar el preview", msg)

    def _p_exportar(self):
        if not self.p_logo:
            messagebox.showwarning("Falta el logo", "Primero elige el logo del cliente.")
            return
        cliente = self.p_cliente.get().strip()
        if not cliente or cliente.lower() == "cliente":
            messagebox.showwarning(
                "Falta la empresa",
                "Escribe el nombre de la empresa del cliente (arriba, en 'Empresa') antes de "
                "exportar, para que el archivo no salga como 'Cliente'.")
            return
        ajustes = estado.aplicar_cambios(self.p_ajustes, {})
        self.p_estado.config(text="Exportando…")

        def trabajo():
            try:
                carpeta, _ = motor.exportar_personalizado(self.p_logo, cliente, ajustes,
                                                          pdf=True, png=True)
                self.raiz.after(0, self._p_export_listo, carpeta)
            except Exception as e:
                self.raiz.after(0, self._p_error, str(e))

        threading.Thread(target=trabajo, daemon=True).start()

    def _p_export_listo(self, carpeta):
        self.p_estado.config(text="Exportado ✓ (PNG + PDF)")
        os.startfile(carpeta)

    def _p_guardar(self):
        cliente = self.p_cliente.get().strip()
        ruta = filedialog.asksaveasfilename(
            title="Guardar cotización", defaultextension=".json",
            initialfile="cotizacion-%s.json" % (motor.slug(cliente) if cliente else "cliente"),
            filetypes=[("Cotización Mockups", "*.json")])
        if not ruta:
            return
        import json
        data = estado.serializar(self.p_ajustes, cliente, self.p_logo_ruta,
                                 getattr(self, "p_foto_ruta", None))
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.p_estado.config(text="Guardado ✓")
        except Exception as e:
            self._p_error("No se pudo guardar: %s" % e)

    def _p_reabrir(self):
        ruta = filedialog.askopenfilename(
            title="Reabrir cotización",
            filetypes=[("Cotización Mockups", "*.json"), ("Todos", "*.*")])
        if not ruta:
            return
        import json
        try:
            with open(ruta, encoding="utf-8") as f:
                data = estado.deserializar(json.load(f))
        except Exception as e:
            self._p_error("No se pudo abrir la cotización: %s" % e)
            return
        self.p_ajustes = data["ajustes"]
        self.p_cliente.delete(0, "end")
        self.p_cliente.insert(0, data["empresa"])
        if data["logo_ruta"] and os.path.exists(data["logo_ruta"]):
            self.p_logo_ruta = data["logo_ruta"]
            self.p_logo = motor.cargar_logo(data["logo_ruta"])
            self.p_logo_lbl.config(text=os.path.basename(data["logo_ruta"]), fg=GRIS)
        self.p_foto_ruta = data.get("foto_ruta") or None
        try:
            self.p_modelo_var.set(self._modelo_actual().nombre)
        except StopIteration:
            pass
        from plantillas import DATOS
        for campo, e in self._p_texto_entries.items():
            e.delete(0, "end")
            e.insert(0, self.p_ajustes["textos"].get(campo) or DATOS[campo])
        self._p_rebuild_controles()
        self._p_render_filas_editor()
        self._p_schedule_render()


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
