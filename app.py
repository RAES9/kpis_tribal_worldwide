import streamlit as st
from auth.discord_auth import get_user_info, get_access_token, client_id, redirect_uri
from auth.firebase_auth import verify_user
from firebase_admin import db
import pandas as pd
from io import BytesIO
import openpyxl

st.set_page_config(page_title="KPIs", layout="wide")


def plot_kpis_by_month_st(dataframe, month, kpi_columns):
    month_data = dataframe[dataframe['Mes'] == month]
    month_data = month_data.set_index('Nombre')[kpi_columns]
    st.bar_chart(month_data)
    return month_data


# Diccionario de mapeo para nombres descriptivos
nombres_descriptivos = {
    "KPI_1": "Tareas Completadas",
    "KPI_2": "Errores en el Código",
    "KPI_3": "Tiempos en Clockify",
    "KPI_4": "Educación",
    "KPI_SS_1": "Actitud de Servicio",
    "KPI_SS_2": "Trabajo en Equipo",
    "KPI_SS_3": "Búsqueda de Excelencia",
    "KPI_SS_4": "Pasión por el Desempeño",
    "KPI_SS_5": "Excelencia"
}

# Mapeo de claves a nombres amigables para responsabilidades y valores
kpi_names_mapping = {
    "KPI_1": "Tareas completadas",
    "KPI_2": "Errores de código",
    "KPI_3": "Tiempos en Clockify",
    "KPI_4": "Educación",
    "KPI_SS_1": "Actitud de servicio",
    "KPI_SS_2": "Trabajo en equipo",
    "KPI_SS_3": "Búsqueda de excelencia",
    "KPI_SS_4": "Pasión por el desempeño",
    "KPI_SS_5": "Excelencia"
}


def plot_kpis_by_month_st(dataframe, month, kpi_columns, kpi_names_mapping):
    month_data = dataframe[dataframe['Mes'] == month]

    # Aquí se utiliza kpi_columns (que son las claves originales) para seleccionar los datos
    month_data = month_data.set_index('Nombre')[kpi_columns]

    # Renombrar las columnas utilizando el mapeo de nombres amigables
    month_data = month_data.rename(columns=kpi_names_mapping)

    st.bar_chart(month_data)
    return month_data

# Invertir el diccionario para mapear desde el nombre descriptivo a la clave interna
nombres_inverso = {v: k for k, v in nombres_descriptivos.items()}


# Función para seleccionar un KPI para comparar, mostrando nombres amigables
def seleccionar_kpi_para_comparar():
    # Mostrar los nombres descriptivos en el selectbox
    selected_kpi_name = st.sidebar.selectbox(
        'Selecciona un KPI para comparar',
        list(nombres_descriptivos.values())
    )

    # Convertir el nombre amigable seleccionado a la clave interna (por ejemplo, de 'Tareas Completadas' a 'KPI_1')
    kpi_clave_interna = nombres_inverso[selected_kpi_name]

    return kpi_clave_interna


# Función para mostrar promedios usando los nombres descriptivos
def display_averages(dataframe, kpi_columns_responsibilities, kpi_columns_values):
    average_kpis_responsibilities = dataframe.groupby('Nombre')[kpi_columns_responsibilities].mean()
    average_kpis_values = dataframe.groupby('Nombre')[kpi_columns_values].mean()

    overall_average_kpis_responsibilities = average_kpis_responsibilities.mean()
    overall_average_kpis_values = average_kpis_values.mean()

    st.subheader("Resumen de Promedios Generales")
    col1, col2 = st.columns(2)
    with col1:
        for kpi in kpi_columns_responsibilities:
            nombre_descriptivo = nombres_descriptivos.get(kpi, kpi)
            st.metric(label=nombre_descriptivo, value=f"{overall_average_kpis_responsibilities[kpi]:.2f}")
    with col2:
        for kpi in kpi_columns_values:
            nombre_descriptivo = nombres_descriptivos.get(kpi, kpi)
            st.metric(label=nombre_descriptivo, value=f"{overall_average_kpis_values[kpi]:.2f}")

    return average_kpis_responsibilities, average_kpis_values


