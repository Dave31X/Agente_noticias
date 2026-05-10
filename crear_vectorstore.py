# 2_crear_vectorstore.py
# Lee las noticias en texto, las convierte en vectores y las guarda en ChromaDB
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

def cargar_noticias_como_documentos():
    """
    Lee el archivo de texto con las noticias
    y las convierte en objetos Document de LangChain
    """
    print("📂 Leyendo noticias desde datos/noticias.txt...")
    
    with open("datos/noticias.txt", "r", encoding="utf-8") as f:
        contenido = f.read()
    
    # Separar cada noticia por el separador que usamos
    noticias_raw = contenido.split("=== NOTICIA ")
    noticias_raw = [n for n in noticias_raw if n.strip()]
    
    documentos = []
    for noticia_texto in noticias_raw:
        if len(noticia_texto.strip()) > 100:  # ignorar textos muy cortos
            doc = Document(
                page_content=noticia_texto.strip(),
                metadata={"fuente": "NewsAPI"}
            )
            documentos.append(doc)
    
    print(f"   ✅ {len(documentos)} noticias cargadas como documentos")
    return documentos

def crear_chunks(documentos):
    """
    Divide cada noticia en fragmentos más pequeños
    para que el RAG sea más preciso
    """
    print("\n✂️  Dividiendo documentos en chunks...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # cada fragmento tiene máximo 500 caracteres
        chunk_overlap=50,    # 50 caracteres se repiten entre fragmentos
        separators=["\n\n", "\n", ".", " "]
    )
    
    chunks = splitter.split_documents(documentos)
    print(f"   ✅ {len(chunks)} chunks creados")
    return chunks

def crear_vectorstore(chunks):
    """
    Convierte los chunks en vectores numéricos (embeddings)
    y los guarda en ChromaDB
    """
    print("\n🔢 Creando embeddings (esto puede tardar 1-2 minutos)...")
    
    # Modelo de embeddings GRATIS de HuggingFace
    # Se descarga automáticamente la primera vez
    
    embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
    )
    
    print("💾 Guardando en ChromaDB...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./datos/noticias_db"  # se guarda en disco
    )
    
    print(f"   ✅ Vector store creado con {len(chunks)} fragmentos")
    print("   📁 Guardado en: datos/noticias_db/")
    
    return vectorstore

# ── Ejecutar ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Creando Vector Store...\n")
    
    documentos = cargar_noticias_como_documentos()
    chunks = crear_chunks(documentos)
    vectorstore = crear_vectorstore(chunks)
    
    # Prueba rápida
    print("\n🧪 Prueba de búsqueda:")
    resultados = vectorstore.similarity_search("economía Colombia", k=2)
    for r in resultados:
        print(f"   → {r.page_content[:100]}...")
    
    print("\n🎉 Vector Store listo!")