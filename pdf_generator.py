# pdf_generator.py (VERSIÓN DE DEPURACIÓN CRÍTICA)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime
import os
from typing import Literal

# Ruta a la fuente NotoSans-Regular.ttf
FONT_PATH_REGULAR = os.path.join(os.path.dirname(__file__), 'NotoSans-Regular.ttf')

if not os.path.exists(FONT_PATH_REGULAR):
    print(f"ERROR: No se encontró la fuente 'NotoSans-Regular.ttf' en la ruta: {FONT_PATH_REGULAR}")
    print("Por favor, descarga 'NotoSans-Regular.ttf' y colócalo en la ubicación correcta.")

def _limpiar_texto(texto):
    if not texto:
        return ''
    return (str(texto)
            .replace('\n', ' ')
            .replace('\r', ' ')
            .replace('á', 'a').replace('é', 'e').replace('í', 'i')
            .replace('ó', 'o').replace('ú', 'u')
            .replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
            .replace('Ó', 'O').replace('Ú', 'U')
            .replace('ñ', 'n').replace('Ñ', 'N')
            .replace('€', 'Euros')
            .replace('“', '"').replace('”', '"')
            .replace('‘', "'").replace('’', "'")
            .replace('—', '-')
            .replace('…', '...') # Agregado por si hay elipses
            .replace('°', ' grados') # Agregado por si hay símbolos de grado
            # Puedes seguir agregando más reemplazos si identificas otros caracteres problemáticos
           )

def generate_diagnostico_pdf(diagnostico_data, cliente_data, output_path):
    # Registrar la fuente NotoSans-Regular.ttf
    font_path = os.path.join(os.path.dirname(__file__), 'NotoSans-Regular.ttf')
    pdfmetrics.registerFont(TTFont('NotoSans', font_path))

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont('NotoSans', 15)
    width, height = A4
    y = height - 40
    c.drawCentredString(width/2, y, 'Informe de Diagnóstico de Equipo de Cómputo')
    y -= 30
    c.setFont('NotoSans', 11)
    c.drawString(40, y, '1. Datos del Cliente')
    y -= 20
    c.setFont('NotoSans', 9)
    c.drawString(50, y, f"Nombre: {cliente_data.get('nombre', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Teléfono: {cliente_data.get('telefono', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Email: {cliente_data.get('email', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Dirección: {cliente_data.get('direccion', 'N/A')}")
    y -= 25
    c.setFont('NotoSans', 11)
    c.drawString(40, y, '2. Datos del Equipo y Problema')
    y -= 20
    c.setFont('NotoSans', 9)
    c.drawString(50, y, f"Fecha de Recepción: {diagnostico_data.get('fecha_recepcion', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Tipo de Equipo: {diagnostico_data.get('tipo_equipo', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Marca: {diagnostico_data.get('marca', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Modelo: {diagnostico_data.get('modelo', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Número de Serie (Serial): {diagnostico_data.get('serial', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Accesorios Recibidos: {diagnostico_data.get('accesorios_recibidos', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Problema Reportado: {diagnostico_data.get('problema_reportado', 'N/A')}")
    y -= 25
    c.setFont('NotoSans', 11)
    c.drawString(40, y, '3. Diagnóstico y Resultado Técnico')
    y -= 20
    c.setFont('NotoSans', 9)
    c.drawString(50, y, f"Diagnóstico Inicial: {diagnostico_data.get('diagnostico_inicial', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Solución Aplicada: {diagnostico_data.get('solucion_aplicada', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Piezas Reemplazadas: {diagnostico_data.get('piezas_reemplazadas', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Estado Final: {diagnostico_data.get('estado_final', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Fecha de Entrega: {diagnostico_data.get('fecha_entrega', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Costo del Servicio: {diagnostico_data.get('costo_servicio', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Observaciones Adicionales: {diagnostico_data.get('observaciones_adicionales', 'N/A')}")
    y -= 30
    c.setFont('NotoSans', 8)
    c.drawRightString(width-40, y, f"Fecha de generación del informe: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30
    c.drawCentredString(width/2, y, '_________________________')
    y -= 15
    c.drawCentredString(width/2, y, 'Firma del Técnico')
    c.save()

if __name__ == '__main__':
    # Puedes ejecutar este script directamente para probar el PDF con texto estático
    output_pdf_file_example = "informe_diagnostico_estatico.pdf"
    try:
        generate_diagnostico_pdf({}, {}, output_pdf_file_example) # Pasa diccionarios vacíos
        print(f"PDF estático generado: {output_pdf_file_example}")
    except Exception as e:
        print("Ocurrió un error al generar el PDF estático:")
        import traceback
        traceback.print_exc()