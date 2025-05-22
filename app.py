from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from database import init_db, get_db
from pdf_generator import generate_diagnostico_pdf
import sqlite3
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # ¡IMPORTANTE! Cambia esto por una clave secreta fuerte y única
app.debug = True

# Inicializar la base de datos al inicio de la aplicación
with app.app_context():
    init_db()

# Función auxiliar para limpiar el nombre del cliente para el nombre del archivo
def _limpiar_nombre_archivo(nombre):
    nombre_limpio = re.sub(r'[^\w\s-]', '', nombre)
    nombre_limpio = re.sub(r'\s+', '_', nombre_limpio)
    nombre_limpio = re.sub(r'_+', '_', nombre_limpio).strip('_')
    return nombre_limpio.lower()

@app.route('/')
def index():
    return render_template('index.html') 

# --- RUTA: Listado y Búsqueda de Diagnósticos (Existente) ---
@app.route('/diagnosticos')
def listar_diagnosticos():
    db = get_db()
    query = """
        SELECT
            d.id, d.fecha_recepcion, d.tipo_equipo, d.marca, d.modelo, d.estado_final,
            d.cliente_ci, 
            c.nombre AS cliente_nombre, c.telefono AS cliente_telefono
        FROM
            diagnosticos d
        JOIN
            clientes c ON d.cliente_ci = c.ci 
        WHERE 1=1
    """
    params = []

    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all').strip()
    
    if search_query:
        if search_type == 'cliente':
            query += " AND (c.nombre LIKE ? OR c.telefono LIKE ? OR c.ci LIKE ?)" 
            params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
        elif search_type == 'equipo':
            query += " AND (d.tipo_equipo LIKE ? OR d.marca LIKE ? OR d.modelo LIKE ?)"
            params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
        elif search_type == 'estado':
            query += " AND d.estado_final LIKE ?"
            params.append(f'%{search_query}%')
        else: # 'all'
            query += """
                AND (
                    c.nombre LIKE ? OR c.telefono LIKE ? OR c.ci LIKE ? OR 
                    d.tipo_equipo LIKE ? OR d.marca LIKE ? OR d.modelo LIKE ? OR
                    d.problema_reportado LIKE ? OR d.estado_final LIKE ?
                )
            """
            params.extend([
                f'%{search_query}%', f'%{search_query}%', f'%{search_query}%',
                f'%{search_query}%', f'%{search_query}%', f'%{search_query}%',
                f'%{search_query}%', f'%{search_query}%'
            ])
    
    query += " ORDER BY d.fecha_recepcion DESC"

    diagnosticos = db.execute(query, tuple(params)).fetchall()
    db.close()

    return render_template('listar_diagnosticos.html', 
                           diagnosticos=diagnosticos, 
                           search_query=search_query,
                           search_type=search_type)

# --- NUEVA RUTA: Listado y Búsqueda de Clientes ---
@app.route('/clientes')
def listar_clientes():
    db = get_db()
    query = "SELECT * FROM clientes WHERE 1=1"
    params = []

    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all').strip()

    if search_query:
        if search_type == 'ci':
            query += " AND ci LIKE ?"
            params.append(f'%{search_query}%')
        elif search_type == 'nombre':
            query += " AND nombre LIKE ?"
            params.append(f'%{search_query}%')
        elif search_type == 'telefono':
            query += " AND telefono LIKE ?"
            params.append(f'%{search_query}%')
        else: # 'all'
            query += " AND (ci LIKE ? OR nombre LIKE ? OR telefono LIKE ? OR email LIKE ? OR direccion LIKE ?)"
            params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    
    query += " ORDER BY nombre ASC" # Ordenar por nombre del cliente

    clientes = db.execute(query, tuple(params)).fetchall()
    db.close()

    return render_template('listar_clientes.html', 
                           clientes=clientes, 
                           search_query=search_query,
                           search_type=search_type)


# --- Rutas de Formularios y Acciones ---

