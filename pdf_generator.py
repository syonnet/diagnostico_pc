from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, grey, white

# Obtener la hoja de e
styles = getSampleStyleSheet()

# Definir y añadir estilos personalizados (si no existen) o modificar los existentes
# Para estilos que son nuevos y no parte de getSampleStyleSheet() por defecto, usar styles.add()
styles.add(ParagraphStyle(name='TitleStyle',
                          fontName='Helvetica-Bold',
                          fontSize=18,
                          alignment=TA_CENTER,
                          spaceAfter=8))
styles.add(ParagraphStyle(name='SubtitleStyle',
                          fontName='Helvetica-Bold',
                          fontSize=12,
                          alignment=TA_CENTER,
                          spaceAfter=6,
                          textColor=HexColor('#007bff'))) # Azul Bootstrap

# Para estilos que ya existen en getSampleStyleSheet() (como 'Heading2' y 'BodyText'),
# modificamos sus propiedades directamente en lugar de intentar añadirlos.
# Esto evita el KeyError.
styles['Heading2'].fontName = 'Helvetica-Bold'
styles['Heading2'].fontSize = 10
styles['Heading2'].spaceBefore = 6
styles['Heading2'].spaceAfter = 4
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
                          fontSize=7,
                          alignment=TA_CENTER,
                          spaceBefore=10,
                          textColor=HexColor('#6c757d'))) # Gris Bootstrap


def generate_diagnostico_pdf(diagnostico_data, cliente_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.5*inch, rightMargin=0.5*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []

    # Título del documento
    story.append(Paragraph("Syon Net-Soluciones Informáticas", styles['TitleStyle']))
    story.append(Paragraph("Informe de Diagnóstico", styles['TitleStyle']))
    story.append(Spacer(1, 0.08 * inch))

    # Sección de Datos del Cliente
    story.append(Paragraph("Datos del Cliente", styles['Heading2']))
    cliente_data_list = [
        ["Nombre:", cliente_data.get('nombre', 'N/A')],
        ["Cédula de Identidad (CI):", cliente_data.get('ci', 'N/A')],
        ["Teléfono:", cliente_data.get('telefono', 'N/A')],
        ["Dirección:", cliente_data.get('direccion', 'N/A')]
    ]
    cliente_table = Table(cliente_data_list, colWidths=[2*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#f2f2f2')),
        ('TEXTCOLOR', (0,0), (-1,0), black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (1,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,1), (-1,-1), white),
        ('GRID', (0,0), (-1,-1), 1, grey)
    ]))
    story.append(cliente_table)
    story.append(Spacer(1, 0.08 * inch))

    # Sección de Datos del Equipo y Problema Reportado
    story.append(Paragraph("Datos del Equipo y Problema Reportado", styles['Heading2']))
    equipo_problema_list = [
        ["Fecha de Recepción:", diagnostico_data.get('fecha_recepcion', 'N/A')],
        ["Tipo de Equipo:", diagnostico_data.get('tipo_equipo', 'N/A')],
        ["Marca:", diagnostico_data.get('marca', 'N/A')],
        ["Modelo:", diagnostico_data.get('modelo', 'N/A')],
        ["Número de Serie (Serial):", diagnostico_data.get('serial', 'N/A')],
        ["Componentes:", diagnostico_data.get('componentes', 'N/A')],
    ]
    equipo_problema_table = Table(equipo_problema_list, colWidths=[2*inch, 4*inch])
    equipo_problema_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#f2f2f2')),
        ('TEXTCOLOR', (0,0), (-1,0), black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (1,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,1), (-1,-1), white),
        ('GRID', (0,0), (-1,-1), 1, grey)
    ]))
    story.append(equipo_problema_table)
    story.append(Paragraph(f"<b>Problema Reportado:</b> {diagnostico_data.get('problema_reportado', 'N/A')}", styles['BodyText']))
    story.append(Spacer(1, 0.05 * inch))

    # Sección de Diagnóstico y Resultado Técnico
    story.append(Paragraph("Diagnóstico y Resultado Técnico", styles['Heading2']))
    story.append(Paragraph(f"<b>Diagnóstico Inicial:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('diagnostico_inicial', 'N/A'), styles['BodyText']))
    story.append(Spacer(1, 0.05 * inch))

    story.append(Paragraph(f"<b>Solución Aplicada:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('solucion_aplicada', 'N/A'), styles['BodyText']))
    
    # Piezas Reemplazadas, Estado Final, Fecha Entrega, Costo (usar tabla)
    resultado_tecnico_list = [
        ["Piezas Reemplazadas:", diagnostico_data.get('piezas_reemplazadas', 'N/A')],
        ["Estado Final:", diagnostico_data.get('estado_final', 'N/A')],
        ["Fecha de Entrega:", diagnostico_data.get('fecha_entrega', 'N/A')],
        ["Costo del Servicio:", f"${float(diagnostico_data.get('costo_servicio', '0') or '0'):.2f}"]
    ]
    resultado_tecnico_table = Table(resultado_tecnico_list, colWidths=[2*inch, 4*inch])
    resultado_tecnico_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#f2f2f2')),
        ('TEXTCOLOR', (0,0), (-1,0), black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (1,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,1), (-1,-1), white),
        ('GRID', (0,0), (-1,-1), 1, grey)
    ]))

    story.append(Paragraph(f"<b>Observaciones Adicionales:</b>", styles['StrongBodyText']))
    story.append(Paragraph(diagnostico_data.get('observaciones_adicionales', 'N/A'), styles['BodyText']))
    story.append(Spacer(1, 0.5 * inch))

    story.append(resultado_tecnico_table)
    story.append(Spacer(1, 0.05 * inch))

    doc.build(story)

