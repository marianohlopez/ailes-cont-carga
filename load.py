from playwright.sync_api import sync_playwright
from login import login
import time


def load_data(email, password):

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    if not login(page, email, password):
        print("❌ No se pudo iniciar sesión.")
        return []

    # ✅ Ir a Pre-Admisiones
    url = "https://ailes.indyco.com.ar/facturasEmitidas"
    page.goto(url)
    page.wait_for_load_state("networkidle")

    # ✅ Abrir modal
    page.click("button:has-text('Preinscripciones Procesadas')")
    page.wait_for_selector("h4:has-text('Preinscripciones PROCESADAS')", timeout=15000)
    page.wait_for_selector("table tbody tr", timeout=20000)

    tabla = page.locator("table#table_base_default")
    tabla.locator("tbody tr").first.wait_for(state="visible")

    # ✅ Mostrar "Todos"
    select = page.locator('select[wire\\:model\\.live="setUp.footer.perPage"]')
    select.nth(1).select_option("0")
    time.sleep(4)

    # ✅ Selector del filtro por año
    input_anio = page.locator('input[wire\\:model="filters.input_text.pread_ciclo"]')

    for anio_filtro in ["2025","2026"]:
        print(f"📌 Filtrando ciclo {anio_filtro}")

        input_anio.nth(1).fill(anio_filtro)
        time.sleep(5)

        rows = tabla.locator("tbody tr")
        row_count = rows.count()

        if row_count == 0:
            print(f"⚠ No hay filas para el ciclo {anio_filtro}")
            continue

        for i in range(row_count):
            row = rows.nth(i)
            cells = row.locator("td span div")

            col_count = cells.count()
            if col_count == 0:
                continue

            valores = [cells.nth(j).inner_text().strip() for j in range(col_count)]

            # Evitar encabezados fantasmas
            if valores[0] in ["", "AILES"]:
                continue
            
            print(valores[0], valores[9])

            # ✅ Mapear datos
            alumno = {
                "APELLIDO": valores[0],
                "NOMBRE": valores[1],
                "DNI": valores[2],
                "CONTACTO": valores[3],
                "TELEFONO": valores[4],
                "EMAIL": valores[5],
                "LOCALIDAD": valores[6],
                "CICLO": valores[9],
                "FEC_PASE_ADMISION": valores[12],
                "FEC_PASE_NEGATIVA": valores[13]
            }

            alumnos.append(alumno)

    browser.close()

  print(f"✅ Total alumnos extraídos: {len(alumnos)}")
  return alumnos
