import re
import json
from pathlib import Path
import tiktoken  # Token counter


# Function to count tokens in a text
def count_tokens(text):
    """
    Returns the number of tokens in `text` using the tiktoken encoder for gpt-4o-mini.
    """
    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    return len(encoding.encode(text))

# Function to split a chapter by token count
def split_by_tokens(chapter, max_tokens=1000):
    """
    Splits `chapter["content"]` into parts each <= max_tokens, breaking at sentence boundaries where possible.
    If a single sentence exceeds max_tokens, it falls back to splitting at word boundaries.
    Returns a list of new chapter dicts with updated titles and content.
    """
    content = chapter["content"]
    # Split on sentence boundaries
    sentences = re.split(r'(?<=\.)\s+', content)

    parts = []
    temp = ""

    for sent in sentences:
        # If current temp+sentence fits, accumulate
        combined = (temp + ' ' + sent).strip()
        if count_tokens(combined) <= max_tokens:
            temp = combined
        else:
            # Flush existing temp
            if temp:
                parts.append(temp)
            # If the sentence itself is too long, split by words
            if count_tokens(sent) > max_tokens:
                words = sent.split()
                seg = ""
                for w in words:
                    if count_tokens((seg + ' ' + w).strip()) <= max_tokens:
                        seg = (seg + ' ' + w).strip()
                    else:
                        parts.append(seg)
                        seg = w
                if seg:
                    parts.append(seg)
                temp = ""
            else:
                # Start new segment with this sentence
                temp = sent
    # Add any remaining text
    if temp:
        parts.append(temp)

    # Create new chapter entries
    result = []
    for idx, text in enumerate(parts):
        new_ch = chapter.copy()
        title_base = chapter.get('title', 'Chapter')
        new_ch['title'] = f"{title_base} - part {idx+1}"
        new_ch['content'] = text
        result.append(new_ch)

    return result

# Recursive function to split long chapters
def split_long_chapters(chapters, max_tokens=1000):
    """
    Recursively splits all chapters in the list so that no chapter's content exceeds max_tokens.
    - chapters: list of dicts, each with at least 'title' and 'content'.
    - max_tokens: integer token limit.

    Returns a new list of chapters all within the token limit.
    """
    split_result = []

    for ch in chapters:
        total = count_tokens(ch['content'])
        if total > max_tokens:
            # print(f"{total} tokens detected in '{ch.get('title', '')}'... splitting...")
            # First-level split
            parts = split_by_tokens(ch, max_tokens)
            # Recursively ensure each part is within the limit
            split_result.extend(split_long_chapters(parts, max_tokens))
        else:
            split_result.append(ch)

    return split_result


def remove_empty_content(list_of_dicts):
    return [
        item for item in list_of_dicts
        if item.get("content", "") != ""
    ]


