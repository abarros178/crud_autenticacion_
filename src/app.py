from flask import Flask,jsonify,request,session
from werkzeug.security import generate_password_hash, check_password_hash
from config import config
from flask_mysqldb import MySQL
import uuid
from datetime import datetime, timedelta



app = Flask(__name__)

app.config['SECRET_KEY'] = '165asa68dsdsf551'

conexion=MySQL(app)

@app.route('/crear_persona', methods=['POST'])
def crear_persona():
    nombrecompleto=request.json.get('nombrecompleto')
    identificacion=request.json.get('identificacion')
    correo=request.json.get('correo')
    contrasena=request.json.get('contrasena')
    direccion=request.json.get('direccion')
    telefono=request.json.get('telefono')
    fecha_nacimiento=request.json.get('fecha_nacimiento')
    if not nombrecompleto or not identificacion or not correo or not contrasena  or not direccion  or not telefono or not fecha_nacimiento:
        return jsonify({'mensaje': 'Por favor ingrese todos los datos requeridos.'}), 400

    cursor = conexion.connection.cursor()
    cursor.execute('SELECT * FROM persona WHERE identificacion = %s', (identificacion,))
    persona_existente = cursor.fetchone()
    cursor.close()
    if persona_existente:
        return jsonify({'mensaje': 'La identificación ya se encuentra registrada.'}), 409
    
    cursor = conexion.connection.cursor()
    cursor.execute('SELECT * FROM persona WHERE correo = %s', (correo,))
    persona_existente = cursor.fetchone()
    cursor.close()
    if persona_existente:
        return jsonify({'mensaje': 'El correo ya se encuentra registrado.'}), 409
    
    usuario_id = str(uuid.uuid4())
    password = generate_password_hash(contrasena)

    cursor = conexion.connection.cursor()
    cursor.execute('INSERT INTO persona (nombrecompleto, identificacion, correo,direccion,telefono,fecha_nacimiento) VALUES (%s, %s, %s, %s, %s, %s)', (nombrecompleto, identificacion, correo,direccion,telefono,fecha_nacimiento))
    conexion.connection.commit()
    cursor.close()

    cursor = conexion.connection.cursor()
    cursor.execute('INSERT INTO usuario (id, correo, contrasena) VALUES (%s, %s, %s)', (usuario_id, correo, password))
    conexion.connection.commit()
    cursor.close()

    cursor = conexion.connection.cursor()
    cursor.execute('SELECT * FROM usuario WHERE correo = %s', (correo,))
    usuario = cursor.fetchone()
    cursor.close()
    if not usuario:
        return jsonify({'mensaje': 'Ha ocurrido un error al autenticar al usuario.'}), 500

    session['usuario_id'] = str(usuario[0])
    return jsonify({'mensaje': "Usuario a iniciado sesion satisfatoriamente",'mensaje2': 'La persona se ha creado correctamente y se ha autenticado.', 'usuario': usuario,})

@app.route('/productos', methods=['POST'])
def crear_producto():
    if 'usuario_id' in session:
        nombre = request.json['nombre']
        valor = request.json['valor']
        cantidad = request.json['cantidad']

        if not nombre or not valor or not cantidad:
            return jsonify({'mensaje': 'Por favor ingrese todos los datos requeridos.'}), 400
        
        cursor = conexion.connection.cursor()
        cursor.execute('SELECT * FROM productos WHERE nombre = %s', (nombre,))
        producto_exitse = cursor.fetchone()
        cursor.close()
        if producto_exitse:
            return jsonify({'mensaje': 'Ya hay un producto creado con ese nombre.'}), 409

        
        cursor = conexion.connection.cursor()
        cursor.execute('INSERT INTO productos (nombre, valor, cantidad) VALUES (%s, %s, %s)', (nombre, valor, cantidad))
        conexion.connection.commit()
        cursor.close()

        return jsonify({'mensaje': 'Producto creado exitosamente'}),201
    else:
        return jsonify({'mensaje': 'No tiene una sesión iniciada.'}), 400
    
@app.route('/productos', methods=['GET'])
def leer_productos():
    if 'usuario_id' in session:
        cursor = conexion.connection.cursor()
        cursor.execute('SELECT * FROM productos where estado = 1')
        productos=cursor.fetchall()

        productos_list = []
        for row in productos:
            cursos = {
                
                'id': row[0],
                'nombre': row[1],
                'valor': row[2],
                'cantidad': row[3],
                'estado': row[4],
            }
            productos_list.append(cursos)

        return jsonify(productos_list)
    else:
        return jsonify({'mensaje': 'No tiene una sesión iniciada.'}), 400
    


