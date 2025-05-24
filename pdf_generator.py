from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

# Obtener la hoja de estilos base una vez
styles = getSampleStyleSheet()

# Definir y añadir estilos personalizados (si no existen) o modificar los existentes
# Para estilos que son nuevos y no parte de getSampleStyleSheet() por defecto, usar styles.add()
styles.add(ParagraphStyle(name='TitleStyle',
                          fontName='Helvetica-Bold',
                          fontSize=24,
                          alignment=TA_CENTER,
                          spaceAfter=14))
styles.add(ParagraphStyle(name='SubtitleStyle',
                          fontName='Helvetica-Bold',
                          fontSize=16,
                          alignment=TA_CENTER,
                          spaceAfter=10,
                          textColor=HexColor('#007bff'))) # Azul Bootstrap

# Para estilos que ya existen en getSampleStyleSheet() (como 'Heading2' y 'BodyText'),
# modificamos sus propiedades directamente en lugar de intentar añadirlos.
# Esto evita el KeyError.
styles['Heading2'].fontName = 'Helvetica-Bold'
styles['Heading2'].fontSize = 14
styles['Heading2'].spaceBefore = 12
styles['Heading2'].spaceAfter = 6
styles['Heading2'].textColor = HexColor('#343a40') # Gris oscuro Bootstrap

styles['BodyText'].fontName = 'Helvetica'
styles['BodyText'].fontSize = 10
styles['BodyText'].spaceAfter = 4
styles['BodyText'].alignment = TA_LEFT

# Este estilo es probablemente nuevo, así que lo añadimos
styles.add(ParagraphStyle(name='StrongBodyText',
                          fontName='Helvetica-Bold',
                          fontSize=10,
                          spaceAfter=4,
                          alignment=TA_LEFT))

# Este estilo es probablemente nuevo, así que lo añadimos
styles.add(ParagraphStyle(name='Disclaimer',
                          fontName='Helvetica-Oblique',
                          fontSize=8,
                          alignment=TA_CENTER,
                          spaceBefore=20,
                          textColor=HexColor('#6c757d'))) # Gris Bootstrap


def generate_diagnostico_pdf(diagnostico_data, cliente_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    
    story = []

    # Título del documento
    story.append(Paragraph("Syon Net", styles['TitleStyle']))
    story.append(Paragraph("Informe de Diagnóstico de Equipo", styles['TitleStyle']))
    story.append(Spacer(1, 0.2 * inch))

    # Sección de Datos del Cliente
    story.append(Paragraph("Datos del Cliente", styles['Heading2']))
    story.append(Paragraph(f"<b>Nombre:</b> {cliente_data.get('nombre', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Cédula de Identidad (CI):</b> {cliente_data.get('ci', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Teléfono:</b> {cliente_data.get('telefono', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Correo Electrónico:</b> {cliente_data.get('email', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Dirección:</b> {cliente_data.get('direccion', 'N/A')}", styles['BodyText']))
    story.append(Spacer(1, 0.2 * inch))

    # Sección de Datos del Equipo y Problema
    story.append(Paragraph("Datos del Equipo y Problema", styles['Heading2']))
    story.append(Paragraph(f"<b>ID Diagnóstico:</b> {diagnostico_data.get('id', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Fecha de Recepción:</b> {diagnostico_data.get('fecha_recepcion', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Tipo de Equipo:</b> {diagnostico_data.get('tipo_equipo', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Marca:</b> {diagnostico_data.get('marca', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Modelo:</b> {diagnostico_data.get('modelo', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Número de Serie (Serial):</b> {diagnostico_data.get('serial', 'N/A')}", styles['BodyText']))
    
    # Campo: Componentes
    story.append(Paragraph(f"<b>Especificaciones del Equipo (Componentes):</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('componentes', 'N/A'), styles['BodyText']))
    
    story.append(Paragraph(f"<b>Accesorios Recibidos:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('accesorios_recibidos', 'N/A'), styles['BodyText']))
    story.append(Paragraph(f"<b>Problema Reportado:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('problema_reportado', 'N/A'), styles['BodyText']))
    story.append(Spacer(1, 0.2 * inch))

    # Sección de Diagnóstico y Resultado Técnico
    story.append(Paragraph("Diagnóstico y Resultado Técnico", styles['Heading2']))
    story.append(Paragraph(f"<b>Diagnóstico Inicial:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('diagnostico_inicial', 'N/A'), styles['BodyText']))
    story.append(Paragraph(f"<b>Solución Aplicada:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('solucion_aplicada', 'N/A'), styles['BodyText']))
    story.append(Paragraph(f"<b>Piezas Reemplazadas:</b> {diagnostico_data.get('piezas_reemplazadas', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Estado Final:</b> {diagnostico_data.get('estado_final', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Fecha de Entrega:</b> {diagnostico_data.get('fecha_entrega', 'N/A')}", styles['BodyText']))
    story.append(Paragraph(f"<b>Costo del Servicio:</b> ${diagnostico_data.get('costo_servicio', 0.0):.2f}", styles['BodyText']))
    story.append(Paragraph(f"<b>Observaciones Adicionales:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('observaciones_adicionales', 'N/A'), styles['BodyText']))
    story.append(Spacer(1, 0.5 * inch))

    # Pie de página o descargo de responsabilidad
    story.append(Paragraph("Este informe es generado automáticamente por Syon Net.", styles['Disclaimer']))

    doc.build(story)