# Modificar también la selección de KPIs en la comparación para mostrar nombres descriptivos
def plot_kpis_by_person_st(dataframe, name, kpi_columns):
    person_data = dataframe[dataframe['Nombre'] == name]
    person_data['Mes'] = pd.Categorical(person_data['Mes'], categories=[
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
        "Diciembre"], ordered=True)
    person_data = person_data.sort_values('Mes').set_index('Mes')[kpi_columns]

    # Renombrar las columnas usando los nombres descriptivos
    person_data.columns = [nombres_descriptivos.get(col, col) for col in person_data.columns]

    st.line_chart(person_data)
    return person_data


def calcular_promedio(valores):
    return sum(valores) / len(valores)


def obtener_devs():
    ref = db.reference('devs')  # Referencia a 'devs' en Firebase
    devs = ref.get()  # Obtener todos los devs
    if devs:
        nombres_formateados = []
        for dev in devs.keys():
            nombre_formateado = dev.replace("_", " ").title()  # Formatear el nombre
            nombres_formateados.append(nombre_formateado)
        return nombres_formateados
    else:
        return []


def exportar_csv(dataframe):
    output = BytesIO()
    dataframe.to_csv(output, index=False)
    output.seek(0)
    return output


def load_firebase_data():
    ref = db.reference('devs')
    devs = ref.get()

    if devs:
        registros = []
        for dev, meses in devs.items():
            for mes, kpis in meses.items():
                registro = {'Nombre': dev.replace("_", " ").title(), 'Mes': mes}
                registro.update(kpis)
                registros.append(registro)

        df = pd.DataFrame(registros)
        return df
    return None


def guardar_kpis(nombre_empleado, mes, kpis):
    ref = db.reference(f'devs/{nombre_empleado}/{mes}')
    if ref.get() is None:
        ref.set(kpis)
        return True
    return False


def modificar_excel(excel_file, nombre_empleado, puesto, jefe_inmediato, puesto_jefe, fecha,
                    promedio_habilidades_tecnicas,
                    promedio_habilidades_blandas, tareas_completadas, errores_codigo, tiempos_clockify, educacion,
                    actitud_servicio, trabajo_equipo, busqueda_excelencia, pasion_desempeno, excelencia):
    # Cargar el archivo de Excel
    workbook = openpyxl.load_workbook(excel_file)
    sheet = workbook.active

    # Modificar las celdas con los datos proporcionados
    sheet["B5"] = nombre_empleado.replace(" ", "_").lower()
    sheet["B6"] = puesto
    sheet["B7"] = jefe_inmediato
    sheet["B8"] = puesto_jefe

    # Modificar los detalles de habilidades técnicas
    sheet["D13"] = tareas_completadas
    sheet["D14"] = errores_codigo
    sheet["D15"] = tiempos_clockify
    sheet["D16"] = educacion

    # Modificar los detalles de habilidades blandas
    sheet["D21"] = excelencia
    sheet["D22"] = actitud_servicio
    sheet["D23"] = trabajo_equipo
    sheet["D24"] = busqueda_excelencia
    sheet["D25"] = pasion_desempeno

    # Guardar el archivo modificado en BytesIO para descargar
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return output


# Descripciones de los KPIs
descripciones_tecnicas = {
    "tareas_completadas": "Indica la cantidad de tareas completadas dentro de un sprint.",
    "errores_codigo": "Cantidad de errores encontrados por el equipo en el código entregado.",
    "tiempos_clockify": "Tiempos siempre ingresados en Clockify durante el mes.",
    "educacion": "Avance de curso educativo para mantenerse al día en habilidades."
}

descripciones_blandas = {
    "actitud_servicio": "Disposición y actitud para atender necesidades internas y externas.",
    "trabajo_equipo": "Colaboración efectiva en equipo.",
    "busqueda_excelencia": "Compromiso con la mejora continua y la búsqueda de la excelencia.",
    "pasion_desempeno": "Pasión por alcanzar un alto desempeño en todas las tareas.",
    "excelencia": "Mantener la excelencia en el desempeño individual."
}

# Si el token de acceso ya está en session_state, no es necesario volver a autenticar
if 'access_token' not in st.session_state:
    if 'code' in st.query_params:
        code = st.query_params['code']

        if len(code) < 5:
            st.error("El código recibido parece inválido o está truncado.")
            st.stop()

        # Intentar obtener el token de acceso
        token_data = get_access_token(code)

        if 'access_token' in token_data:
            access_token = token_data['access_token']
            st.session_state.access_token = access_token  # Guardar el token en session_state
        else:
            st.error(
                f"Error al obtener el token de acceso: {token_data.get('error_description', 'No se proporcionó una descripción del error')}")
            st.stop()

