import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'tu_llave_secreta_aqui'

# --- Gestión de la Base de Datos ---
def get_db_connection():
    conn = sqlite3.connect('cine.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funciones (
            id_funcion TEXT PRIMARY KEY,
            titulo_pelicula TEXT NOT NULL,
            formato_datos TEXT,
            asientos_disponibles INTEGER NOT NULL,
            precio_boleto REAL NOT NULL,
            sala TEXT,
            estado_funcion TEXT NOT NULL DEFAULT 'Próximamente'
        )
    ''')
    conn.commit()
    conn.close()

# --- RUTAS PÚBLICAS (CLIENTES) ---

@app.route('/')
def home():
    """Página de inicio principal del sitio."""
    return render_template('home.html')

@app.route('/peliculas')
def peliculas():
    """Muestra la página con las tarjetas de películas."""
    # Datos de las películas para generar las tarjetas automáticamente
    lista_peliculas = [
        {
            'titulo': 'La Maldición del Perla Negra',
            'descripcion': 'El herrero Will Turner se une al excéntrico pirata Jack Sparrow para salvar a su amada, la hija del gobernador.',
            'imagen': 'a.jpg'
        },
        {
            'titulo': 'El Cofre de la Muerte',
            'descripcion': 'Jack Sparrow corre para recuperar el corazón de Davy Jones para evitar esclavizar su alma al servicio de Jones.',
            'imagen': 'b.jpg'
        },
        {
            'titulo': 'En el Fin del Mundo',
            'descripcion': 'Will Turner y Elizabeth Swann deben navegar fuera del borde del mapa y forjar alianzas finales.',
            'imagen': 'c.jpg'
        },
        {
            'titulo': 'Navegando Aguas Misteriosas',
            'descripcion': 'Jack Sparrow y Barbossa se embarcan en una búsqueda para encontrar la esquiva Fuente de la Juventud.',
            'imagen': 'd.jpg'
        },
        {
            'titulo': 'La Venganza de Salazar',
            'descripcion': 'El Capitán Jack Sparrow es perseguido por un viejo rival, el Capitán Salazar y sus piratas fantasmas.',
            'imagen': 'e.jpg'
        }
    ]
    return render_template('peliculas.html', peliculas=lista_peliculas)

@app.route('/formulario')
def formulario():
    """Muestra la página del formulario de contacto."""
    return render_template('formulario.html')


# --- RUTAS DE GESTIÓN (ADMINISTRACIÓN) ---

@app.route('/cine')
def gestion_cine():
    conn = get_db_connection()
    query = request.args.get('query', '')
    if query:
        funciones = conn.execute(
            'SELECT * FROM funciones WHERE (estado_funcion = "En Cartelera" OR estado_funcion = "Agotada") AND (titulo_pelicula LIKE ? OR sala LIKE ?)',
            ('%' + query + '%', '%' + query + '%')
        ).fetchall()
    else:
        funciones = conn.execute('SELECT * FROM funciones WHERE estado_funcion = "En Cartelera" OR estado_funcion = "Agotada"').fetchall()
    conn.close()
    return render_template('index.html', funciones=funciones, query=query, is_admin_view=False)

@app.route('/cine/admin')
def admin():
    conn = get_db_connection()
    query = request.args.get('query', '')
    if query:
        funciones = conn.execute(
            'SELECT * FROM funciones WHERE titulo_pelicula LIKE ? OR sala LIKE ?',
            ('%' + query + '%', '%' + query + '%')
        ).fetchall()
    else:
        funciones = conn.execute('SELECT * FROM funciones ORDER BY estado_funcion').fetchall()
    conn.close()
    return render_template('index.html', funciones=funciones, query=query, is_admin_view=True)

@app.route('/cine/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        try:
            id_funcion = request.form['id_funcion']
            titulo_pelicula = request.form['titulo_pelicula']
            formato_datos = request.form['formato_datos']
            asientos_disponibles = request.form['asientos_disponibles']
            precio_boleto = request.form['precio_boleto']
            sala = request.form['sala']
            estado_funcion = request.form['estado_funcion']

            conn = get_db_connection()
            conn.execute(
                'INSERT INTO funciones (id_funcion, titulo_pelicula, formato_datos, asientos_disponibles, precio_boleto, sala, estado_funcion) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (id_funcion, titulo_pelicula, formato_datos, int(asientos_disponibles), float(precio_boleto), sala, estado_funcion)
            )
            conn.commit()
            conn.close()
            flash('¡Función agregada exitosamente!', 'success')
            return redirect(url_for('admin'))
        except sqlite3.IntegrityError:
            flash('Error: El ID de la función ya existe.', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error: {e}', 'danger')

    return render_template('agregar.html')

@app.route('/cine/editar/<id_funcion>', methods=['GET', 'POST'])
def editar(id_funcion):
    conn = get_db_connection()
    funcion = conn.execute('SELECT * FROM funciones WHERE id_funcion = ?', (id_funcion,)).fetchone()

    if request.method == 'POST':
        conn.execute(
            'UPDATE funciones SET titulo_pelicula = ?, formato_datos = ?, asientos_disponibles = ?, precio_boleto = ?, sala = ?, estado_funcion = ? WHERE id_funcion = ?',
            (request.form['titulo_pelicula'], request.form['formato_datos'], int(request.form['asientos_disponibles']), 
             float(request.form['precio_boleto']), request.form['sala'], request.form['estado_funcion'], id_funcion)
        )
        conn.commit()
        conn.close()
        flash('¡Función actualizada exitosamente!', 'success')
        return redirect(url_for('admin'))

    conn.close()
    return render_template('editar.html', funcion=funcion)

@app.route('/cine/finalizar/<id_funcion>')
def finalizar(id_funcion):
    conn = get_db_connection()
    conn.execute('UPDATE funciones SET estado_funcion = "Finalizada" WHERE id_funcion = ?', (id_funcion,))
    conn.commit()
    conn.close()
    flash('La función ha sido marcada como "Finalizada".', 'warning')
    return redirect(url_for('admin'))

@app.route('/cine/vender_entrada/<id_funcion>')
def vender_entrada(id_funcion):
    conn = get_db_connection()
    funcion = conn.execute('SELECT * FROM funciones WHERE id_funcion = ?', (id_funcion,)).fetchone()

    if funcion and funcion['asientos_disponibles'] > 0:
        nuevos_asientos = funcion['asientos_disponibles'] - 1
        nuevo_estado = 'Agotada' if nuevos_asientos == 0 else funcion['estado_funcion']
        conn.execute('UPDATE funciones SET asientos_disponibles = ?, estado_funcion = ? WHERE id_funcion = ?', (nuevos_asientos, nuevo_estado, id_funcion))
        conn.commit()
        flash(f"¡Entrada vendida para '{funcion['titulo_pelicula']}'!", 'success')
    else:
        flash('No se pudo vender la entrada. Agotada o no existe.', 'danger')

    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)