# Ruta para generar y descargar el PDF (Existente)
@app.route('/diagnostico/pdf/<int:diagnostico_id>')
def descargar_pdf(diagnostico_id):
    db = get_db()
    diagnostico = db.execute('SELECT * FROM diagnosticos WHERE id = ?', (diagnostico_id,)).fetchone()

    if not diagnostico:
        db.close()
        flash('Diagnóstico no encontrado para generar PDF.', 'danger')
        return redirect(url_for('listar_diagnosticos'))

    cliente = db.execute('SELECT * FROM clientes WHERE ci = ?', (diagnostico['cliente_ci'],)).fetchone()
    db.close()

    if not cliente:
        flash('Cliente asociado no encontrado para generar PDF.', 'danger')
        return redirect(url_for('listar_diagnosticos'))

    cliente_nombre_limpio = _limpiar_nombre_archivo(cliente['nombre'])
    pdf_filename = f"informe_diagnostico_{cliente_nombre_limpio}_{diagnostico_id}.pdf"
    output_path = os.path.join(app.root_path, pdf_filename)

    try:
        generate_diagnostico_pdf(dict(diagnostico), dict(cliente), output_path)
        return send_file(output_path, as_attachment=True, download_name=pdf_filename)
    except Exception as e:
        flash(f'Error al generar el PDF: {e}', 'danger')
        import traceback
        traceback.print_exc()
        return redirect(url_for('ver_diagnostico', diagnostico_id=diagnostico_id))
        
# --- RUTA MODIFICADA/RENOMBRADA: Gestión de Cliente (Creación y Edición) ---
# Ahora acepta un cliente_ci opcional para edición
@app.route('/cliente/gestion', methods=['GET', 'POST'])
@app.route('/cliente/gestion/<string:cliente_ci>', methods=['GET', 'POST'])
def gestion_cliente(cliente_ci=None):
    db = get_db()
    cliente = None # Cliente existente si estamos editando

    if cliente_ci: # Modo edición
        cliente = db.execute('SELECT * FROM clientes WHERE ci = ?', (cliente_ci,)).fetchone()
        if not cliente:
            db.close()
            flash('Cliente no encontrado para edición.', 'danger')
            return redirect(url_for('listar_clientes'))
    
    if request.method == 'POST':
        ci = request.form['ci'].strip()
        nombre = request.form['nombre']
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        direccion = request.form.get('direccion')

        if not ci or not nombre:
            flash('La Cédula de Identidad y el nombre del cliente son obligatorios.', 'danger')
            # Mantener los datos del formulario si hay un error de validación
            form_data = request.form
            db.close()
            return render_template('form_cliente.html', 
                                   cliente=cliente, # Pasar el objeto cliente para la plantilla (si estamos editando)
                                   form_data=form_data)

        try:
            cursor = db.cursor()
            if cliente_ci: # Es una actualización de un cliente existente
                # Si la CI fue cambiada, verificar que la nueva CI no exista ya
                if ci != cliente_ci:
                    existing_client = db.execute('SELECT ci FROM clientes WHERE ci = ?', (ci,)).fetchone()
                    if existing_client:
                        db.close()
                        flash(f'La nueva Cédula de Identidad {ci} ya está registrada para otro cliente.', 'danger')
                        return render_template('form_cliente.html', 
                                               cliente=cliente, # Pasar el objeto cliente original
                                               form_data=request.form)
                    # Si la CI cambia, también debemos actualizarla en los diagnósticos asociados
                    cursor.execute("UPDATE diagnosticos SET cliente_ci = ? WHERE cliente_ci = ?", (ci, cliente_ci))

                cursor.execute("""
                    UPDATE clientes SET
                        ci = ?, nombre = ?, telefono = ?, email = ?, direccion = ?
                    WHERE ci = ?
                """, (ci, nombre, telefono, email, direccion, cliente_ci))
                db.commit()
                db.close()
                flash('Datos del cliente actualizados exitosamente!', 'success')
                return redirect(url_for('listar_clientes')) # Volver a la lista de clientes
            else: # Es una nueva creación de cliente
                # Verificar si la CI ya existe
                existing_client = db.execute('SELECT ci FROM clientes WHERE ci = ?', (ci,)).fetchone()
                if existing_client:
                    db.close()
                    flash(f'La Cédula de Identidad {ci} ya está registrada.', 'danger')
                    return render_template('form_cliente.html', form_data=request.form)

                cursor.execute("""
                    INSERT INTO clientes (ci, nombre, telefono, email, direccion)
                    VALUES (?, ?, ?, ?, ?)
                """, (ci, nombre, telefono, email, direccion))
                db.commit()
                db.close()
                flash('Cliente registrado exitosamente!', 'success')
                # Después de crear un cliente, podemos redirigir a la lista de clientes
                # o a la página de nuevo diagnóstico con este cliente precargado
                return redirect(url_for('listar_clientes')) 
        except sqlite3.Error as e:
            flash(f'Error al guardar/actualizar cliente: {e}', 'danger')
            form_data = request.form
            db.close()
            return render_template('form_cliente.html', 
                                   cliente=cliente, 
                                   form_data=form_data)

    # Si es GET, rellenar el formulario con los datos existentes si es modo edición
    form_data = dict(cliente) if cliente else {}
    db.close()
    return render_template('form_cliente.html', 
                           cliente=cliente, # Pasa el objeto cliente para la plantilla
                           form_data=form_data)


