# 🤖 Agente IA para Búsqueda de Empleo

Este proyecto es un **Agente de IA** en **Python** que realiza **scraping** de un portal de convocatorias laborales, filtra vacantes para **Ingenieros de Sistemas** y evalúa automáticamente la compatibilidad con un **CV** usando **Google Gemini**.

## ✨ Características
- 🔍 Scraping de convocatorias de empleo.  
- 📊 Filtrado según sueldo y vigencia.  
- 📄 Lectura automática de CV en PDF o TXT.  
- 🤖 Evaluación del match con el CV mediante Gemini.  
- 💾 Exporta resultados a `convocatorias_filtradas.json`.  

## 🛠️ Tecnologías utilizadas
- Python 3  
- BeautifulSoup4  
- Requests  
- LangChain + Gemini  
- PyPDF2  
- python-dotenv  

## 🚀 Cómo usarlo

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/jhodasoft/agente-ia-empleo.git
   cd agente-ia-empleo
   ```

2. **Crear y activar un entorno virtual** (opcional, pero recomendado)
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   source venv/bin/activate   # Linux/Mac
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   - Copiar el archivo de ejemplo:
     ```bash
     cp .env.example .env
     ```
   - Editar `.env` y agregar tu API Key de Google Gemini:
     ```dotenv
     GOOGLE_API_KEY=tu_api_key
     ```

5. **Ejecutar el proyecto**
   ```bash
   python agenteia.py
   ```

## 📹 Demo
👉 [Video de demostración en youtube](https://youtu.be/wn8dWrscgtI)


## 👨‍💻 Autor
Desarrollado con ❤️ por [Jhonny Dante](https://www.linkedin.com/in/jhodasoft/)

