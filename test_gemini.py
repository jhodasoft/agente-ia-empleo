from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Cargar variables de entorno (.env)
load_dotenv()

# Inicializar modelo
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Hacer una prueba simple
pregunta = "Dame un resumen breve sobre la bolsa de Nueva York hoy."
respuesta = llm.invoke(pregunta)

print("🔹 Pregunta:", pregunta)
print("🔹 Respuesta:", respuesta.content if hasattr(respuesta, "content") else respuesta)
