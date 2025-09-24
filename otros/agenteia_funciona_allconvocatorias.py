import requests
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import PyPDF2
from langchain_google_genai import ChatGoogleGenerativeAI

# === CONFIGURACIÓN ===
load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# === FUNCIÓN PARA LEER CV ===
def extraer_texto_cv(pdf_path: str) -> str:
    """Extrae texto desde un archivo PDF de CV"""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
    return texto

CV_TEXTO = extraer_texto_cv("mi_cv.pdf")  # 👈 asegúrate de tener tu CV en la misma carpeta con este nombre

# === SCRAPING DE CONVOCATORIAS ===
def scrape_convocatorias(paginas=5):
    convocatorias = []
    for p in range(1, paginas + 1):
        if p == 1:
            url = "https://www.convocatoriasdetrabajo.com/ofertas-de-empleo-en-INGENIERIA-DE-SISTEMAS-18.html"
        else:
            url = f"https://www.convocatoriasdetrabajo.com/ofertas-de-empleo-en-INGENIERIA-DE-SISTEMAS-18.html?page={p}&sort=1-fechapublicacion"

        print(f"\n🌍 Scrapeando página {p}: {url}")
        r = requests.get(url)
        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, "html.parser")

        for article in soup.find_all("article", class_="convocatoria"):
            titulo_tag = article.find("h4").find("a")
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else None
            enlace = titulo_tag["href"] if titulo_tag else None

            detalle = article.get_text(" ", strip=True)

            convocatorias.append({
                "titulo": titulo,
                "detalle": detalle,
                "enlace": enlace
            })

        time.sleep(2)  # descanso entre páginas para no sobrecargar
    return convocatorias

# === ANÁLISIS EN BLOQUES DE 5 ===
def analizar_en_bloques(convocatorias, cv_texto, bloque=5):
    resultados = []
    for i in range(0, len(convocatorias), bloque):
        lote = convocatorias[i:i+bloque]
        texto_convocatorias = "\n\n".join(
            [f"{idx+1}. {c['titulo']} - {c['detalle']}" for idx, c in enumerate(lote)]
        )

        prompt = f"""
        Soy un postulante con el siguiente perfil:
        {cv_texto}

        Estas son varias convocatorias de empleo. 
        Evalúa del 1 al {len(lote)} si se ajustan a mi perfil y justifica brevemente cada una:

        {texto_convocatorias}
        """

        print(f"\n🤖 Analizando bloque {i//bloque + 1} con {len(lote)} convocatorias...")
        try:
            respuesta = llm.invoke(prompt).content
            resultados.append(respuesta)
        except Exception as e:
            print(f"⚠️ Error analizando bloque {i//bloque + 1}: {e}")
        
        time.sleep(10)  # espera para no pasarte de cuota

    return resultados

# === MAIN ===
if __name__ == "__main__":
    convocatorias = scrape_convocatorias(paginas=4)
    print(f"\n📌 Total convocatorias extraídas: {len(convocatorias)}")

    resultados = analizar_en_bloques(convocatorias, CV_TEXTO, bloque=5)

    print("\n=== RESULTADOS ===")
    for r in resultados:
        print(r)
        print("="*80)