def analyze (input_file, output_file=None):
    try:
        # Leer el archivo Markdown
        input_path = Path(input_file)
        with open(input_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Preprocesamiento: Eliminar números consecutivos y limpiar tablas
        markdown_content = preprocess_markdown(markdown_content)
        
        # Patrón para detectar encabezados en Markdown (# Título, ## Subtítulo, etc.)
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        # Patrón para detectar enlaces en Markdown
        link_pattern = re.compile(r'\[.+?\]\(.+?\)')
        
        # Encontrar todos los encabezados
        headers = list(header_pattern.finditer(markdown_content))
        
        # Si no hay encabezados, crear uno ficticio para procesar todo el contenido
        if not headers:
            sections = [{
                "title": "Contenido sin título",
                "content": markdown_content.strip(),
                "ntitle": 1,
                "links": bool(link_pattern.search(markdown_content))
            }]
        else:
            # Lista para almacenar las secciones extraídas
            sections = []
            
            # Procesar cada sección (desde un encabezado hasta el siguiente)
            for i, match in enumerate(headers):
                header_mark = match.group(1)
                title = match.group(2).strip()
                start_pos = match.end()
                
                # Si es el último encabezado, el contenido va hasta el final del documento
                if i == len(headers) - 1:
                    content = markdown_content[start_pos:].strip()
                else:
                    # Si no es el último, el contenido va hasta el siguiente encabezado
                    content = markdown_content[start_pos:headers[i+1].start()].strip()
                    
                # Determinar si hay enlaces en el contenido
                has_links = bool(link_pattern.search(content))
                
                # Agregar la sección a la lista de resultados
                sections.append({
                    "title": title,
                    "content": content,
                    "ntitle": len(header_mark),  # Número de # en el encabezado
                    "links": has_links
                })
        
        # split long chapters
        sections = split_long_chapters(sections)
        # and remove empty content chapters
        sections = remove_empty_content(sections)

        # Si se proporciona un archivo de salida, guardar el resultado como JSON
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=4)
            print(f"Procesamiento completado. El resultado se ha guardado en {output_path}")
        
        return sections
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def preprocess_markdown(content):
    """
    Realiza preprocesamiento del contenido Markdown:
    1. Elimina números consecutivos en líneas separadas (incluso cuando están dentro de bloques de código)
    2. Limpia y simplifica tablas Markdown (elimina líneas de separación y exceso de espacios)
    
    Args:
        content (str): Contenido Markdown original
    
    Returns:
        str: Contenido Markdown preprocesado
    """
    # 1. Eliminar secuencias de números dentro de bloques de código
    # Busca patrones como \n1\n2\n3\n... dentro de bloques de código
    number_sequence_pattern = re.compile(r'```[\w]*\n(?:\d+\n)+', re.MULTILINE)
    
    def clean_number_sequence(match):
        code_start = match.group(0).split('\n', 1)[0]  # Preservar la primera línea con ```python
        return f"{code_start}\n"
    
    content = number_sequence_pattern.sub(clean_number_sequence, content)
    
    # 2. Procesar tablas Markdown
    lines = content.split('\n')
    cleaned_lines = []
    in_table = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detectar inicio de tabla (línea que comienza con |)
        if line.strip().startswith('|') and not in_table:
            in_table = True
            # Limpiar la primera línea de la tabla (encabezados)
            cleaned_line = clean_table_line(line)
            cleaned_lines.append(cleaned_line)
            
            # Buscar y omitir la línea de separación (siguiente línea con solo |, - y espacios)
            if i + 1 < len(lines) and re.match(r'^\s*\|[\s\-\|]+\|\s*$', lines[i + 1]):
                i += 1  # Saltar la línea de separación
            
            # Continuar procesando la tabla
            i += 1
            continue
            
        # Si estamos en una tabla y encontramos una línea que no es parte de ella
        elif in_table and not line.strip().startswith('|'):
            in_table = False
        
        # Si estamos en una tabla, limpiar los espacios excesivos
        if in_table:
            cleaned_line = clean_table_line(line)
            cleaned_lines.append(cleaned_line)
        else:
            cleaned_lines.append(line)
        
        i += 1
    
    return '\n'.join(cleaned_lines)

def clean_table_line(line):
    """
    Limpia una línea de tabla eliminando espacios excesivos.
    
    Args:
        line (str): Línea de tabla original
    
    Returns:
        str: Línea limpia
    """
    # Regla específica: eliminar secuencias de más de 5 espacios consecutivos en tablas
    cleaned_line = re.sub(r' {5,}', ' ', line)
    
    # También aplicar otra limpieza para mantener la estructura pero eliminar exceso de espacios
    # Eliminar espacios excesivos entre pipes
    cleaned_line = re.sub(r'\|\s+', '| ', cleaned_line)
    cleaned_line = re.sub(r'\s+\|', ' |', cleaned_line)
    
    return cleaned_line


analyze ("markdowns/Proyecto Final Bases Avanzadas 52f65a2a12764fea957602078be90658.md", "res.json")