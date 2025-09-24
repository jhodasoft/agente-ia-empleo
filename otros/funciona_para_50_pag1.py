import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time

BASE_URL = "https://www.convocatoriasdetrabajo.com/ofertas-de-empleo-en-INGENIERIA-DE-SISTEMAS-18.html"
SITE_ROOT = "https://www.convocatoriasdetrabajo.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def obtener_convocatorias_pagina(url):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    convocatorias = []
    for art in soup.select("article.convocatoria"):
        data = {}

        # titulo + entidad
        titulo_a = art.select_one("h4 a")
        if titulo_a:
            data["titulo"] = titulo_a.get_text(strip=True)
            data["detalle_url"] = urljoin(SITE_ROOT, titulo_a["href"])

        # requisitos (icon-grado)
        req = art.select_one("i.icon-grado + span")
        data["requisitos"] = req.get_text(strip=True) if req else ""

        # ubicación (icon-mapa1)
        loc = art.select_one("i.icon-mapa1 + span")
        data["ubicacion"] = loc.get_text(strip=True) if loc else ""

        # remuneración (icon-moneda)
        sueldo = art.select_one("i.icon-moneda + span")
        data["remuneracion"] = sueldo.get_text(strip=True) if sueldo else ""

        # fecha cierre (icon-calendario)
        fecha = art.select_one("i.icon-calendario + span")
        data["fecha_cierre"] = fecha.get_text(strip=True) if fecha else ""

        # obtener PDF entrando al detalle
        data["pdf_url"] = obtener_pdf_detalle(data["detalle_url"]) if data.get("detalle_url") else ""

        convocatorias.append(data)

    return convocatorias

def obtener_pdf_detalle(url):
    """Visita la página de detalle y extrae el link del PDF."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        pdf_tag = soup.find("a", href=re.compile(r"\.pdf$", re.I))
        if pdf_tag and pdf_tag.get("href"):
            return urljoin(SITE_ROOT, pdf_tag["href"])
    except Exception as e:
        print(f"⚠️ Error al extraer PDF de {url}: {e}")
    return ""

def main():
    url = BASE_URL
    convocatorias = obtener_convocatorias_pagina(url)

    print(f"Encontradas {len(convocatorias)} convocatorias en la primera página\n")
    for i, c in enumerate(convocatorias, 1):
        print(f"{i}. {c['titulo']}")
        print(f"   Requisitos: {c['requisitos']}")
        print(f"   Ubicación: {c['ubicacion']}")
        print(f"   Remuneración: {c['remuneracion']}")
        print(f"   Cierre: {c['fecha_cierre']}")
        print(f"   Detalle: {c['detalle_url']}")
        print(f"   PDF: {c['pdf_url']}\n")
        time.sleep(0.5)  # para no saturar el servidor

if __name__ == "__main__":
    main()
