import requests
from bs4 import BeautifulSoup
import json
import re
import os
from dotenv import load_dotenv

# Cargar variables de entorno (.env)
load_dotenv()

# -----------------------
# Configuración segura
# -----------------------
BASE_URL = "https://www.convocatoriasdetrabajo.com/ofertas-de-empleo-en-INGENIERIA-DE-SISTEMAS-18.html"

# Cambia a True solo cuando estés 100% seguro de usar tu cuota.
USE_GEMINI = True

# Límite de llamadas al modelo por ejecución (para evitar gastar cuota por accidente).
# Pon None para no limitar.
MAX_GEMINI_CALLS = 2

# -----------------------
# Funciones originales
# -----------------------
def parse_sueldo(sueldo_text):
    """Convierte el texto de sueldo en número. Devuelve None si no se puede."""
    if not sueldo_text:
        return None
    match = re.findall(r"\d+", sueldo_text.replace(",", ""))
    if not match:
        return None
    try:
        return int("".join(match))
    except:
        return None

def scrape_page(url):
    """Extrae todas las convocatorias de una sola página"""
    resp = requests.get(url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    convocatorias = []
    for article in soup.find_all("article", class_="convocatoria"):
        # Título + enlace principal
        titulo_tag = article.find("h4").find("a") if article.find("h4") else None
        titulo = titulo_tag.get_text(strip=True) if titulo_tag else None
        link = titulo_tag["href"] if titulo_tag else None

        # Requisitos (si existieran)
        requisito_tag = article.find("i", class_="icon-grado")
        requisito = requisito_tag.find_next("span").get_text(strip=True) if requisito_tag else None

        # Lugar, sueldo, fecha
        lugar, sueldo, fecha = None, None, None
        grupo = article.find("li", class_="convocatoria_group")
        if grupo:
            items = grupo.find_all("span")
            if len(items) >= 3:
                lugar, sueldo, fecha = [x.get_text(strip=True) for x in items[:3]]

        # Botón "VER CONVOCATORIA"
        ver_tag = article.find("a", class_="enlace1")
        ver_link = ver_tag["href"] if ver_tag else None

        convocatorias.append({
            "titulo": titulo,
            #"link": link,
            #"requisito": requisito,
            "lugar": lugar,
            #"sueldo": sueldo,
            "sueldo_num": parse_sueldo(sueldo),
            "fecha": fecha,
            "ver_convocatoria": ver_link
        })

    return convocatorias

def scrape_all():
    """Recorre todas las páginas hasta que no encuentre más convocatorias"""
    all_convocatorias = []
    page = 1
    while True:
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}?page={page}&sort=1-fechapublicacion"

        print(f"\n🌍 Scrapeando página {page}: {url}")
        convocatorias = scrape_page(url)

        if not convocatorias:
            print("✅ No hay más convocatorias. Fin del scraping.")
            break

        all_convocatorias.extend(convocatorias)
        page += 1

    return all_convocatorias

