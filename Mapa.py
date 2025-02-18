import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import socket
import fiona
import sys

# Lista de IPs permitidas
IP_PERMITIDAS = ["11.35.85.97", "11.35.87.30"]

def verificar_ip():
    try:
        ip_actual = socket.gethostbyname(socket.gethostname())
        if ip_actual not in IP_PERMITIDAS:
            print(f"⚠️ Acceso denegado: Tu IP ({ip_actual}) no está autorizada.")
            sys.exit()  # Cierra el programa
        else:
            print(f"✅ Acceso permitido: IP ({ip_actual}) autorizada.")
    except Exception as e:
        print(f"❌ Error al obtener la IP: {e}")
        sys.exit()  # Cierra el programa si no se puede verificar la IP

# Ejecutar la verificación antes de iniciar el programa
verificar_ip()

# Ruta del shapefile (ajústala si es necesario)
shapefile_path = "SHPCensoDepartamento INEI 2007 geogpsperu SuyoPomalia.shp"

# Función para seleccionar un color
def seleccionar_color():
    colormaps = [
        "OrRd", "Blues", "Greens", "Reds", "Purples", "viridis", "plasma", "inferno",
        "magma", "cividis", "coolwarm", "Spectral", "hsv", "twilight"
    ]
    
    # Crear una ventana para seleccionar la escala de colores
    color_window = tk.Toplevel()
    color_window.title("Seleccionar Escala de Colores")

    def set_color(selected_color):
        color_label.config(text=selected_color)
        color_window.destroy()

    for cmap in colormaps:
        btn = tk.Button(color_window, text=cmap, command=lambda c=cmap: set_color(c))
        btn.pack(pady=2)


# Función para generar y descargar la plantilla de Excel
def descargar_plantilla():
    try:
        # Extraer los nombres de las regiones desde la columna "NAME_1"
        with fiona.open(shapefile_path, "r") as shp:
            regiones = list(set(feature["properties"]["NAME_1"] for feature in shp))

        # Eliminar "Lago Titicaca"
        regiones = [r for r in regiones if r != "Lago TitiCaca"]

        # Reemplazar "Provincia Constitucional del Callao" por "Callao"
        regiones = ["Callao" if r == "Provincia Constitucional del Callao" else r for r in regiones]

        # Ordenar alfabéticamente
        regiones.sort()

        # Crear un DataFrame con la estructura deseada
        df_plantilla = pd.DataFrame({"REGION": regiones, "IGED_COBERTURA": [None] * len(regiones)})

        # Seleccionar ubicación para guardar el archivo
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx")],
                                                 title="Guardar Plantilla")

        if file_path:
            df_plantilla.to_excel(file_path, index=False)
            messagebox.showinfo("Éxito", "Plantilla descargada correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar la plantilla: {e}")

# Función para generar el mapa con etiquetas de datos
def generar_mapa():
    try:
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        
        df = pd.read_excel(file_path)
        
        # Sumar Lima Metropolitana y Lima Provincias en "LIMA"
        df.loc[df["REGION"].isin(["LIMA METROPOLITANA", "LIMA PROVINCIAS"]), "REGION"] = "LIMA"
        df = df.groupby("REGION", as_index=False).sum()

        # Cargar el mapa
        peru_map = gpd.read_file(shapefile_path)
        peru_map = peru_map.merge(df, left_on="NAME_1", right_on="REGION", how="left")

        # Obtener color de escala
        color_scale = color_label.cget("text") if color_label.cget("text") else "OrRd"

        # Graficar el mapa
        fig, ax = plt.subplots(figsize=(10, 12))
        peru_map.plot(column="IGED_COBERTURA", cmap=color_scale, linewidth=0.8, edgecolor="black",
                      legend=True, ax=ax, missing_kwds={"color": "lightgrey", "label": "No data"})
        
        # Agregar etiquetas de datos en cada región
        for idx, row in peru_map.iterrows():
            if not pd.isna(row["IGED_COBERTURA"]):  # Solo si hay datos
                centroid = row["geometry"].centroid
                ax.text(centroid.x, centroid.y, str(int(row["IGED_COBERTURA"])), 
                        fontsize=8, ha='center', color="black", weight="bold")

        ax.set_title("Cobertura de IGED por Región en Perú", fontsize=14)
        ax.axis("off")
        plt.show()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar el mapa: {e}")

# Crear la ventana de la interfaz
root = tk.Tk()
root.title("Mapa de IGED - Perú")

# Botón para seleccionar el color de escala
btn_color = tk.Button(root, text="Seleccionar Color de Escala", command=seleccionar_color)
btn_color.pack(pady=5)

# Etiqueta para mostrar el color seleccionado
color_label = tk.Label(root, text="OrRd", bg="white", width=15)
color_label.pack(pady=5)

# Botón para descargar la plantilla de Excel
btn_descargar = tk.Button(root, text="Descargar Plantilla Excel", command=descargar_plantilla)
btn_descargar.pack(pady=5)

# Botón para cargar el archivo de datos y generar el mapa
btn_generar = tk.Button(root, text="Cargar Datos y Generar Mapa", command=generar_mapa)
btn_generar.pack(pady=5)

# Iniciar la interfaz
root.mainloop()
