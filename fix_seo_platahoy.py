#!/usr/bin/env python3
"""
Script para corregir issues de SEO en los artículos de Plata Hoy.
Ejecutar desde la raíz del proyecto (donde está /articulos/).

Uso:
    python fix_seo_platahoy.py

Crea copias de seguridad en articulos/_backup/ antes de modificar.
"""

import os
import re
import shutil


ARTICLES_DIR = "articulos"
BACKUP_DIR = os.path.join(ARTICLES_DIR, "_backup")


# ─── Fixes ─────────────────────────────────────────────────────────────


def fix_share_buttons(html: str) -> str:
    """Eliminar .html de las URLs en los botones de compartir."""
    return re.sub(
        r'(href="[^"]*?/articulos/[^"]+?)\.html(")',
        r'\1\2',
        html
    )


def fix_nav_links(html: str) -> str:
    """Eliminar .html de los enlaces de navegación entre artículos."""
    return re.sub(
        r'(href="/articulos/[^"]+?)\.html(")',
        r'\1\2',
        html
    )


def fix_h1_duplicate(html: str) -> str:
    """Cambiar el <h1> del header (logo) por <span>."""
    html = html.replace(
        '<h1><a href="/">🏠 Plata Hoy</a></h1>',
        '<span class="logo"><a href="/">🏠 Plata Hoy</a></span>'
    )
    html = html.replace(
        '<h1><a href="/">Plata Hoy</a></h1>',
        '<span class="logo"><a href="/">Plata Hoy</a></span>'
    )
    return html


def extract_meta(html: str, name: str) -> str:
    """Extraer contenido de un meta tag."""
    # name="..."
    m = re.search(rf'<meta\s+name="{name}"\s+content="([^"]*)"', html)
    if m:
        return m.group(1)
    # property="..."
    m = re.search(rf'<meta\s+property="{name}"\s+content="([^"]*)"', html)
    if m:
        return m.group(1)
    return ""


def add_missing_meta_tags(html: str) -> str:
    """Agregar og:url, og:locale, og:site_name y Twitter Cards si faltan."""
    canonical = extract_meta(html, 'canonical')
    og_title = extract_meta(html, 'og:title')
    og_description = extract_meta(html, 'og:description')
    og_image = extract_meta(html, 'og:image')

    tags_to_add = []

    if canonical and 'property="og:url"' not in html:
        tags_to_add.append(f'    <meta property="og:url" content="{canonical}">')

    if 'property="og:locale"' not in html:
        tags_to_add.append('    <meta property="og:locale" content="es_AR">')

    if 'property="og:site_name"' not in html:
        tags_to_add.append('    <meta property="og:site_name" content="Plata Hoy">')

    if 'name="twitter:card"' not in html:
        tags_to_add.append('    <meta name="twitter:card" content="summary_large_image">')
    if 'name="twitter:title"' not in html and og_title:
        tags_to_add.append(f'    <meta name="twitter:title" content="{og_title}">')
    if 'name="twitter:description"' not in html and og_description:
        tags_to_add.append(f'    <meta name="twitter:description" content="{og_description}">')
    if 'name="twitter:image"' not in html and og_image:
        tags_to_add.append(f'    <meta name="twitter:image" content="{og_image}">')

    if not tags_to_add:
        return html

    new_tags = "\n".join(tags_to_add) + "\n"

    # Insertar después del último meta og existente
    # Buscar og:type como punto de insercion
    if 'property="og:type"' in html:
        idx = html.index('property="og:type"')
        end = html.index('>', idx) + 1
        html = html[:end] + "\n" + new_tags + html[end:]
    elif 'property="og:title"' in html:
        idx = html.index('property="og:title"')
        html = html[:idx] + new_tags + html[idx:]
    else:
        # Fallback: antes de </head>
        idx = html.index("</head>")
        html = html[:idx] + new_tags + html[idx:]

    return html