# Paso 2: Formulario de Equipo (Creación y Edición) (Existente)
@app.route('/diagnostico/equipo/<string:cliente_ci>', methods=['GET', 'POST'])
@app.route('/diagnostico/equipo/<string:cliente_ci>/<int:diagnostico_id>', methods=['GET', 'POST'])
def diagnostico_equipo(cliente_ci, diagnostico_id=None):
    db = get_db()
    cliente = db.execute('SELECT * FROM clientes WHERE ci = ?', (cliente_ci,)).fetchone()
    
    if not cliente:
        db.close()
        flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('listar_clientes'))

    diagnostico = None
    if diagnostico_id: 
        diagnostico = db.execute('SELECT * FROM diagnosticos WHERE id = ? AND cliente_ci = ?', (diagnostico_id, cliente_ci)).fetchone()
        if not diagnostico:
            db.close()
            flash('Diagnóstico no encontrado para edición o no pertenece a este cliente.', 'danger')
            return redirect(url_for('listar_diagnosticos'))
    
    if request.method == 'POST':
        tipo_equipo = request.form['tipo_equipo']
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        serial = request.form.get('serial')
        accesorios_recibidos = request.form.get('accesorios_recibidos')
        problema_reportado = request.form['problema_reportado']

        if not tipo_equipo or not problema_reportado:
            flash('Tipo de equipo y problema reportado son obligatorios.', 'danger')
            form_data = request.form
            db.close()
            return render_template('form_equipo.html', 
                                   cliente=cliente, 
                                   diagnostico=diagnostico,
                                   form_data=form_data)

        try:
            cursor = db.cursor()
            if diagnostico_id: 
                cursor.execute("""
                    UPDATE diagnosticos SET
                        tipo_equipo = ?, marca = ?, modelo = ?, serial = ?,
                        accesorios_recibidos = ?, problema_reportado = ?
                    WHERE id = ? AND cliente_ci = ? 
                """, (
                    tipo_equipo, marca, modelo, serial,
                    accesorios_recibidos, problema_reportado,
                    diagnostico_id, cliente_ci
                ))
                db.commit()
                db.close()
                flash('Datos del equipo actualizados exitosamente!', 'success')
                return redirect(url_for('ver_diagnostico', diagnostico_id=diagnostico_id))
            else: 
                fecha_recepcion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO diagnosticos (
                        cliente_ci, fecha_recepcion, tipo_equipo, marca, modelo, serial,
                        accesorios_recibidos, problema_reportado, estado_final
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cliente_ci, fecha_recepcion, tipo_equipo, marca, modelo, serial,
                    accesorios_recibidos, problema_reportado, 'Pendiente'
                ))
                db.commit()
                diagnostico_id = cursor.lastrowid
                db.close()
                flash('Datos del equipo y problema guardados exitosamente!', 'success')
                return redirect(url_for('diagnostico_resultado', diagnostico_id=diagnostico_id))
        except sqlite3.Error as e:
            flash(f'Error al guardar/actualizar equipo y problema: {e}', 'danger')
            form_data = request.form
            db.close()
            return render_template('form_equipo.html', 
                                   cliente=cliente, 
                                   diagnostico=diagnostico,
                                   form_data=form_data)

    form_data = dict(diagnostico) if diagnostico else {}
    db.close()
    return render_template('form_equipo.html', 
                           cliente=cliente, 
                           diagnostico=diagnostico,
                           form_data=form_data)


