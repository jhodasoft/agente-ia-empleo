import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.convocatoriasdetrabajo.com/ofertas-de-empleo-en-INGENIERIA-DE-SISTEMAS-18.html"

def scrape_page(url):
    """Extrae todas las convocatorias de una sola página"""
    resp = requests.get(url)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    convocatorias = []
    for article in soup.find_all("article", class_="convocatoria"):
        # Título + enlace principal
        titulo_tag = article.find("h4").find("a")
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
            "link": link,
            "requisito": requisito,
            "lugar": lugar,
            "sueldo": sueldo,
            "fecha": fecha,
            "ver_convocatoria": ver_link
        })

    return convocatorias

def scrape_all():
    """Recorre todas las páginas hasta que no encuentre más convocatorias"""
    all_convocatorias = []

    # ✅ Página base (sin parámetros)
    print(f"\n🌍 Scrapeando página 1: {BASE_URL}")
    convocatorias = scrape_page(BASE_URL)
    all_convocatorias.extend(convocatorias)

    # ✅ Páginas siguientes con ?page=N
    page = 2
    while True:
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
    resultados = scrape_all()

    print(f"\n📊 Total convocatorias recolectadas: {len(resultados)}\n")

    for i, r in enumerate(resultados, start=1):  # 👈 arranca desde 1
        print(f"🔹 Convocatoria {i}")
        print(f"   🏢 Título: {r['titulo']}")
        print(f"   🔗 Link: {r['link']}")
        print(f"   🎓 Requisito: {r['requisito']}")
        print(f"   📍 Lugar: {r['lugar']}")
        print(f"   💰 Sueldo: {r['sueldo']}")
        print(f"   📅 Fecha: {r['fecha']}")
        print(f"   📄 Ver convocatoria: {r['ver_convocatoria']}")
        print("-" * 80)