def fix_encoding(html: str) -> str:
    """Corregir caracteres corruptos comunes por encoding."""
    replacements = {
        "Art\u0081culos": "Art\u00edculos",
        "Art\u0080culos": "Art\u00edculos",
        "Artculos": "Art\u00edculos",
        "C\u0082mo": "C\u00f3mo",
        "C\u0080mo": "C\u00f3mo",
        "Cmo": "C\u00f3mo",
        "Gu\u0082a": "Gu\u00eda",
        "gu\u0082a": "gu\u00eda",
        "Gu\u0080a": "Gu\u00eda",
        "Gu\u00eda": "Gu\u00eda",  # ya correcto, no-op
        "n\u00ba": "n.\u00ba",
    }
    for wrong, right in replacements.items():
        if wrong != right:
            html = html.replace(wrong, right)
    return html


def add_logo_style(html: str) -> str:
    """Agregar estilo para .logo manteniendo el mismo visual que h1."""
    if '<span class="logo">' in html and '.logo {' not in html:
        # Extender los selectores existentes del header h1
        html = html.replace(
            '.header-inner h1 {',
            '.header-inner h1, .header-inner .logo {'
        )
        html = html.replace(
            '.header-inner h1 a {',
            '.header-inner h1 a, .header-inner .logo a {'
        )
    return html


# ─── Main ──────────────────────────────────────────────────────────────


def process_file(filepath: str) -> dict:
    """Procesar un archivo HTML y aplicar todos los fixes."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()

    original = html

    html = fix_share_buttons(html)
    html = fix_nav_links(html)
    html = fix_h1_duplicate(html)
    html = add_missing_meta_tags(html)
    html = fix_encoding(html)
    html = add_logo_style(html)

    changed = html != original

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

    return {
        'file': os.path.basename(filepath),
        'changed': changed,
    }


def main():
    print("=" * 55)
    print("  SEO Fix Script - Plata Hoy")
    print("=" * 55)
    print()

    if not os.path.isdir(ARTICLES_DIR):
        print(f"ERROR: No se encontro el directorio '{ARTICLES_DIR}/'")
        print("Ejecuta este script desde la raiz de tu proyecto.")
        return

    html_files = sorted(
        f for f in os.listdir(ARTICLES_DIR)
        if f.endswith('.html')
    )

    if not html_files:
        print(f"No se encontraron archivos .html en '{ARTICLES_DIR}/'")
        return

    print(f"Archivos a procesar: {len(html_files)}")
    print()

    # Backup
    if os.path.exists(BACKUP_DIR):
        print(f"Backup ya existe en '{BACKUP_DIR}/' (no se sobrescribe)")
    else:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        for f in html_files:
            shutil.copy2(os.path.join(ARTICLES_DIR, f), os.path.join(BACKUP_DIR, f))
        print(f"Backup creado: {BACKUP_DIR}/ ({len(html_files)} archivos)")

    print()
    print("-" * 55)
    print(f"  {'Archivo':<42} {'Estado'}")
    print("-" * 55)

    changed_count = 0
    for filename in html_files:
        filepath = os.path.join(ARTICLES_DIR, filename)
        result = process_file(filepath)
        status = "MODIFICADO" if result['changed'] else "OK"
        if result['changed']:
            changed_count += 1
        print(f"  {filename:<42} {status}")

    print("-" * 55)
    print()
    print(f"Total: {changed_count}/{len(html_files)} archivos modificados")
    print()
    print("Fixes aplicados:")
    print("  1. Share buttons: URLs sin .html")
    print("  2. Nav links: URLs sin .html")
    print("  3. H1 duplicado: logo cambiado a <span>")
    print("  4. Meta tags: og:url, og:locale, og:site_name")
    print("  5. Twitter Cards agregadas")
    print("  6. Encoding corregido")
    print("  7. Estilo .logo agregado")
    print()
    print(f"Si algo sale mal, restaura desde {BACKUP_DIR}/")


if __name__ == '__main__':
    main()