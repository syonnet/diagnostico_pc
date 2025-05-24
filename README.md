# 💻 Sistema de Gestión de Diagnósticos de PC

✨ ¡Bienvenido al Sistema de Gestión de Diagnósticos de PC! ✨

Este proyecto es una aplicación web sencilla desarrollada con Flask que te permite llevar un registro detallado de los diagnósticos técnicos realizados a equipos de computación. Podrás almacenar información del cliente, detalles del equipo, el problema reportado, el diagnóstico inicial, la solución aplicada y generar informes profesionales en formato PDF.

## 🚀 Características Principales

*   **Gestión de Clientes:** 🧑‍💻 Registra y consulta la información de tus clientes.
*   **Registro de Equipos:** 🖥️ Detalla las especificaciones y componentes de los equipos recibidos.
*   **Seguimiento de Diagnósticos:** 🔍 Documenta el problema, diagnóstico y solución para cada equipo.
*   **Generación de PDF:** 📄 Crea informes de diagnóstico listos para imprimir o compartir.

## ✅ Requisitos del Sistema

Asegúrate de tener instalado lo siguiente:

*   **Python 13 o superior:** El lenguaje de programación principal.
*   **pip:** El gestor de paquetes de Python (generalmente viene incluido con Python).

## ⚙️ Primeros Pasos: Configuración e Instalación

Sigue estos sencillos pasos para poner en marcha el proyecto en tu máquina local:

1.  **Clona el Repositorio:** Descarga el código fuente desde GitHub.
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd diagnostico_pc
    ```
    *(Reemplaza `<URL_DEL_REPOSITORIO>` con la URL real de tu repositorio)*

2.  **Crea un Entorno Virtual (¡Recomendado!):** Esto aísla las dependencias del proyecto de otras instalaciones de Python en tu sistema.
    ```bash
    python -m venv venv
    ```

3.  **Activa el Entorno Virtual:**
    *   **En Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **En macOS y Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Instala las Dependencias:** Instala todas las bibliotecas necesarias listadas en `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ ¡Manos a la Obra! Uso de la Aplicación

Una vez configurado, puedes iniciar la aplicación:

1.  **Ejecuta el Archivo Principal:**
    ```bash
    python app.py
    ```
    Verás un mensaje en la terminal indicando que el servidor web ha iniciado.

2.  **Accede a la Aplicación:** Abre tu navegador web favorito y visita la siguiente dirección:
    ```
    http://127.0.0.1:5000/
    ```
    ¡Ya puedes empezar a usar el sistema! 🎉

## 📂 Estructura del Proyecto (Un Vistazo Rápido)

Aquí te presento los archivos y directorios más importantes:

*   `app.py`: El corazón de la aplicación Flask, maneja las rutas y la lógica principal.
*   `database.py`: Contiene el código para inicializar la base de datos SQLite (`database.db`).
*   `database.db`: El archivo de la base de datos donde se almacenan todos los datos (clientes, diagnósticos, etc.). Se crea automáticamente si no existe al ejecutar `database.py` o `app.py` por primera vez.
*   `pdf_generator.py`: El script encargado de tomar los datos de un diagnóstico y generar el informe en formato PDF.
*   `requirements.txt`: Lista todas las bibliotecas de Python que necesita el proyecto para funcionar.
*   `static/`: Aquí se guardan los archivos estáticos como hojas de estilo CSS (`static/css/style.css`).
*   `templates/`: Contiene los archivos HTML que definen la interfaz de usuario de la aplicación.
*   `venv/`: El directorio del entorno virtual (si lo creaste).

## 🤝 ¿Quieres Contribuir?

¡Tu ayuda es bienvenida! Si encuentras errores, tienes sugerencias o quieres añadir nuevas funcionalidades, no dudes en:

1.  Abrir un **Issue** describiendo el problema o la idea.
2.  Enviar un **Pull Request** con tus cambios propuestos.

## Licencia

Este proyecto es propiedad de Syon Net y se distribuye bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles (si existe en el repositorio).