@app.route('/productos/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    if 'usuario_id' in session:
        valores = []
        consulta = 'UPDATE productos SET '
        if 'nombre' in request.json:
            nombre = request.json.get('nombre')
            consulta += 'nombre=%s, '
            valores.append(nombre)
        if 'valor' in request.json:
            print("entre")
            valor = request.json.get('valor')
            consulta += 'valor=%s, '
            valores.append(valor)
        if 'cantidad' in request.json:
            cantidad = request.json.get('cantidad')
            consulta += 'cantidad=%s, '
            valores.append(cantidad)

        cur = conexion.connection.cursor()
        cur.execute("SELECT * FROM productos WHERE id=%s", (id,))
        producto = cur.fetchone()
        cur.close()

        if not producto:
            return jsonify({'status': 'error', 'message': f'El produto con el {id} no existe'}), 401

            
        consulta = consulta[:-2] + ' WHERE id=%s'
        valores.append(id)

        cur = conexion.connection.cursor()
        cur.execute(consulta, valores)
        conexion.connection.commit()
        cur.close()

        mensaje = f'El producto con el id {id} ha sido actualizado exitosamente'
        return jsonify({'status': 'success', 'message': mensaje}), 200
    else:
        return jsonify({'mensaje': 'No tiene una sesión iniciada.'}), 400



@app.route('/productos_eliminar/<int:id>', methods=['PUT'])
def borrar_producto(id):
    if 'usuario_id' in session:
    
        cursor = conexion.connection.cursor()
        cursor.execute('UPDATE productos SET estado = %s WHERE id = %s', ('0', id))
        conexion.connection.commit()
        cursor.close()
        return jsonify({'mensaje': 'Producto eliminado exitosamente'})
    else:
        return jsonify({'mensaje': 'No tiene una sesión iniciada.'}), 400


@app.route('/login', methods=['POST'])
def login():
    correo = request.json.get('correo')
    contrasena = request.json.get('contrasena')

    if not correo or not contrasena:
        return jsonify({'mensaje': 'Por favor ingrese todos los datos requeridos.'}), 400

    cursor = conexion.connection.cursor()
    cursor.execute('SELECT * FROM usuario WHERE correo = %s', (correo,))
    usuario = cursor.fetchone()
    cursor.close()
    if not usuario:
        return jsonify({'mensaje': 'Credenciales incorrectas.'}), 401

    if not check_password_hash(usuario[2], contrasena):
        return jsonify({'mensaje': 'Credenciales incorrectas.'}), 401

    if 'usuario_id' in session:
        return jsonify({'mensaje': 'Ya tiene una sesión iniciada.'}), 400


    session['usuario_id'] = str(usuario[0])
    return jsonify({'mensaje': "Usuario a iniciado sesion satisfatoriamente"})

@app.route('/logout', methods=['POST'])
def logout():
    if 'usuario_id' not in session:
        return jsonify({'mensaje': 'No tiene una sesión iniciada.'}), 400

    session.pop('usuario_id', None)

    return jsonify({'mensaje': 'Sesión cerrada correctamente.'})

@app.route('/compras', methods=['POST'])
def crear_compras():
    if 'usuario_id' in session:

        if not request.json:
            return jsonify({'error': 'Los datos enviados no son válidos'})
        
        datos_compra = {
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'cantidad': request.json.get('cantidad', ''),
            'id_producto': request.json.get('id_producto'),
            'id_persona': request.json.get('id_persona')
        }

        cursor = conexion.connection.cursor()
        cursor.execute('SELECT cantidad,valor FROM productos WHERE id = %s',(datos_compra['id_producto']))
        producto = cursor.fetchone()

        if int(producto[0]) < int(datos_compra['cantidad']):
            return jsonify({'error': 'No hay suficiente stock disponible para realizar la compra'}), 400
        
        nueva_cantidad = int(producto[0])-int(datos_compra['cantidad'])
        cursor.execute('UPDATE productos SET cantidad = %s WHERE id = %s',(nueva_cantidad,datos_compra['id_producto']))
        conexion.connection.commit()

        total = int(producto[1]) * int(datos_compra['cantidad'])
        print(producto[1])
        print(total)
        datos_compra['total'] = total

        cursor.execute('INSERT INTO compras (fecha, cantidad, total, id_producto, id_persona) VALUES (CURDATE(), %s, %s, %s, %s)', (datos_compra['cantidad'], total, datos_compra['id_producto'], datos_compra['id_persona']))
        conexion.connection.commit()
        cursor.close()

        return jsonify({'mensaje': 'Compra realizada exitosamente'}), 200
    else:
        return jsonify({'mensaje': 'No tiene una sesión iniciada.'}), 400


@app.route('/compras', methods=['GET'])
def listar_compras():
    if 'usuario_id' in session:

        cur = conexion.connection.cursor()
        cur.execute('SELECT c.id, c.fecha, p.nombrecompleto AS persona, c.total AS total FROM compras c INNER JOIN persona p ON c.id_persona = p.id INNER JOIN productos pr ON  pr.id = c.id_producto')
        compras = cur.fetchall()
        cur.close()
        compras_list = []
        for row in compras:
            cursos = {
                
                'id_compra': row[0],
                'fecha_compra': row[1],
                'nombre_completo_comprador': row[2],
                'total_compra': row[3],
            }
            compras_list.append(cursos)

        return jsonify(compras_list)
        return jsonify(compras)
    else:
        return jsonify({'mensaje': 'No tiene una sesión iniciada.'}), 400

    
def page_not_found(error):
    return "<h1>La pagina no existe</h1>"

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(404,page_not_found)
    app.run(debug=True)
