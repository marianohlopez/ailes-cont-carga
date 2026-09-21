from playwright.sync_api import sync_playwright
from login import login
import time
import re

MIN_COLS = 48          # el código usa índices hasta row_indyco[47]
MAX_INTENTOS = 5


def clean(btn_clean, page):
    print("🧹 Limpiando filtros")
    btn_clean.click()
    page.wait_for_timeout(4000)


def normalizar_texto(txt):
    if not txt:
        return ''
    txt = txt.lower()
    txt = txt.replace('<br>', ' ')
    txt = re.sub(r'\s+', ' ', txt)  # espacios, tabs, saltos de línea
    return txt.strip()


def leer_fila(table_row, page, min_cols=MIN_COLS, reintentos=3):
    """
    Lee todas las celdas de la fila en una sola llamada (all_inner_texts no
    espera ni tira timeout). Si el DOM está a medio renderizar, reintenta.
    Devuelve None si no logra una fila completa.
    """
    for _ in range(reintentos):
        try:
            textos = [t.strip() for t in table_row.locator("td span div").all_inner_texts()]
        except Exception:
            textos = []

        if len(textos) >= min_cols:
            return textos

        page.wait_for_timeout(1000)

    return None


def buscar_factura(page, table, fc_id):
    """
    Aplica el filtro y espera a que la tabla muestre una fila con la factura.
    Devuelve True si la encontró, False si agotó los reintentos.
    """
    btn_buscar = page.locator('form[wire\\:submit\\.prevent="filtrar"] button:has-text("Buscar")')

    for intento in range(1, MAX_INTENTOS + 1):
        print(f"🔄 Intento {intento}: buscando factura {fc_id}")

        try:
            # Re-localizar el input (el DOM puede haber cambiado)
            input_fc = page.locator('#ts-nros-comprobante-ts-control')
            input_fc.click()
            input_fc.press("Control+A")
            input_fc.fill(str(fc_id))
            page.wait_for_timeout(2000)
            input_fc.press("Enter")
            page.wait_for_timeout(1500)

            # Esperar la respuesta real de Livewire al filtrar
            with page.expect_response(
                lambda r: "livewire" in r.url and r.request.method == "POST",
                timeout=15000
            ):
                btn_buscar.click()

            # Esperar una FILA que contenga la factura (no un div ancestro)
            fila = table.locator("tbody tr").filter(has_text=str(fc_id))
            fila.first.wait_for(state="visible", timeout=15000)
            page.wait_for_load_state("networkidle")

            print(f"✅ Factura {fc_id} encontrada en la tabla")
            return True

        except Exception as e:
            print(f"⚠️ Factura {fc_id} no encontrada ({type(e).__name__}), reintentando...")

    return False


