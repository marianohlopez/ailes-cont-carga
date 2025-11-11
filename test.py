from googleapiclient.discovery import build
from google.auth import default

def main():

    creds, _ = default()
    service = build("drive", "v3", credentials=creds)

    print("\n✅ Autenticación correcta con la Service Account")

    DRIVE_ID = "0ALVObxz8zlW1Uk9PVA" 
    print(f"\n📂 Listando archivos dentro de la unidad compartida {DRIVE_ID}:\n")

    results = service.files().list(
        pageSize=20,
        fields="files(id, name, mimeType)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        corpora="drive",
        driveId=DRIVE_ID
    ).execute()

    files = results.get("files", [])

    if not files:
        print("⚠ No se encontraron archivos.")
    else:
        for f in files:
            print(f"- {f['name']} ({f['id']}) | {f['mimeType']}")


if __name__ == "__main__":
    main()
