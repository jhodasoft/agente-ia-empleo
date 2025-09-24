# requirements (ejemplo):
# pip install requests beautifulsoup4 python-dotenv langchain langchain-google-genai langchain-ollama langchain-text-splitters

from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
import time

load_dotenv()

# --- CONFIG ---
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3.5")
USER_AGENT = "Mozilla/5.0 (compatible; vacancy-scraper/1.0)"

# Inicializa modelos (asegúrate de tener las credenciales / servicios)
llm_gemini = ChatGoogleGenerativeAI(model=GOOGLE_MODEL)
llm_ollama = ChatOllama(model=OLLAMA_MODEL)  # opcional

def extraer_texto_desde_url(url: str, max_chars=None) -> str:
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()  # lanza excepción si status != 200
    soup = BeautifulSoup(resp.content, "html.parser")

    # eliminar elementos no útiles
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)  # NOTE: 'separator' es correcto
    if max_chars:
        return text[:max_chars]
    return text

def analizar_pagina_con_gemini(url: str):
    html_text = extraer_texto_desde_url(url)

    # CHUNKEAR para no pasar todo en una sola llamada (evita límites de tokens)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=200
    )
    chunks = splitter.split_text(html_text)

    mini_resumenes = []
    for i, chunk in enumerate(chunks, start=1):
        prompt = (
            f"Este es un fragmento (parte {i}/{len(chunks)}) de la página {url}.\n"
            "Analiza si en este fragmento hay noticias que puedan afectar acciones en bolsa. "
            "Si hay, indica brevemente: 1) por qué afecta; 2) empresas/sectores mencionados; 3) cifras relevantes.\n\n"
            f"{chunk}"
        )
        try:
            resp = llm_gemini.invoke(prompt)  # invoke acepta un string o lista de mensajes
        except Exception as e:
            print(f"Error llamando al LLM en chunk {i}: {e}")
            continue

        # el objeto devuelto puede tener .content o ser imprimible; accedemos de forma segura:
        text_out = getattr(resp, "content", None) or str(resp)
        mini_resumenes.append(text_out)
        time.sleep(0.3)  # pausa corta para cortesía / rate limits

    # Consolidar mini-resúmenes en un único prompt
    consolidated_prompt = (
        "He analizado la página en varias partes. A continuación están los mini-resúmenes.\n\n"
        + "\n\n".join(mini_resumenes)
        + "\n\nCon base en todo lo anterior, dame una conclusión clara y breve: ¿hay noticias relevantes que puedan afectar acciones? "
        "Enumera empresas/sectores y una valoración breve (sí/no + por qué)."
    )

    final_resp = llm_gemini.invoke(consolidated_prompt)
    final_text = getattr(final_resp, "content", None) or str(final_resp)
    return final_text

if __name__ == "__main__":
    url = "https://edition.cnn.com"
    resultado = analizar_pagina_con_gemini(url)
    print("Resultado final:\n", resultado)