# Si ya tenemos el token de acceso, proceder con el resto de la lógica
if 'access_token' in st.session_state:
    access_token = st.session_state.access_token
    user_info = get_user_info(access_token)
    user_id = user_info['id']
    user_name = user_info['username']

    if verify_user(user_name):
        st.title("Registro de KPIs Devs iOS")

        st.success(f"Bienvenido, {user_name}")

        # Subir archivo de Excel
        excel_file = st.file_uploader("Sube el archivo Excel con el formato", type=["xlsx"])

        # Obtener lista de devs de Firebase
        lista_devs = obtener_devs()

        if lista_devs:
            # Seleccionar el nombre del empleado desde la lista de devs
            nombre_empleado = st.selectbox("Seleccione el nombre del Empleado", lista_devs).replace(" ", "_").lower()
        else:
            st.error("No se encontraron empleados en Firebase")

        # Puesto
        puesto = st.text_input("Puesto")

        # Selección del mes
        mes = st.selectbox("Seleccione el Mes",
                           ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
                            "Octubre", "Noviembre", "Diciembre"])

        # Nombre del jefe inmediato
        jefe_inmediato = st.text_input("Nombre del Jefe Inmediato")

        # Puesto
        puesto_jefe = st.text_input("Puesto jefe inmediato")

        # Fecha
        fecha = st.date_input("Fecha de evaluación")

        st.subheader("Habilidades Técnicas")
        st.write(descripciones_tecnicas["tareas_completadas"])
        tareas_completadas = st.number_input("Número de tareas completadas por sprint", min_value=0, max_value=100)

        st.write(descripciones_tecnicas["errores_codigo"])
        errores_codigo = st.number_input("Número de errores de código reportados", min_value=0, max_value=100)

        st.write(descripciones_tecnicas["tiempos_clockify"])
        tiempos_clockify = st.number_input("Tiempos ingresados en Clockify (%)", min_value=0, max_value=100)

        st.write(descripciones_tecnicas["educacion"])
        educacion = st.number_input("Puntaje de Educación (Avance de curso educativo)", min_value=0, max_value=100)

        # Calcular promedio de Habilidades Técnicas
        promedio_habilidades_tecnicas = calcular_promedio(
            [tareas_completadas, errores_codigo, tiempos_clockify, educacion])
        st.write(f"Puntaje Promedio de Habilidades Técnicas: {promedio_habilidades_tecnicas:.2f}")

        st.subheader("Habilidades Blandas")
        st.write(descripciones_blandas["actitud_servicio"])
        actitud_servicio = st.number_input("Actitud de servicio", min_value=0, max_value=100)

        st.write(descripciones_blandas["trabajo_equipo"])
        trabajo_equipo = st.number_input("Trabajo en equipo", min_value=0, max_value=100)

        st.write(descripciones_blandas["busqueda_excelencia"])
        busqueda_excelencia = st.number_input("Búsqueda de excelencia", min_value=0, max_value=100)

        st.write(descripciones_blandas["pasion_desempeno"])
        pasion_desempeno = st.number_input("Pasión por el alto desempeño", min_value=0, max_value=100)

        st.write(descripciones_blandas["excelencia"])
        excelencia = st.number_input("Excelencia", min_value=0, max_value=100)

        # Calcular promedio de Habilidades Blandas
        promedio_habilidades_blandas = calcular_promedio(
            [actitud_servicio, trabajo_equipo, busqueda_excelencia, pasion_desempeno, excelencia])
        st.write(f"Puntaje Promedio de Habilidades Blandas: {promedio_habilidades_blandas:.2f}")

        # Guardar KPIs
        if st.button("Guardar KPIs"):
            kpis = {
                "KPI_1": tareas_completadas,
                "KPI_2": errores_codigo,
                "KPI_3": tiempos_clockify,
                "KPI_4": educacion,
                "KPI_SS_1": actitud_servicio,
                "KPI_SS_2": trabajo_equipo,
                "KPI_SS_3": busqueda_excelencia,
                "KPI_SS_4": pasion_desempeno,
                "KPI_SS_5": excelencia
            }

            if guardar_kpis(nombre_empleado, mes, kpis):
                st.success(f"KPIs guardados exitosamente para {nombre_empleado} en {mes}.")
            else:
                st.error(f"Ya existe un registro de KPIs para {nombre_empleado} en {mes}.")

        # Botón para descargar el Excel modificado
        if excel_file and st.button("Modificar Excel"):
            excel_modificado = modificar_excel(
                excel_file, nombre_empleado, puesto, jefe_inmediato, puesto_jefe, fecha,
                promedio_habilidades_tecnicas, promedio_habilidades_blandas,
                tareas_completadas, errores_codigo, tiempos_clockify, educacion,
                actitud_servicio, trabajo_equipo, busqueda_excelencia, pasion_desempeno, excelencia
            )
            st.download_button(label="Descargar Excel", data=excel_modificado,
                               file_name=f"KPI_Report_{nombre_empleado}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.divider()

        st.title('Visualización de KPIs')

        # Definir nombres de KPIs ya establecidos
        kpi_columns_responsibilities = ["KPI_1", "KPI_2", "KPI_3", "KPI_4"]
        kpi_columns_values = ["KPI_SS_1", "KPI_SS_2", "KPI_SS_3", "KPI_SS_4", "KPI_SS_5"]

        # Cargar datos desde Firebase
        df = load_firebase_data()

        if df is not None:
            # Mostrar promedios
            avg_responsibilities, avg_values = display_averages(df, kpi_columns_responsibilities, kpi_columns_values)

            # Filtro por nombre
            st.sidebar.subheader('Filtrar por Nombre')
            selected_name = st.sidebar.selectbox('Selecciona un nombre', df['Nombre'].unique())
            if selected_name:
                st.subheader(f'Histórico KPIs de {selected_name}')
                plot_kpis_by_person_st(df, selected_name, kpi_columns_responsibilities)
                plot_kpis_by_person_st(df, selected_name, kpi_columns_values)

            # Filtro por mes
            st.sidebar.subheader('Filtrar por Mes')
            selected_month = st.sidebar.selectbox('Selecciona un mes', df['Mes'].unique())
            if selected_month:
                st.subheader(f'KPIs del Mes de {selected_month}')

                st.subheader("Responsabilidades")
                plot_kpis_by_month_st(df, selected_month, ["KPI_1", "KPI_2", "KPI_3", "KPI_4"], kpi_names_mapping)

                st.subheader("Valores")
                plot_kpis_by_month_st(df, selected_month, ["KPI_SS_1", "KPI_SS_2", "KPI_SS_3", "KPI_SS_4", "KPI_SS_5"],
                                      kpi_names_mapping)

            # Análisis adicional
            st.sidebar.subheader('Análisis Adicional')
            analysis_option = st.sidebar.selectbox('Selecciona el tipo de análisis',
                                                   ['Comparación entre Personas', 'Tendencias de KPIs'])
            if analysis_option == 'Comparación entre Personas':
                st.subheader('Comparación entre Personas')

                # Usar la función para seleccionar el KPI
                selected_kpi = seleccionar_kpi_para_comparar()

                # Realizar la comparación con la clave interna (selected_kpi)
                comparison_data = df.pivot(index='Mes', columns='Nombre', values=selected_kpi).reset_index()
                comparison_data['Mes'] = pd.Categorical(comparison_data['Mes'], categories=[
                    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
                    "Noviembre", "Diciembre"], ordered=True)
                comparison_data = comparison_data.sort_values('Mes').set_index('Mes')
                st.scatter_chart(comparison_data)
            elif analysis_option == 'Tendencias de KPIs':
                st.subheader('Tendencias de KPIs')

                # Usar la función para seleccionar el KPI, que muestra los nombres amigables
                selected_kpi = seleccionar_kpi_para_comparar()

                # Realizar el análisis de tendencia con la clave interna (selected_kpi)
                trend_data = df.groupby('Mes')[selected_kpi].mean().reset_index()
                trend_data['Mes'] = pd.Categorical(trend_data['Mes'], categories=[
                    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
                    "Noviembre", "Diciembre"], ordered=True)
                trend_data = trend_data.sort_values('Mes').set_index('Mes')
                st.line_chart(trend_data)

            st.header("Exportar KPIs a CSV")
            csv_data = exportar_csv(df)
            st.download_button(label="Descargar CSV", data=csv_data, file_name="kpis_firebase.csv", mime="text/csv")
        else:
            st.error('No se encontraron datos en Firebase.')

    else:
        st.error("No tienes acceso.")
else:
    st.title("Bienvenido al portal de registro de KPIs de Tribal Worldwide (Departamento de desarrollo)")

    login_url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify"

    st.markdown(f"[Haz clic aquí para iniciar sesión con Discord]({login_url})")