# -----------------------
# Lectura segura del CV
# -----------------------
def load_cv_text():
    """
    Intenta leer 'mi_cv.pdf' (si PyPDF2 está disponible) o 'mi_cv.txt'.
    Si no existe ninguno, devuelve string vacío.
    """
    text = ""

    # 1) Intentar PDF
    try:
        import PyPDF2
        if os.path.exists("mi_cv.pdf"):
            with open("mi_cv.pdf", "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    if page.extract_text():
                        text += page.extract_text() + "\n"
    except Exception:
        # Si falla PyPDF2 o no hay PDF, seguimos
        pass

    # 2) Si no hay PDF o quedó vacío, intentar txt
    if not text and os.path.exists("mi_cv.txt"):
        try:
            with open("mi_cv.txt", "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            text = ""

    if not text:
        print("⚠️ No se encontró 'mi_cv.pdf' ni 'mi_cv.txt' o están vacíos. Gemini recibirá CV vacío si lo activas.")

    # Truncar CV si es muy largo (para evitar tokens excesivos)
    MAX_CHARS_CV = 25000
    if len(text) > MAX_CHARS_CV:
        print(f"⚠️ CV muy largo ({len(text)} chars). Se truncará a {MAX_CHARS_CV} chars para evitar exceso de tokens.")
        text = text[:MAX_CHARS_CV]

    return text

# -----------------------
# Integración con Gemini (solo si USE_GEMINI=True)
# -----------------------
def init_gemini():
    """Intenta inicializar la librería y el LLM. Devuelve None si hay fallo."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as e:
        print(f"⚠️ No se pudo importar 'langchain_google_genai': {e}")
        return None

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,
            max_output_tokens=256,
        )
        return llm
    except Exception as e:
        print(f"⚠️ Error al inicializar Gemini: {e}")
        return None

def evaluar_con_gemini(llm, convocatoria_text, cv_text):
    """
    Si llm es None, devuelve mensaje de error.
    Se espera que llm tenga método invoke(prompt).
    """
    if llm is None:
        return "Error: Gemini no inicializado"

    prompt = f"""Eres un asistente que evalúa si un CV encaja con una convocatoria.
CV:
{cv_text}

Convocatoria:
{convocatoria_text}

Responde en una sola línea con este formato:
SI/NO - razón breve (máx 20 palabras).
"""
    try:
        # Muchas versiones de la librería devuelven un objeto con .content
        resp = llm.invoke(prompt)
        if hasattr(resp, "content"):
            return resp.content.strip()
        else:
            return str(resp).strip()
    except Exception as e:
        return f"Error al usar Gemini: {e}"

# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    todas = scrape_all()  # todas las convocatorias
    filtradas = [c for c in todas if c["sueldo_num"] and c["sueldo_num"] >= 6000]

    # Ordenar por sueldo (descendente)
    filtradas.sort(key=lambda x: x["sueldo_num"], reverse=True)

    # Cargar CV (si existe mi_cv.pdf o mi_cv.txt)
    cv_texto = load_cv_text()

    # Preparar Gemini solo si el flag está activo
    llm = None
    if USE_GEMINI:
        print("ℹ️ USE_GEMINI = True -> intentando inicializar Gemini (asegúrate de tu cuota).")
        llm = init_gemini()
        if llm is None:
            print("⚠️ No se pudo inicializar Gemini. Se continuará en modo prueba.")
            # No forzamos fallo, seguiremos con 'No evaluado (modo prueba)'
            USE_GEMINI = False

    # Evaluar (o modo prueba)
    llamadas = 0
    for conv in filtradas:
        conv_texto = f"{conv.get('titulo')} - Lugar: {conv.get('lugar')} - Sueldo: {conv.get('sueldo_num')} - Fecha: {conv.get('fecha')}"
        if USE_GEMINI:
            # Mostrar aviso y respetar el límite MAX_GEMINI_CALLS
            if MAX_GEMINI_CALLS is not None and llamadas >= MAX_GEMINI_CALLS:
                conv["evaluacion_cv"] = "No evaluado (límite de llamadas alcanzado)"
            else:
                conv["evaluacion_cv"] = evaluar_con_gemini(llm, conv_texto, cv_texto)
                llamadas += 1
        else:
            conv["evaluacion_cv"] = "No evaluado (modo prueba)"

    # Guardar solo las filtradas (igual nombre de archivo que usabas)
    try:
        with open('convocatorias_filtradas.json', 'w', encoding='utf-8') as f:
            json.dump(filtradas, f, indent=4, ensure_ascii=False)

        print("\n✅ Scraping completado con éxito.")
        print(f"📊 {len(filtradas)} convocatorias cumplen el filtro (sueldo >= 6000) de un total de {len(todas)}")
        print("💾 Resultados guardados en el archivo 'convocatorias_filtradas.json'.")
        if USE_GEMINI:
            print(f"🤖 Se realizaron {llamadas} llamadas a Gemini (MAX_GEMINI_CALLS={MAX_GEMINI_CALLS}).")

        # Mostrar en consola TODAS las convocatorias filtradas con buena presentación
        print("\n📝 Convocatorias filtradas:")
        for i, r in enumerate(filtradas, start=1):
            print(f"🔹 {i}. {r.get('titulo')}")
            print(f"   📍 Lugar: {r.get('lugar')}")
            print(f"   💰 Sueldo: {r.get('sueldo_num')}")
            print(f"   📅 Fecha: {r.get('fecha')}")
            print(f"   🔗 Ver: {r.get('ver_convocatoria')}")
            print(f"   📌 Match con CV: {r.get('evaluacion_cv')}")
            print("-" * 60)

    except Exception as e:
        print(f"\n❌ Ocurrió un error al guardar el archivo: {e}")