# Paso 3: Formulario de Diagnóstico y Resultado (Existente)
@app.route('/diagnostico/resultado/<int:diagnostico_id>', methods=['GET', 'POST'])
def diagnostico_resultado(diagnostico_id):
    db = get_db()
    diagnostico = db.execute('SELECT * FROM diagnosticos WHERE id = ?', (diagnostico_id,)).fetchone()
    
    if not diagnostico:
        db.close()
        flash('Diagnóstico no encontrado.', 'danger')
        return redirect(url_for('listar_diagnosticos'))

    cliente = db.execute('SELECT nombre FROM clientes WHERE ci = ?', (diagnostico['cliente_ci'],)).fetchone()
    db.close()

    if not cliente:
        flash('Cliente asociado no encontrado.', 'danger')
        return redirect(url_for('listar_diagnosticos'))

    if request.method == 'POST':
        diagnostico_inicial = request.form.get('diagnostico_inicial')
        solucion_aplicada = request.form.get('solucion_aplicada')
        piezas_reemplazadas = request.form.get('piezas_reemplazadas')
        estado_final = request.form['estado_final']
        costo_servicio = request.form.get('costo_servicio')
        observaciones_adicionales = request.form.get('observaciones_adicionales')
        fecha_entrega = request.form.get('fecha_entrega')

        if not estado_final:
            flash('El estado final es obligatorio.', 'danger')
            return render_template('form_resultado.html', diagnostico=diagnostico, cliente_nombre=cliente['nombre'], form_data=request.form)

        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                UPDATE diagnosticos SET
                    diagnostico_inicial = ?,
                    solucion_aplicada = ?,
                    piezas_reemplazadas = ?,
                    estado_final = ?,
                    fecha_entrega = ?,
                    costo_servicio = ?,
                    observaciones_adicionales = ?
                WHERE id = ?
            """, (
                diagnostico_inicial, solucion_aplicada, piezas_reemplazadas, estado_final,
                fecha_entrega, costo_servicio, observaciones_adicionales,
                diagnostico_id
            ))
            db.commit()
            db.close()
            flash('Diagnóstico y resultado actualizados exitosamente!', 'success')
            return redirect(url_for('ver_diagnostico', diagnostico_id=diagnostico_id))
        except sqlite3.Error as e:
            flash(f'Error al actualizar el diagnóstico: {e}', 'danger')
            return render_template('form_resultado.html', diagnostico=diagnostico, cliente_nombre=cliente['nombre'], form_data=request.form)

    form_data = dict(diagnostico) if diagnostico else {}
    return render_template('form_resultado.html', diagnostico=diagnostico, cliente_nombre=cliente['nombre'], form_data=form_data)


# Ruta para ver un diagnóstico completo (Existente)
@app.route('/diagnostico/ver/<int:diagnostico_id>')
def ver_diagnostico(diagnostico_id):
    db = get_db()
    diagnostico = db.execute('SELECT * FROM diagnosticos WHERE id = ?', (diagnostico_id,)).fetchone()
    
    if not diagnostico:
        db.close()
        flash('Diagnóstico no encontrado.', 'danger')
        return redirect(url_for('listar_diagnosticos'))

    cliente = db.execute('SELECT * FROM clientes WHERE ci = ?', (diagnostico['cliente_ci'],)).fetchone()
    db.close()

    if not cliente:
        flash('Cliente asociado no encontrado.', 'danger')
        return redirect(url_for('listar_diagnosticos'))

    return render_template('ver_diagnostico.html', diagnostico=diagnostico, cliente=cliente)

if __name__ == '__main__':
    app.run(debug=True)
