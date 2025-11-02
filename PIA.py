import datetime as dt
from tabulate import tabulate 
import json
import csv
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
import sys
import sqlite3
from sqlite3 import Error
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

fecha_hoy = dt.date.today()
fecha_hoy = fecha_hoy.strftime("%m/%d/%Y")
fecha_hoy = dt.datetime.strptime(fecha_hoy, "%m/%d/%Y").date()
try:
    with sqlite3.connect("Eventos.db") as conn:
        mi_cursor = conn.cursor()
        mi_cursor.execute("CREATE TABLE IF NOT EXISTS CLIENTES (ID_CLIENTE INTEGER PRIMARY KEY, NOMBRE TEXT NOT NULL, APELLIDO TEXT NOT NULL);")
        mi_cursor.execute("CREATE TABLE IF NOT EXISTS SALAS (ID_SALA INTEGER PRIMARY KEY, NOMBRE TEXT NOT NULL, CAPACIDAD INTEGER NOT NULL);")
        print("Se comenzo desde un estado vacio")
        mi_cursor.execute("CREATE TABLE IF NOT EXISTS EVENTOS (ID_EVENTO INTEGER PRIMARY KEY, ID_SALA INTEGER, ID_CLIENTE INTEGER, NOMBRE_EVENTO TEXT NOT NULL, TURNO TEXT NOT NULL, FECHA timestamp, DISPONIBILIDAD INTEGER NOT NULL, FOREIGN KEY (ID_SALA) REFERENCES SALAS(ID_SALA), FOREIGN KEY (ID_CLIENTE) REFERENCES CLIENTES(ID_CLIENTE));")
except Error as e:
    print (e)
except:
    print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")

print("*"*70)
print("\t***Bienvenido al sistema de reservacion de eventos***")
print("*"*70)

