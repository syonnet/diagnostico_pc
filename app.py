from flask import Flask, render_template, request, redirect, url_for, flash, session, g, abort, send_file
from database import init_db, get_db
from pdf_generator import generate_diagnostico_pdf
import sqlite3
from datetime import datetime
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import tempfile # Importar el módulo tempfile

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # ¡IMPORTANTE! Cambia esto por una clave secreta fuerte y única para producción
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

# --- Context Processor para el usuario actual ---
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        db.close()

# --- Decorador para rutas protegidas por login ---
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# --- Decorador para autorización por rol ---
def role_required(required_role):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if not g.user:
                flash('Debes iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('login'))
            
            user_role = g.user['role'].lower() if g.user['role'] else 'user'
            
            if user_role != required_role.lower():
                flash(f'No tienes permiso para acceder a esta funcionalidad. Solo los usuarios con rol "{required_role}" pueden hacerlo.', 'danger')
                return redirect(url_for('index'))
            return view(**kwargs)
        return wrapped_view
    return decorator


# --- Rutas de Autenticación ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form.get('role', 'user') 
        
        # Validación: Solo un admin logueado puede registrar a otro admin
        if role.lower() == 'admin' and (not g.user or g.user['role'].lower() != 'admin'):
            flash('No tienes permiso para registrar un usuario con rol de administrador.', 'danger')
            return render_template('register.html', form_data=request.form)

        if not username or not password:
            flash('El nombre de usuario y la contraseña son obligatorios.', 'danger')
            return render_template('register.html', form_data=request.form)

        db = get_db()
        try:
            hashed_password = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, hashed_password, role),
            )
            db.commit()
            flash('Registro exitoso. ¡Ahora puedes iniciar sesión!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash(f'El nombre de usuario "{username}" ya está registrado.', 'danger')
        except sqlite3.Error as e:
            flash(f'Error al registrar usuario: {e}', 'danger')
        finally:
            db.close()
    return render_template('register.html', form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        db.close()

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Nombre de usuario o contraseña incorrectos.', 'danger')
        else:
            session.clear()
            session['user_id'] = user['id']
            flash(f'¡Bienvenido, {user["username"]}!', 'success')
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

# --- Rutas de la Aplicación ---
@app.route('/')
def index():
    return render_template('index.html') 

# --- RUTA: Panel de Control (Dashboard) ---
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    
    # Total de clientes
    total_clientes = db.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
    
    # Total de diagnósticos
    total_diagnosticos = db.execute('SELECT COUNT(*) FROM diagnosticos').fetchone()[0]
    
    # Diagnósticos por estado
    diagnosticos_por_estado_raw = db.execute('SELECT estado_final, COUNT(*) FROM diagnosticos GROUP BY estado_final').fetchall()
    diagnosticos_por_estado = {row['estado_final']: row['COUNT(*)'] for row in diagnosticos_por_estado_raw}
    
    # Ingresos estimados (suma de costo_servicio para diagnósticos "Reparado" o "Entregado")
    ingresos_estimados_raw = db.execute("SELECT SUM(costo_servicio) FROM diagnosticos WHERE estado_final IN ('Reparado', 'Entregado')").fetchone()[0]
    ingresos_estimados = ingresos_estimados_raw if ingresos_estimados_raw is not None else 0.0
    
    db.close()
    
    return render_template('dashboard.html',
                           total_clientes=total_clientes,
                           total_diagnosticos=total_diagnosticos,
                           diagnosticos_por_estado=diagnosticos_por_estado,
                           ingresos_estimados=ingresos_estimados)


@app.route('/diagnosticos')
@login_required
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

@app.route('/clientes')
@login_required
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
    
    query += " ORDER BY nombre ASC"

    clientes = db.execute(query, tuple(params)).fetchall()
    db.close()

    return render_template('listar_clientes.html', 
                           clientes=clientes, 
                           search_query=search_query,
                           search_type=search_type)

@app.route('/diagnostico/pdf/<int:diagnostico_id>')
@login_required
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

    # Usar tempfile para crear un archivo temporal de forma segura
    # delete=False porque lo eliminaremos manualmente después de enviar
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
        output_path = temp_pdf_file.name # Obtener la ruta completa del archivo temporal

    try:
        # Genera el PDF en la ruta del archivo temporal
        generate_diagnostico_pdf(dict(diagnostico), dict(cliente), output_path)
        
        # Envía el archivo como adjunto para que se descargue
        response = send_file(output_path, as_attachment=True, download_name=pdf_filename)
        
        # Después de enviar el archivo, programar su eliminación
        @response.call_on_close
        def remove_file():
            try:
                os.remove(output_path)
                print(f"Archivo temporal eliminado: {output_path}")
            except Exception as e:
                print(f"Error al eliminar el archivo temporal {output_path}: {e}")
        
        return response
    except Exception as e:
        flash(f'Error al generar el PDF: {e}', 'danger')
        import traceback
        traceback.print_exc()
        # Asegurarse de que el archivo temporal se elimine incluso si ocurre un error
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"Archivo temporal de error eliminado: {output_path}")
            except Exception as cleanup_e:
                print(f"Error al limpiar el archivo temporal de error {output_path}: {cleanup_e}")
        return redirect(url_for('ver_diagnostico', diagnostico_id=diagnostico_id))
        
@app.route('/diagnostico/iniciar', methods=['GET', 'POST'])
@login_required
def iniciar_diagnostico():
    if request.method == 'POST':
        ci = request.form['ci'].strip()
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        direccion = request.form.get('direccion')
        
        # Validar longitud de la CI
        if not ci or len(ci) != 10:
            flash('La Cédula de Identidad debe tener exactamente 10 caracteres.', 'danger')
            return render_template('form_cliente_inicio.html', form_data=request.form, ci_provided=ci, nombre_provided=nombre, telefono_provided=telefono, email_provided=email, direccion_provided=direccion)

        db = get_db()
        existing_client = db.execute('SELECT * FROM clientes WHERE ci = ?', (ci,)).fetchone()

        if existing_client:
            db.close()
            flash(f'Cliente {existing_client["nombre"]} (CI: {ci}) seleccionado para el nuevo diagnóstico.', 'info')
            return redirect(url_for('diagnostico_equipo', cliente_ci=ci))
        else:
            # Si el cliente no existe, debemos pedir el nombre para crearlo
            if not nombre:
                db.close()
                flash(f'La Cédula de Identidad {ci} no está registrada. Por favor, ingrese el nombre del nuevo cliente y los demás datos.', 'danger')
                return render_template('form_cliente_inicio.html', form_data=request.form, ci_provided=ci, nombre_provided=nombre, telefono_provided=telefono, email_provided=email, direccion_provided=direccion)
            
            try:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO clientes (ci, nombre, telefono, email, direccion)
                    VALUES (?, ?, ?, ?, ?)
                """, (ci, nombre, telefono, email, direccion))
                db.commit()
                db.close()
                flash(f'Nuevo cliente {nombre} (CI: {ci}) registrado y seleccionado para el diagnóstico.', 'success')
                return redirect(url_for('diagnostico_equipo', cliente_ci=ci))
            except sqlite3.IntegrityError as e:
                db.close()
                if "UNIQUE constraint failed: clientes.ci" in str(e):
                    flash(f'Error: La Cédula de Identidad {ci} ya está registrada. Por favor, use una CI diferente o seleccione el cliente existente.', 'danger')
                else:
                    flash(f'Error de base de datos al registrar el nuevo cliente: {e}', 'danger')
                return render_template('form_cliente_inicio.html', form_data=request.form, ci_provided=ci, nombre_provided=nombre, telefono_provided=telefono, email_provided=email, direccion_provided=direccion)
            except sqlite3.Error as e:
                db.close()
                flash(f'Error al registrar el nuevo cliente: {e}', 'danger')
                return render_template('form_cliente_inicio.html', form_data=request.form, ci_provided=ci, nombre_provided=nombre, telefono_provided=telefono, email_provided=email, direccion_provided=direccion)

    return render_template('form_cliente_inicio.html', form_data={})

@app.route('/cliente/editar/<string:cliente_ci>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_cliente(cliente_ci):
    db = get_db()
    cliente = db.execute('SELECT * FROM clientes WHERE ci = ?', (cliente_ci,)).fetchone()
    
    if not cliente:
        db.close()
        flash('Cliente no encontrado para edición.', 'danger')
        return redirect(url_for('listar_clientes'))
    
    if request.method == 'POST':
        ci_form = request.form['ci'].strip()
        nombre = request.form['nombre']
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        direccion = request.form.get('direccion')

        if not ci_form or not nombre:
            flash('La Cédula de Identidad y el nombre del cliente son obligatorios.', 'danger')
            form_data = request.form
            db.close()
            return render_template('form_cliente.html', 
                                   cliente=cliente, 
                                   form_data=form_data)
        
        # Validar longitud de la CI en edición
        if len(ci_form) != 10:
            flash('La Cédula de Identidad debe tener exactamente 10 caracteres.', 'danger')
            form_data = request.form
            db.close()
            return render_template('form_cliente.html', 
                                   cliente=cliente, 
                                   form_data=form_data)

        try:
            cursor = db.cursor()
            if ci_form != cliente_ci:
                existing_client = db.execute('SELECT ci FROM clientes WHERE ci = ?', (ci_form,)).fetchone()
                if existing_client:
                    db.close()
                    flash(f'La nueva Cédula de Identidad {ci_form} ya está registrada para otro cliente.', 'danger')
                    return render_template('form_cliente.html', 
                                           cliente=cliente, 
                                           form_data=request.form)
                cursor.execute("UPDATE diagnosticos SET cliente_ci = ? WHERE cliente_ci = ?", (ci_form, cliente_ci))

            cursor.execute("""
                UPDATE clientes SET
                    ci = ?, nombre = ?, telefono = ?, email = ?, direccion = ?
                WHERE ci = ?
            """, (ci_form, nombre, telefono, email, direccion, cliente_ci))
            db.commit()
            db.close()
            flash('Datos del cliente actualizados exitosamente!', 'success')
            return redirect(url_for('listar_clientes')) 
        except sqlite3.Error as e:
            flash(f'Error al actualizar cliente: {e}', 'danger')
            form_data = request.form
            db.close()
            return render_template('form_cliente.html', 
                                   cliente=cliente, 
                                   form_data=form_data)

    form_data = dict(cliente) if cliente else {}
    db.close()
    return render_template('form_cliente.html', 
                           cliente=cliente, 
                           form_data=form_data)

@app.route('/diagnostico/equipo/<string:cliente_ci>', methods=['GET', 'POST'])
@app.route('/diagnostico/equipo/<string:cliente_ci>/<int:diagnostico_id>', methods=['GET', 'POST'])
@login_required
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
        componentes = request.form.get('componentes') # NUEVO CAMPO
        accesorios_recibidos = request.form.get('accesorios_recibidos')
        problema_reportado = request.form['problema_reportado']
        fecha_recepcion = request.form.get('fecha_recepcion') # Asegúrate de obtenerlo del formulario

        if not tipo_equipo or not problema_reportado or not fecha_recepcion: # Validar fecha_recepcion
            flash('Tipo de equipo, problema reportado y fecha de recepción son obligatorios.', 'danger')
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
                        componentes = ?, -- NUEVO CAMPO
                        accesorios_recibidos = ?, problema_reportado = ?, fecha_recepcion = ?
                    WHERE id = ? AND cliente_ci = ? 
                """, (
                    tipo_equipo, marca, modelo, serial,
                    componentes, # NUEVO CAMPO
                    accesorios_recibidos, problema_reportado, fecha_recepcion,
                    diagnostico_id, cliente_ci
                ))
                db.commit()
                db.close()
                flash('Datos del equipo actualizados exitosamente!', 'success')
                return redirect(url_for('ver_diagnostico', diagnostico_id=diagnostico_id))
            else: 
                cursor.execute("""
                    INSERT INTO diagnosticos (
                        cliente_ci, fecha_recepcion, tipo_equipo, marca, modelo, serial,
                        componentes, -- NUEVO CAMPO
                        accesorios_recibidos, problema_reportado, estado_final
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cliente_ci, fecha_recepcion, tipo_equipo, marca, modelo, serial,
                    componentes, # NUEVO CAMPO
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
    # Asegurarse de que 'componentes' esté en form_data para la precarga
    if 'componentes' not in form_data:
        form_data['componentes'] = diagnostico['componentes'] if diagnostico else ''

    if not diagnostico_id:
        if 'fecha_recepcion' not in form_data:
            form_data['fecha_recepcion'] = datetime.now().strftime('%Y-%m-%d')
    elif diagnostico and diagnostico['fecha_recepcion']:
        form_data['fecha_recepcion'] = diagnostico['fecha_recepcion'].split(' ')[0]

    db.close()
    return render_template('form_equipo.html', 
                           cliente=cliente, 
                           diagnostico=diagnostico,
                           form_data=form_data)

@app.route('/diagnostico/resultado/<int:diagnostico_id>', methods=['GET', 'POST'])
@login_required
def diagnostico_resultado(diagnostico_id):
    db = get_db()
    diagnostico = db.execute('SELECT * FROM diagnosticos WHERE id = ?', (diagnostico_id,)).fetchone()
    
    if not diagnostico:
        db.close()
        flash('Diagnóstico no encontrado.', 'danger')
        return redirect(url_for('listar_diagnosticos'))

    cliente = db.execute('SELECT nombre FROM clientes WHERE ci = ?', (diagnostico['cliente_ci'],)).fetchone()
    
    estados_finalizados = ['Reparado', 'Irreparable', 'Entregado', 'Devuelto sin reparar']
    
    if diagnostico['estado_final'] in estados_finalizados and request.method == 'POST':
        if not g.user or g.user['role'].lower() != 'admin':
            db.close()
            flash('No tienes permiso para modificar un diagnóstico finalizado. Solo los administradores pueden hacerlo.', 'danger')
            return redirect(url_for('ver_diagnostico', diagnostico_id=diagnostico_id))
    
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
            db.close()
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
            db.close()
            return render_template('form_resultado.html', diagnostico=diagnostico, cliente_nombre=cliente['nombre'], form_data=request.form)

    form_data = dict(diagnostico) if diagnostico else {}
    db.close()
    return render_template('form_resultado.html', diagnostico=diagnostico, cliente_nombre=cliente['nombre'], form_data=form_data)

@app.route('/diagnostico/ver/<int:diagnostico_id>')
@login_required
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

@app.route('/diagnostico/eliminar/<int:diagnostico_id>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_diagnostico(diagnostico_id):
    db = get_db()
    try:
        diagnostico = db.execute('SELECT id FROM diagnosticos WHERE id = ?', (diagnostico_id,)).fetchone()
        if not diagnostico:
            flash('Diagnóstico no encontrado para eliminar.', 'danger')
            return redirect(url_for('listar_diagnosticos'))

        cursor = db.cursor()
        cursor.execute("DELETE FROM diagnosticos WHERE id = ?", (diagnostico_id,))
        db.commit()
        flash('Diagnóstico eliminado exitosamente.', 'success')
    except sqlite3.Error as e:
        flash(f'Error al eliminar el diagnóstico: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('listar_diagnosticos'))

@app.route('/cliente/eliminar/<string:cliente_ci>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_cliente(cliente_ci):
    db = get_db()
    try:
        cliente = db.execute('SELECT ci, nombre FROM clientes WHERE ci = ?', (cliente_ci,)).fetchone()
        if not cliente:
            flash('Cliente no encontrado para eliminar.', 'danger')
            return redirect(url_for('listar_clientes'))
        
        diagnosticos_asociados = db.execute('SELECT COUNT(*) FROM diagnosticos WHERE cliente_ci = ?', (cliente_ci,)).fetchone()[0]
        
        if diagnosticos_asociados > 0:
            flash(f'No se puede eliminar el cliente "{cliente["nombre"]}" (CI: {cliente_ci}) porque tiene {diagnosticos_asociados} diagnóstico(s) asociado(s). Elimine los diagnósticos primero.', 'danger')
        else:
            cursor = db.cursor()
            cursor.execute("DELETE FROM clientes WHERE ci = ?", (cliente_ci,))
            db.commit()
            flash(f'Cliente "{cliente["nombre"]}" (CI: {cliente_ci}) eliminado exitosamente.', 'success')
    except sqlite3.Error as e:
        flash(f'Error al eliminar el cliente: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('listar_clientes'))

# --- Rutas de Gestión de Usuarios ---

@app.route('/users')
@login_required
@role_required('admin')
def listar_usuarios():
    db = get_db()
    users = db.execute('SELECT id, username, role FROM users ORDER BY username ASC').fetchall()
    db.close()
    return render_template('listar_usuarios.html', users=users)

@app.route('/user/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form.get('role', 'user')

        if not username or not password:
            flash('El nombre de usuario y la contraseña son obligatorios.', 'danger')
            return render_template('form_usuario.html', form_data=request.form)

        db = get_db()
        try:
            hashed_password = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, hashed_password, role),
            )
            db.commit()
            flash(f'Usuario "{username}" agregado exitosamente.', 'success')
            return redirect(url_for('listar_usuarios'))
        except sqlite3.IntegrityError:
            flash(f'El nombre de usuario "{username}" ya está registrado.', 'danger')
        except sqlite3.Error as e:
            flash(f'Error al agregar usuario: {e}', 'danger')
        finally:
            db.close()
    return render_template('form_usuario.html', form_data={})

@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    db = get_db()
    user = db.execute('SELECT id, username, role FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        db.close()
        flash('Usuario no encontrado para edición.', 'danger')
        return redirect(url_for('listar_usuarios'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form.get('password')
        role = request.form.get('role', 'user')

        if not username:
            flash('El nombre de usuario es obligatorio.', 'danger')
            return render_template('form_usuario.html', user=user, form_data=request.form)

        db = get_db()
        try:
            update_query = "UPDATE users SET username = ?, role = ? WHERE id = ?"
            params = [username, role, user_id]

            if password:
                hashed_password = generate_password_hash(password)
                update_query = "UPDATE users SET username = ?, password_hash = ?, role = ? WHERE id = ?"
                params = [username, hashed_password, role, user_id]

            db.execute(update_query, tuple(params))
            db.commit()
            flash(f'Usuario "{username}" actualizado exitosamente.', 'success')
            return redirect(url_for('listar_usuarios'))
        except sqlite3.IntegrityError:
            flash(f'El nombre de usuario "{username}" ya está registrado.', 'danger')
        except sqlite3.Error as e:
            flash(f'Error al actualizar usuario: {e}', 'danger')
        finally:
            db.close()
    
    form_data = dict(user)
    db.close()
    return render_template('form_usuario.html', user=user, form_data=form_data)

@app.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    db = get_db()
    try:
        if g.user and g.user['id'] == user_id:
            flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
            return redirect(url_for('listar_usuarios'))

        user_to_delete = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user_to_delete:
            flash('Usuario no encontrado para eliminar.', 'danger')
            return redirect(url_for('listar_usuarios'))

        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        flash(f'Usuario "{user_to_delete["username"]}" eliminado exitosamente.', 'success')
    except sqlite3.Error as e:
        flash(f'Error al eliminar usuario: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('listar_usuarios'))

if __name__ == '__main__':
    app.run(debug=True)
