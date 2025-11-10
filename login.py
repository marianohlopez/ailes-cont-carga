def login(page, email, password):
    page.goto("https://ailes.indyco.com.ar/login")

    # Completar login
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")

    # Espera a que termine
    page.wait_for_load_state("networkidle")

    # Comprobamos si realmente inició sesión
    if "/home" in page.url:
        print("✅ Login exitoso en Playwright")
        return True

    print("❌ Falló el login")
    return False
