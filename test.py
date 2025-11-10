from googleapiclient.discovery import build
from google.auth import default

def main():

    # Obtiene las credenciales del entorno (WIF en GitHub Actions)
    creds, _ = default()

    # Inicializa el cliente de Drive
    service = build("drive", "v3", credentials=creds)

    print("\n✅ Autenticación correcta con la Service Account")

    # ----------------------------
    # MODO 1 — Listar archivos del Drive personal / Mi Unidad
    # ----------------------------
    print("\n📂 Listando archivos de 'Mi unidad':\n")

    results = service.files().list(
        pageSize=20,
        fields="files(id, name, mimeType)"
    ).execute()

    files = results.get("files", [])

    if not files:
        print("⚠ No se encontraron archivos.")
    else:
        for f in files:
            print(f"- {f['name']} ({f['id']}) | {f['mimeType']}")

    # ----------------------------
    # MODO 2 — Listar archivos de una carpeta específica (opcional)
    # ----------------------------
    # Para usar este modo:
    # 1. Buscá en Drive la carpeta
    # 2. Copiá su ID de la URL
    # 3. Pegalo acá:

    FOLDER_ID = "0ALVObxz8zlW1Uk9PVA" 

    if FOLDER_ID:
        print(f"\n📁 Listando archivos dentro de la carpeta {FOLDER_ID}:\n")

        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            pageSize=20,
            fields="files(id, name, mimeType)"
        ).execute()

        files = results.get("files", [])

        if not files:
            print("⚠ La carpeta está vacía.")
        else:
            for f in files:
                print(f"- {f['name']} ({f['id']})")


if __name__ == "__main__":
    main()
