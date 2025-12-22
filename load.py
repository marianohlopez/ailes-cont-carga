from playwright.sync_api import sync_playwright
from login import login
import time
from datetime import datetime

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
        input_fc = page.locator('input[wire\\:model\\.defer="nroComprobante"]')
        # BUsco el boton de buscar
        btn_buscar = page.locator('form[wire\\:submit\\.prevent="filtrar"] button:has-text("Buscar")')
        for data_row in data: 
            fc_id = data_row[0] 
            print(f"📌 Filtrando factura {fc_id}")

            # Filtrando por id de factura
            input_fc.fill("")
            input_fc.fill(str(fc_id))
            # Click en Buscar
            btn_buscar.click()

            # Esperar a que aparezca el input hidden con el factura_id correcto
            page.wait_for_selector(
                f'table#table_base_facturas_emitidas_grid div:has-text("{fc_id}")',
                state="attached",
                timeout=10000
            )
            
            print(f"✅ Factura {fc_id} encontrada en la tabla")

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
                fec_env = datetime.strptime(data_row[3], "%Y-%m-%d").strftime("%d/%m/%Y")   
                periodo = data_row[6]   
                os_alum = data_row[7].strip()
                lst_name = data_row[8].split(",")[0].strip()
                name = data_row[8].split(",")[1].strip()
                full_name = f'{name} {lst_name}'
                obs = data_row[-2]
                state = data_row[5]       

                """ print(' '.join(row_indyco[30].split()))
                print(row_indyco[14])      

                print(row_indyco[28])      

                print(row_indyco[-21])      

                print(row_indyco[32])      
                print(row_indyco[-34])      
                print(row_indyco[35].split('(')[0].strip())     
                print(full_name == row_indyco[35].split('(')[0].strip()) 
                print(state == ' '.join(row_indyco[30].split()))
                print(fact_imp == row_indyco[14])
                print(fec_fact == row_indyco[28])
                print(fec_env == row_indyco[-21])
                print(periodo == row_indyco[32])
                print(os_alum == row_indyco[-34]) """

                # Comparar con los datos del excel contable y verificar que la obs no se haya hecho
                if (state == ' '.join(row_indyco[30].split()) and fact_imp == row_indyco[14] and fec_fact == row_indyco[28]
                    and fec_env == row_indyco[-21] and periodo == row_indyco[32] 
                    and os_alum == row_indyco[-34] and full_name == row_indyco[35].split('(')[0].strip()
                    ):

                    # Comparacion con string de indyco sin saltos de lineas
                    if obs.strip() == ' '.join(row_indyco[12].split()):
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