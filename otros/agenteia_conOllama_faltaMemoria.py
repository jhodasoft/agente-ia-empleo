# agenteia.py
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import PyPDF2
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
import json

# ========================
# Extraer texto del CV
# ========================
def extraer_texto_cv(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        texto = ""
        for page in reader.pages:
            if page.extract_text():
                texto += page.extract_text() + "\n"
    return texto

cv_texto = extraer_texto_cv("mi_cv.pdf")

# ========================
# Scraping convocatorias
# ========================
BASE_URL = "https://www.convocatoriasdetrabajo.com/ofertas-de-empleo-en-INGENIERIA-DE-SISTEMAS-18.html"

def scrape_convocatorias(max_pages: int = 30) -> List[Dict]:
    convocatorias = []
    for page in range(1, max_pages + 1):
        url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}&sort=1-fechapublicacion"
        print(f"\n🌍 Scrapeando página {page}: {url}")
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("div.media-body")
        if not items:
            print("✅ No hay más convocatorias. Fin del scraping.")
            break

        for item in items:
            titulo = item.select_one("h2 a").get_text(strip=True) if item.select_one("h2 a") else "N/A"
            empresa = item.select_one("p strong").get_text(strip=True) if item.select_one("p strong") else "N/A"
            detalles = item.select("p")
            sueldo, ubicacion = "N/A", "N/A"
            for d in detalles:
                txt = d.get_text(strip=True)
                if "Sueldo:" in txt:
                    sueldo = txt.replace("Sueldo:", "").strip()
                if "Lugar de trabajo:" in txt:
                    ubicacion = txt.replace("Lugar de trabajo:", "").strip()
            convocatorias.append({
                "titulo": titulo,
                "empresa": empresa,
                "sueldo": sueldo,
                "ubicacion": ubicacion,
            })
    return convocatorias

# ========================
# Parsear sueldo
# ========================
def parse_sueldo(sueldo_str: str) -> float:
    if not sueldo_str or sueldo_str == "N/A":
        return 0
    numeros = "".join([c if c.isdigit() else " " for c in sueldo_str])
    partes = [int(p) for p in numeros.split() if p.isdigit()]
    if not partes:
        return 0
    return max(partes)

# ========================
# Cruzar con CV (usando Ollama)
# ========================
def cruzar_con_cv(convocatorias: List[Dict], cv_texto: str) -> List[Dict]:
    try:
        # 🔹 Modelo de Ollama (puedes cambiarlo por otro que tengas instalado: llama3, mistral, etc.)
        llm = ChatOllama(
            model="gemma:2b",#"llama3(estaba antes, pero mi pc no lo aguanta)",  # o "mistral", "gemma", etc.
            temperature=0.2
        )

        prompt = ChatPromptTemplate.from_template("""
Eres un asistente que cruza convocatorias laborales con el perfil del CV.
Responde en JSON válido con la forma:
[
  {{"titulo": "...", "empresa": "...", "sueldo": "...", "ubicacion": "...", "match_cv": true/false}},
  ...
]

Convocatorias:
{convocatorias}

CV:
{cv}
""")

        chain = prompt | llm
        resp = chain.invoke({"convocatorias": convocatorias, "cv": cv_texto})
        text = resp.content.strip()

        return json.loads(text)

    except Exception as e:
        print(f"⚠️ No se pudo cruzar con CV (motivo: {e}). Mostrando convocatorias filtradas sin cruce.\n")
        # Si falla, devolver las convocatorias con match_cv = "No evaluado"
        for c in convocatorias:
            c["match_cv"] = "No evaluado"
        return convocatorias


# ========================
# MAIN
# ========================
if __name__ == "__main__":
    convocatorias = scrape_convocatorias(max_pages=30)
    print(f"\n📌 Total convocatorias extraídas: {len(convocatorias)}")

    # Filtro sueldo >= 5000
    filtradas = [c for c in convocatorias if parse_sueldo(c["sueldo"]) >= 5000]
    print(f"📊 {len(filtradas)} convocatorias cumplen el filtro (sueldo >= 5000) de un total de {len(convocatorias)}\n")

    # Cruce con CV (si hay cuota disponible)
    resultado = cruzar_con_cv(filtradas, cv_texto)

    # Mostrar en consola de manera legible
    for idx, r in enumerate(resultado, 1):
        print(f"🔹 {idx}. {r['titulo']}")
        print(f"   🏢 Empresa: {r['empresa']}")
        print(f"   📍 Ubicación: {r['ubicacion']}")
        print(f"   💰 Sueldo: {r['sueldo']}")
        print(f"   📌 Match con CV: {r.get('match_cv', 'No evaluado')}")
        print("-" * 60)
