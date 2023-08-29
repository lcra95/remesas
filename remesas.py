from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import sys
import os
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import func, and_
app = Flask(__name__)
CORS(app)
# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://lrequena:18594LCra..@170.239.85.238/delivery'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Transaccion(db.Model):
    __tablename__ = 'transacciones_criptodivisas'

    id = db.Column(db.Integer, primary_key=True)
    fecha_registro = db.Column(
        db.DateTime, default=db.func.current_timestamp())
    nombre_cliente = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    tipo_transaccion = db.Column(
        db.String(10), nullable=False)  # "Compra" o "Venta"
    Tipo_pago = db.Column(db.String(10), nullable=False)  # "Compra" o "Venta"
    estado = db.Column(db.String(10), nullable=False)  # "Compra" o "Venta"


@app.route('/transacciones', methods=['POST'])
def agregar_transaccion():
    try:
        data = request.json

        nueva_transaccion = Transaccion(
            nombre_cliente=data['nombre_cliente'],
            monto=data['monto'],
            tipo_transaccion=data['tipo_transaccion'],
            Tipo_pago=data['Tipo_pago'],
            estado=data['estado'],

        )

        db.session.add(nueva_transaccion)
        db.session.commit()

        return jsonify({"message": "Transacción agregada con éxito", "transaccion": nueva_transaccion.id}), 201
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        msj = 'Error: ' + str(exc_obj) + ' File: ' + \
            fname + ' linea: ' + str(exc_tb.tb_lineno)
        return {"message": msj}, 500


@app.route('/transacciones', methods=['GET'])
def obtener_transacciones():
    query = Transaccion.query.order_by(Transaccion.fecha_registro.desc())

    # Filtro por estado
    estado = request.args.get('estado')
    if estado:
        query = query.filter(Transaccion.estado == estado)

    # Filtro por tipo_pago
    tipo_pago = request.args.get('tipo_pago')
    if tipo_pago:
        query = query.filter(Transaccion.Tipo_pago == tipo_pago)

    # Filtro por fecha exacta
    fecha = request.args.get('fecha')
    if fecha:
        try:
            fecha_parsed = datetime.strptime(fecha, '%Y-%m-%d').date()
            query = query.filter(Transaccion.fecha_registro == fecha_parsed)
        except ValueError:
            return jsonify({"error": "Formato de fecha incorrecto. Use YYYY-MM-DD."}), 400

    # Filtro por intervalo de tiempo
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio_parsed = datetime.strptime(
                fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_parsed = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            query = query.filter(Transaccion.fecha_registro.between(
                fecha_inicio_parsed, fecha_fin_parsed))
        except ValueError:
            return jsonify({"error": "Formato de fecha incorrecto. Use YYYY-MM-DD."}), 400

    transacciones = query.all()
    return jsonify({"data": [{
        'id': t.id,
        'Fecha': t.fecha_registro.strftime('%d-%m-%Y'),
        'Cliente': t.nombre_cliente,
        'Monto': "{:,.0f}".format(t.monto).replace(",", "X").replace(".", ",").replace("X", "."),
        'Transaccion': t.tipo_transaccion,
        'Tipo pago': t.Tipo_pago,
        'Estado': t.estado
    } for t in transacciones]})


@app.route('/ganancias_semanales', methods=['GET'])
def ganancias_semanales():
    today = datetime.now().date()  # Obtiene la fecha actual sin la hora
    # Combina la fecha con la hora 00:00:00
    start_date = datetime.combine(today, datetime.min.time())
    end_date = start_date + timedelta(days=7)

    compras = Transaccion.query.filter_by(tipo_transaccion="Compra").filter(
        Transaccion.fecha_registro.between(start_date, end_date)).all()
    ventas = Transaccion.query.filter_by(tipo_transaccion="Venta").filter(
        Transaccion.fecha_registro.between(start_date, end_date)).all()

    total_compras = sum([trans.monto for trans in compras])
    total_ventas = sum([trans.monto for trans in ventas])

    diferencia = total_ventas - total_compras

    return jsonify({
        "total_compras": total_compras,
        "total_ventas": total_ventas,
        "diferencia": diferencia
    })


@app.route('/editar_estado/<int:transaccion_id>', methods=['PUT'])
def editar_estado(transaccion_id):
    transaccion = Transaccion.query.get(transaccion_id)

    if not transaccion:
        return jsonify({"error": "Transacción no encontrada"}), 404

    if transaccion.estado != "Pendiente":
        return jsonify({"error": "La transacción ya está en estado 'Pagado' o no es editable"}), 400

    transaccion.estado = "Pagado"
    db.session.commit()

    return jsonify({"message": "Estado actualizado con éxito"})


@app.route('/dashboard/metrics', methods=['GET'])
def dashboard_metrics():
    # Obtener parámetros de la solicitud
    estado = request.args.get('estado')
    tipo_pago = request.args.get('tipo_pago')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    # Crear una consulta base para transacciones
    query = db.session.query(Transaccion)

    # Aplicar filtros basados en los parámetros recibidos
    if estado:
        query = query.filter(Transaccion.estado == estado)

    if tipo_pago:
        query = query.filter(Transaccion.Tipo_pago == tipo_pago)

    if fecha_inicio and fecha_fin:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d")
        query = query.filter(and_(Transaccion.fecha_registro >=
                             start_date, Transaccion.fecha_registro <= end_date))
    elif fecha_inicio:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        query = query.filter(Transaccion.fecha_registro >= start_date)
    elif fecha_fin:
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d")
        query = query.filter(Transaccion.fecha_registro <= end_date)

    # Calcular métricas
    total_ventas = query.filter(Transaccion.tipo_transaccion == "Venta").with_entities(
        func.sum(Transaccion.monto)).scalar() or 0
    total_compras = query.filter(Transaccion.tipo_transaccion == "Compra").with_entities(
        func.sum(Transaccion.monto)).scalar() or 0
    total_transacciones = query.filter(
        Transaccion.tipo_transaccion == "Venta").count()

    # Contar transacciones en estado "Pendiente"
    pendientes = query.filter(Transaccion.estado == "Pendiente").count()

    # Monto y porcentaje por tipo de pago (solo para ventas)
    tipo_pago_ventas_query = db.session.query(
        Transaccion.Tipo_pago,
        func.sum(Transaccion.monto).label('total_monto'),
        (func.sum(Transaccion.monto) / total_ventas *
         100 if total_ventas != 0 else 0).label('porcentaje')
    ).filter(Transaccion.tipo_transaccion == "Venta").group_by(Transaccion.Tipo_pago)

    tipo_pago_data = tipo_pago_ventas_query.all()

    # Porcentaje de ganancias (asumimos ganancia = ventas - compras)
    porcentaje_ganancias = 0 if (
        total_ventas + total_compras) == 0 else (total_ventas - total_compras) * 100 / total_ventas

    return jsonify({
        "monto_por_tipo_pago": [{"tipo_pago": data[0], "monto": round(float(data[1])), "porcentaje": round(float(data[2]))} for data in tipo_pago_data],
        "monto_total_ventas": total_ventas,
        "monto_total_compras": total_compras,
        "porcentaje_ganancias": porcentaje_ganancias,
        "total_transacciones": total_transacciones,
        "transacciones_pendientes": pendientes
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9292, debug=True)