def load_data(email, password, data):
    obs_ingresadas = 0
    obs_ing_anteriormente = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Un solo handler para los alert de confirmación
        page.on("dialog", lambda d: d.accept())

        if not login(page, email, password):
            print("❌ No se pudo iniciar sesión.")
            browser.close()
            return []

        # Ir a Facturas Emitidas
        url = "https://ailes.indyco.com.ar/facturasEmitidas"
        page.goto(url)
        page.wait_for_load_state("networkidle")

        table = page.locator("table#table_base_facturas_emitidas_grid")
        table.locator("tbody tr").first.wait_for(state="visible")

        btn_limpiar = page.locator('button:has-text("Limpiar")')
        clean(btn_limpiar, page)
        count_clean = 0

        for data_row in data:

            count_clean += 1

            if count_clean == 5:
                clean(btn_limpiar, page)
                count_clean = 0

            fc_id = data_row[0]
            print(f"📌 Filtrando factura {fc_id}")

            if not buscar_factura(page, table, fc_id):
                print(f"❌ ERROR CRÍTICO: no se encontró la factura {fc_id} después de {MAX_INTENTOS} intentos")
                browser.close()
                return  # detiene load_data completo

            # Solo las filas de ESTA factura (locator lazy: se re-evalúa solo)
            rows = table.locator("tbody tr").filter(has_text=str(fc_id))
            row_count = rows.count()

            if row_count == 0:
                print(f"⚠ No hay filas para la factura {fc_id}")
                continue

            for i in range(row_count):
                table_row = rows.nth(i)

                row_indyco = leer_fila(table_row, page)
                if row_indyco is None:
                    print(f"⚠ No se pudo leer la fila {i} de la factura {fc_id}, salteando...")
                    continue

                # Evitar encabezados fantasmas
                if row_indyco[0] == "":
                    continue

                fact_imp = str(data_row[1]).replace(",", ".")
                fec_fact = data_row[2].strftime("%d/%m/%Y")
                periodo = data_row[6]
                lst_name = data_row[8].split(",")[0].strip()
                name = data_row[8].split(",")[1].strip()
                full_name = f'{lst_name} {name}'
                obs = data_row[10]
                name_indyco = f'{row_indyco[46].strip()} {row_indyco[47].strip()}'
                fact_imp_indyco = row_indyco[17]
                fec_fact_indyco = row_indyco[37]
                periodo_indyco = row_indyco[41]

                """ print(row_indyco)
                    print('------------------------------------------------------------')
                    
                    print(row_indyco[17], f'excel: {fact_imp}', fact_imp == row_indyco[17])      
                    print(row_indyco[37], f'excel: {fec_fact}', fec_fact == row_indyco[37])           
                    print(row_indyco[41], f'excel: {periodo}', periodo == row_indyco[41])  
                    print(name_indyco, f'excel: {full_name}', full_name == name_indyco)     
                    print(row_indyco[7], f'excel: {fc_id}', fc_id == row_indyco[7])
                    print(normalizar_texto(obs) == normalizar_texto(row_indyco[15])) """

                # Comparar con los datos del excel contable y verificar que la obs no se haya hecho
                # No comparamos estado ni OS por si se modifica en indyco
                if (fc_id == row_indyco[7] and fact_imp == fact_imp_indyco and fec_fact == fec_fact_indyco
                        and periodo == periodo_indyco and full_name == name_indyco):

                    obs_excel = normalizar_texto(obs)
                    obs_indyco = normalizar_texto(row_indyco[15])

                    # Comparación con string de indyco sin saltos de línea
                    if obs_excel == obs_indyco:
                        obs_ing_anteriormente += 1
                        print(f'La observacion de la factura {fc_id} ya esta en indyco, '
                              'pasando a la siguiente...')
                        continue

                    print(f"✅ Factura {fc_id} encontrada, procediendo a editar...")

                    # Botón de edición
                    edit_button = table_row.locator('td button[wire\\:modal*="entidad-etiquetas-edit"]')

                    if edit_button.count() > 0:
                        edit_button.first.click()
                        time.sleep(4)

                        # Esperar el modal y el textarea
                        textarea_selector = 'textarea[wire\\:model="factura_obs"]'
                        page.wait_for_selector(textarea_selector)

                        textarea = page.locator(textarea_selector)
                        textarea.clear()
                        textarea.fill(obs)

                        # Botón GUARDAR
                        save_button = page.locator('button[wire\\:click\\.prevent="save()"]')

                        if save_button.count() > 0:
                            save_button.scroll_into_view_if_needed()
                            save_button.click()
                            time.sleep(1)

                            print(f"✅ Observación agregada: {data_row[10]}")
                            obs_ingresadas += 1
                            time.sleep(2)
                        else:
                            print("no se encontro el boton de guardado")

                    else:
                        print(f"❌ No se encontró el botón de edición para la factura {fc_id}")

                else:
                    print(f"❌ Factura {fc_id} NO coincide con el excel contable.")

        browser.close()

    print(f"✅ Proceso completado para {len(data)} facturas")

    return {
        "obs_ingresadas": obs_ingresadas,
        "obs_ing_anteriormente": obs_ing_anteriormente
    }