import requests
from bs4 import BeautifulSoup
import json
import re  # Para limpiar el sueldo y convertirlo en número

BASE_URL = "https://www.convocatoriasdetrabajo.com/ofertas-de-empleo-en-INGENIERIA-DE-SISTEMAS-18.html"


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

        # Requisitos
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
            # "link": link,
            # "requisito": requisito,
            "lugar": lugar,
            # "sueldo": sueldo,
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


if __name__ == "__main__":
    todas = scrape_all()  # todas las convocatorias
    filtradas = [c for c in todas if c["sueldo_num"] and c["sueldo_num"] >= 6000]

    # Ordenar por sueldo (descendente)
    filtradas.sort(key=lambda x: x["sueldo_num"], reverse=True)

    # Guardar solo las filtradas
    try:
        with open('convocatorias_filtradas.json', 'w', encoding='utf-8') as f:
            json.dump(filtradas, f, indent=4, ensure_ascii=False)

        print("\n✅ Scraping completado con éxito.")
        print(f"📊 {len(filtradas)} convocatorias cumplen el filtro (sueldo >= 6000) de un total de {len(todas)}")
        print("💾 Resultados guardados en el archivo 'convocatorias_filtradas.json'.")

        # Mostrar las primeras 5 ordenadas
        print("\n📝 Top 5 convocatorias con mayor sueldo:")
        for i, r in enumerate(filtradas[:5], start=1):
            print(f"🔹 {i}. {r['titulo']} - Sueldo: {r['sueldo_num']}")

    except Exception as e:
        print(f"\n❌ Ocurrió un error al guardar el archivo: {e}")
