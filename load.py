from playwright.sync_api import sync_playwright
from login import login
import time
import re

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

def load_data(email, password, data):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        if not login(page, email, password):
            print("❌ No se pudo iniciar sesión.")
            return []

        # ✅ Ir a Facturas Emitidas
        url = "https://ailes.indyco.com.ar/facturasEmitidas"
        page.goto(url)
        page.wait_for_load_state("networkidle")

        table = page.locator("table#table_base_facturas_emitidas_grid")
        table.locator("tbody tr").first.wait_for(state="visible")

        # ✅ Selector del filtro por nro de comprobante
        btn_limpiar = page.locator('button:has-text("Limpiar")')
        clean(btn_limpiar, page)
        count_clean = 0

        for data_row in data: 

            count_clean += 1

            if count_clean == 5:
                # Limpiar filtros
                clean(btn_limpiar, page)
                count_clean = 0

            fc_id = data_row[0] 
            print(f"📌 Filtrando factura {fc_id}")

            MAX_INTENTOS = 5
            encontrado = False

            for intento in range(1, MAX_INTENTOS + 1):
                print(f"🔄 Intento {intento}: buscando factura {fc_id}")
                btn_buscar = page.locator('form[wire\\:submit\\.prevent="filtrar"] button:has-text("Buscar")')
                # Filtrando por id de factura

                # 🔁 Re-localizar el input (DOM puede haber cambiado)
                input_fc = page.locator('#ts-nros-comprobante-ts-control')
                input_fc.click()
                input_fc.press("Control+A")
                #input_fc.type(str(fc_id), delay=50)
                input_fc.fill(str(fc_id))
                page.wait_for_timeout(2000)
                input_fc.press("Enter")
                page.wait_for_timeout(1500)
                btn_buscar.click()

                try:
                    page.wait_for_selector(
                        f'table#table_base_facturas_emitidas_grid div:has-text("{fc_id}")',
                        state="attached",
                        timeout=10000
                    )

                    print(f"✅ Factura {fc_id} encontrada en la tabla")
                    encontrado = True
                    break   # sale solo del loop de reintentos

                except Exception:
                    print(f"⚠️ Factura {fc_id} no encontrada, reintentando...")

            if not encontrado:
                print(f"❌ ERROR CRÍTICO: no se encontró la factura {fc_id} después de {MAX_INTENTOS} intentos")
                browser.close()
                return   # ⬅ DETIENE load_data COMPLETO

            rows = table.locator("tbody tr")
            row_count = rows.count()

            if row_count == 0:
                print(f"⚠ No hay filas para la factura {fc_id}")
                continue

            for i in range(row_count):
                table_row = rows.nth(i) 
                cells = table_row.locator("td span div")

                col_count = cells.count()
                if col_count == 0:
                    continue

                row_indyco = [cells.nth(j).inner_text().strip() for j in range(col_count)]

                # Evitar encabezados fantasmas
                if row_indyco[0] in [""]:
                    continue

                fact_imp = str(data_row[1]).replace(",", ".")  
                fec_fact = data_row[2].strftime("%d/%m/%Y")    
                #fec_env = datetime.strptime(data_row[3], "%Y-%m-%d").strftime("%d/%m/%Y")   
                periodo = data_row[6]   
                #os_alum = data_row[7].strip()
                lst_name = data_row[8].split(",")[0].strip()
                name = data_row[8].split(",")[1].strip()
                full_name = f'{lst_name} {name}'
                obs = data_row[-2]
                #state = data_row[5]       
                name_indyco = f'{row_indyco[41].strip()} {row_indyco[42].strip()}'
                """ print(row_indyco)
                print('------------------------------------------------------------')
                
                print(row_indyco[16], f'excel: {fact_imp}', fact_imp == row_indyco[16])      
                print(row_indyco[32], f'excel: {fec_fact}', fec_fact == row_indyco[32])           
                print(row_indyco[36], f'excel: {periodo}', periodo == row_indyco[36])  
                print(name_indyco, f'{full_name}', full_name == name_indyco)   """   

                # Comparar con los datos del excel contable y verificar que la obs no se haya hecho
                # No comparamos estado ni OS por si se modifica en indyco
                if (fc_id == row_indyco[6] and fact_imp == row_indyco[16] and fec_fact == row_indyco[32]
                    and periodo == row_indyco[36] and full_name == name_indyco):

                    obs_excel = normalizar_texto(obs)
                    obs_indyco = normalizar_texto(row_indyco[14])

                    # Comparacion con string de indyco sin saltos de lineas
                    if obs_excel == obs_indyco:
                        print(f'La observacion de la factura {fc_id} ya esta en indyco, '
                                'pasando a la siguiente...')
                        continue

                    print(f"✅ Factura {fc_id} encontrada, procediendo a editar...")
                        
                    # Hacer click en el botón de edición (columna 8)
                    edit_button = table_row.locator('td button[wire\\:modal*="entidad-etiquetas-edit"]')
                    
                    if edit_button.count() > 0:
                        # Click en el botón de edición
                        edit_button.first.click()
                        time.sleep(4)
                        
                        # Esperar a que aparezca el modal y el textarea
                        textarea_selector = 'textarea[wire\\:model="factura_obs"]'
                        page.wait_for_selector(textarea_selector)
                        
                        # Localizar y limpiar el textarea
                        textarea = page.locator(textarea_selector)
                        textarea.clear()
                        
                        # Escribir la observación
                        textarea.fill(obs)
                        
                        # Hacer click en el botón GUARDAR usando el ID
                        save_button = page.locator('#btn_guardar')

                        if save_button.count() > 0:

                            # registra un listener
                            dialog_handled = False

                            def handle_dialog(dialog):
                                nonlocal dialog_handled
                                if not dialog_handled:
                                    dialog.accept()
                                    dialog_handled = True
                            
                            # Manejar el alert de confirmación
                            page.on("dialog", handle_dialog)

                            save_button.scroll_into_view_if_needed()
                            save_button.click()
                            time.sleep(1)
                            
                            print(f"✅ Observación agregada: {data_row[-2]}")
                            time.sleep(2)
                        
                        else:
                            print("no se encontro el boton de guardado")

                    else:
                        print(f"❌ No se encontró el botón de edición para la factura {fc_id}")    

                else:
                    print(f"❌ Factura {fc_id} NO coincide con el excel contable.")

        browser.close()

    print(f"✅ Proceso completado para {len(data)} facturas")