while True:
    print("\n===============Menu===============")
    print("1.Registrar evento")
    print("2.Editar nombre del evento")
    print("3.Consultar reservaciones")
    print("4.Cancelar evento")
    print("5.Registrar cliente")
    print("6.Registrar sala")
    print("7.Salir")
    print("="*34)
    
    try:
        opcion = int(input("Ingrese una opcion: "))
    except ValueError:
        print("Favor de digitar un numero valido\n")
        continue
    
    match opcion:
        case 1:
            print("\n===============Registrar evento===============\n")
            try:
                with sqlite3.connect("Eventos.db") as conn:
                    mi_cursor = conn.cursor()
                    mi_cursor.execute("SELECT COUNT(*) FROM CLIENTES")
                    registros = mi_cursor.fetchall()
                    if registros[0][0] == 0:
                        print("Favor de registrar un cliente previamente para poder registrar un evento\n")
                        continue
                    mi_cursor.execute("SELECT COUNT(*) FROM SALAS")
                    registros = mi_cursor.fetchall()
                    if registros[0][0] == 0:
                        print("Favor de registrar una sala previamente para poder registrar un evento\n")
                        continue
            except Error as e:
                print (e)
            except:
                print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                        
            lista_clientes = []
            claves_clientes_validas = []
            
            try:
                with sqlite3.connect("Eventos.db") as conn:
                    mi_cursor = conn.cursor()
                    mi_cursor.execute("SELECT ID_CLIENTE, APELLIDO, NOMBRE FROM CLIENTES ORDER BY APELLIDO, NOMBRE")
                    lista_clientes = mi_cursor.fetchall()
                    claves_clientes_validas = [cliente[0] for cliente in lista_clientes]
            except Error as e:
                print (e)
            except:
                print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                    
            while True:
                print("\n***************Clientes registrados***************")
                encabezados_clientes = ["ID Cliente", "Apellidos", "Nombre(s)"]
                print(tabulate(lista_clientes, headers=encabezados_clientes, tablefmt="fancy_grid", stralign="center", numalign="center"))
                
                try:
                    clave_cliente_elegida = int(input("Ingresa tu clave de cliente: "))                  
                    if clave_cliente_elegida not in claves_clientes_validas:
                        print("El cliente no existe\n")
                        salida = input("Escriba X si quiere regresar al menu principal, si no digita cualquier otro caracter: ")
                        if salida.upper() == "X":
                            break
                        continue
                except ValueError:
                    print("Favor de digitar un numero valido\n")
                    continue
                
                while True:     
                    fecha_elegida = input("\nIngrese la fecha del evento (mm/dd/aaaa): ")
                    try:
                        fecha_evento = dt.datetime.strptime(fecha_elegida, "%m/%d/%Y").date()
                    except ValueError:
                        print("Favor de digitar una fecha valida\n")
                        continue
                    if (fecha_evento - fecha_hoy).days <= 2:
                        print(f"La fecha debe ser, por lo menos, dos días posteriores a la fecha actual\n")
                        continue

                    if fecha_evento.weekday() == 6: 
                        lunes_siguiente = fecha_evento + dt.timedelta(days=1)                      
                        print(f"No se pueden realizar reservaciones para los dias domingo")
                        
                        opcion_domingo = input(f"Se propone reservar para el lunes siguiente ({lunes_siguiente.strftime('%m/%d/%Y')}), colocar S para aceptar: ")                            
                        if opcion_domingo.upper() == "S":
                            fecha_evento = lunes_siguiente
                            break 
                        else:
                            continue
                    break 
                    
                salas_info = {} 
                ids_salas_validas = []
                valor = (fecha_evento,) 
                
                try:
                    with sqlite3.connect("Eventos.db") as conn:
                        mi_cursor = conn.cursor()
                        mi_cursor.execute("SELECT ID_SALA, NOMBRE, CAPACIDAD FROM SALAS")
                        lista_salas_data = mi_cursor.fetchall() 
                        mi_cursor.execute("SELECT ID_SALA, TURNO FROM EVENTOS WHERE DATE(FECHA) = ? AND DISPONIBILIDAD = 1", valor)
                        eventos_en_fecha = mi_cursor.fetchall()
                except Error as e:
                    print(e)
                except:
                    print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                    
                turnos_ocupados_por_sala = {}

                for sala_id, turno_ocupado in eventos_en_fecha:
                    if sala_id in turnos_ocupados_por_sala:
                        turnos_ocupados_por_sala[sala_id].append(turno_ocupado)
                    else:
                        turnos_ocupados_por_sala[sala_id] = [turno_ocupado]
                
                salas_info = {sala[0]: [sala[1], sala[2]] for sala in lista_salas_data}
                ids_salas_validas = list(salas_info.keys())

                turnos_validos = ["MATUTINO", "VESPERTINO", "NOCTURNO"]
                salas_turnos_disponibles = {} 
                filas_tabla_salas = []

                for sala_id, (nombre_sala, capacidad) in salas_info.items():
                    turnos_ocupados = turnos_ocupados_por_sala.get(sala_id, [])              
                    turnos_disponibles = [turno for turno in turnos_validos if turno not in turnos_ocupados]
                    salas_turnos_disponibles[sala_id] = [capacidad, turnos_disponibles] 
                    turnos = ', '.join(turnos_disponibles) if turnos_disponibles else "--- NINGUNO ---"
                    filas_tabla_salas.append([sala_id, nombre_sala, capacidad, turnos])

                print(f"\n\t*****Salas disponibles para la fecha {fecha_evento.strftime('%m/%d/%Y')}*****")
                filas_tabla_salas = []
                for sala_id, info in salas_turnos_disponibles.items():
                    nombre_sala = salas_info[sala_id][0]
                    capacidad = info[0]
                    turnos_str = ', '.join(info[1]) if info[1] else "--- NINGUNO ---"
                    filas_tabla_salas.append([sala_id, nombre_sala, capacidad, turnos_str])
                
                headers = ["Sala ID","Nombre Sala", "Cupo","Turnos Disponibles"]
                tabla = tabulate(filas_tabla_salas, headers, tablefmt="fancy_grid", stralign="center", numalign="center")
                print(tabla)
                
                while True:
                    try:
                        sala_elegida = int(input("Ingrese el ID de la sala: "))
                    except:
                        print("Favor de digitar un numero valido\n")
                        continue  
                    if sala_elegida not in ids_salas_validas:
                        print("La sala no existe\n")
                        continue
                    break 

                while True:
                    turno_elegido = input("Ingrese el turno a elegir: ").upper()
                    if turno_elegido not in turnos_validos:
                        print("Turno no valido \n")
                        continue
                    salida = ""
                    if turno_elegido not in salas_turnos_disponibles[sala_elegida][1]:
                        print("Este turno ya está ocupado para la sala y fecha seleccionadas. Por favor, elija otro turno\n")
                        salida = input("Escriba X si quiere regresar al menu principal, si no digita cualquier otro caracter: ")
                        if salida.upper() == "X":
                            break
                        continue
                    break
                if salida.upper() == "X":
                    break
                
                while True:
                    nombre_evento = input("Ingrese el nombre del evento: ")
                    if not nombre_evento:
                        print("El nombre del evento no puede estar vacio\n") 
                        continue
                    if nombre_evento.isspace():
                        print("El nombre del evento no puede consistir solo en espacios en blanco\n")
                        continue
                    if nombre_evento.isdigit():
                        print("El nombre del evento no puede ser un numero\n")
                        continue
                    break 
                
                valores = (sala_elegida, clave_cliente_elegida, nombre_evento.upper(), turno_elegido.upper(), fecha_evento, 1)

                try:
                    with sqlite3.connect("Eventos.db") as conn:
                        mi_cursor = conn.cursor()
                        mi_cursor.execute("INSERT INTO EVENTOS (ID_SALA, ID_CLIENTE, NOMBRE_EVENTO, TURNO, FECHA, DISPONIBILIDAD) VALUES (?, ?, ?, ?, ?,?)", valores)
                        mi_cursor.execute("PRAGMA foreign_keys = 1")
                        print("\n***Evento registrado con exito***")
                except Error as e:
                    print (e)
                except:
                    print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                break 
        
        case 2:
            print("\n===============Editar nombre del evento===============\n")
            
            while True:
                fecha_inicio = input("Ingrese desde que fecha consultar los eventos (mm/dd/aaaa): ")
                try:
                    fecha_inicio = dt.datetime.strptime(fecha_inicio, "%m/%d/%Y").date()
                    fecha_inicio_iso = fecha_inicio.isoformat()
                    break
                except ValueError:
                    print("Favor de digitar una fecha valida\n")
                    continue

            while True:
                fecha_fin = input("Ingrese hasta que fecha consultar los eventos (mm/dd/aaaa): ")
                try:
                    fecha_fin = dt.datetime.strptime(fecha_fin, "%m/%d/%Y").date()
                    if fecha_fin < fecha_inicio:
                        print("La fecha final no puede ser menor a la fecha inicial\n")
                        continue
                    fecha_fin_iso = fecha_fin.isoformat()
                    break
                except ValueError:
                    print("Favor de digitar una fecha valida\n")
                    continue

            eventos_en_rango = []
            folios_eventos_validos = []
            
            try:
                with sqlite3.connect("Eventos.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as conn:
                    mi_cursor = conn.cursor()
                    consulta = """
                        SELECT E.ID_EVENTO, S.NOMBRE, C.NOMBRE, C.APELLIDO, E.NOMBRE_EVENTO, E.TURNO, strftime('%m/%d/%Y', E.FECHA)
                        FROM EVENTOS AS E INNER JOIN SALAS AS S ON E.ID_SALA = S.ID_SALA
                        INNER JOIN CLIENTES AS C ON E.ID_CLIENTE = C.ID_CLIENTE
                        WHERE DATE(E.FECHA) BETWEEN ? AND ? AND E.DISPONIBILIDAD = 1
                    """
                    valores = (fecha_inicio, fecha_fin)
                    mi_cursor.execute(consulta, valores)
                    eventos_en_rango = mi_cursor.fetchall() 
                    folios_eventos_validos = [evento[0] for evento in eventos_en_rango]
            except Error as e:
                print(f"Error de base de datos al consultar eventos: {e}")
                continue
            except:
                print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                continue

            if not eventos_en_rango:
                print(f"\nNo hay eventos registrados entre {fecha_inicio} y {fecha_fin}\n")
                continue
            else:
                print(f"\n\t**********Eventos registrados entre {fecha_inicio} y {fecha_fin}**********")
                
                filas_tabla_eventos = []
                for evento in eventos_en_rango:
                    folio = evento[0]
                    nombre_sala = evento[1]
                    nombre_cliente = f"{evento[2]} {evento[3]}"
                    nombre_evento = evento[4]
                    turno_evento = evento[5]
                    fecha_evento = evento[6]
                    
                    filas_tabla_eventos.append([folio, nombre_sala, nombre_cliente, nombre_evento, turno_evento, fecha_evento])
                
                headers = ["Folio del evento", "Sala", "Cliente", "Evento", "Turno", "Fecha"]
                tabla = tabulate(filas_tabla_eventos, headers, tablefmt="fancy_grid", stralign="center", numalign="center")
                print(tabla)

            while True:
                try:
                    folio_evento_elegido = int(input("Ingrese el folio del evento a editar: "))
                    if folio_evento_elegido not in folios_eventos_validos:
                        print("Elegir folio de evento dentro de las opciones mostradas\n")
                        print(tabla)
                        continue
                    break
                except ValueError:
                    print("Favor de digitar un numero valido\n")
                    continue
                    
            while True:
                nuevo_nombre_evento = input("Ingrese el nuevo nombre del evento: ")
                if not nuevo_nombre_evento:
                    print("El nombre del evento no puede estar vacio\n")
                    continue
                if nuevo_nombre_evento.isspace():
                    print("El nombre del evento no puede consistir solo en espacios en blanco\n")
                    continue
                if nuevo_nombre_evento.isdigit():
                    print("El nombre del evento no puede ser un numero\n")
                    continue
                nuevo_nombre = nuevo_nombre_evento.upper()
                valores = (nuevo_nombre, folio_evento_elegido)
                
                try:
                    with sqlite3.connect("Eventos.db") as conn:
                        mi_cursor = conn.cursor()
                        mi_cursor.execute("UPDATE EVENTOS SET NOMBRE_EVENTO = ? WHERE ID_EVENTO = ?", valores)
                        print("***Nombre del evento editado con exito***")
                        break
                except Error as e:
                    print(f"Error de base de datos al actualizar el evento: {e}")
                    break
                except:
                    print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                    break
                