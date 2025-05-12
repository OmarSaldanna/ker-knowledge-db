import fitz  # PyMuPDF for working with PDFs
import json  # For saving JSON data
import re  # For regex operations
from collections import Counter, defaultdict  # For counting and grouping
import tiktoken  # Token counter


# Step 5: Detect if a string contains a URL
def detect_link(string):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F]{2}))+'
    return bool(re.search(url_pattern, string))


# Step 6: Remove chapters that are empty or too short, and add a "links" attribute
def filter_and_mark_links(chapters):
    final = []
    for ch in chapters:
        content = ch["content"].strip()
        if content == "" or len(content) < 100:
            continue  # Skip empty or too short chapters
        ch["links"] = detect_link(ch["content"]) or detect_link(ch["title"])
        final.append(ch)
    return final


# Function to count tokens in a text
def count_tokens(text):
    # Load encoder for the model
    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    # Return number of tokens in the encoded text
    return len(encoding.encode(text))
    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    # https://platform.openai.com/tokenizer


# Function to split a chapter by token count
def split_by_tokens(chapter, max_tokens=1000):
    # Get chapter content
    content = chapter["content"]
    # Split by sentence endings
    sentence_split = re.split(r'(?<=\.)\s+', content)

    # Temporary holders
    parts = []
    temp = ""
    tokenized_parts = []

    # Build token-limited segments
    for sentence in sentence_split:
        if count_tokens(temp + " " + sentence) <= max_tokens:
            temp += " " + sentence
        else:
            tokenized_parts.append(temp.strip())
            temp = sentence
    if temp.strip():
        tokenized_parts.append(temp.strip())

    # Create new chapters with updated titles and content
    result = []
    for idx, text in enumerate(tokenized_parts):
        new_chapter = chapter.copy()
        new_chapter["title"] = f"{chapter['title']} - part {idx + 1}"
        new_chapter["content"] = text
        result.append(new_chapter)
    return result


# Function to split long chapters
def split_long_chapters(chapters, max_tokens=1000):
    split_result = []
    for ch in chapters:
        total_tokens = count_tokens(ch["content"])
        if total_tokens > max_tokens:
            parts = split_by_tokens(ch, max_tokens)
            split_result.extend(parts)
        else:
            split_result.append(ch)
    return split_result


# Function to clean and merge chapters
def process_chapters(chapters):
    # Remove chapters without titles
    chapters = [ch for ch in chapters if ch["title"].strip() != ""]

    # Get average content length
    contents = [ch["content"].strip() for ch in chapters if ch["content"].strip()]
    avg_length = sum(len(c) for c in contents) / len(contents) if contents else 0

    # Merge short consecutive chapters with the same title level
    merged = []
    i = 0
    while i < len(chapters):
        current = chapters[i].copy()
        curr_len = len(current["content"].strip())

        if curr_len < avg_length:
            j = i + 1
            while (
                j < len(chapters)
                and chapters[j]["ntitle"] == current["ntitle"]
                and len(chapters[j]["content"].strip()) < avg_length
            ):
                next_ch = chapters[j]
                current["content"] += " " + next_ch["title"].strip()
                current["pages"][0] = min(current["pages"][0], next_ch["pages"][0])
                current["pages"][1] = max(current["pages"][1], next_ch["pages"][1])
                j += 1
            merged.append(current)
            i = j
        else:
            merged.append(current)
            i += 1

    return merged


# Function to check if a title is valid
def is_valid_title(text):
    # Returns True if title has at least one alphanumeric character
    return bool(re.search(r'\w', text))


# Main function to analyze PDF
def analyze (pdf_path, json_output=None):
    # Open the PDF
    doc = fitz.open(pdf_path)
    font_sizes = []

    # Collect all font sizes
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])

    # Get the most common font size (body text)
    font_counter = Counter(font_sizes)
    most_common_size = font_counter.most_common(1)[0][0]

    # Extract and segment chapters based on font size
    result = []
    current_chapter = None

    for page_number, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    size = span["size"]

                    # If font is larger than body text, it's a title
                    if size > most_common_size:
                        if current_chapter:
                            current_chapter["pages"][1] = page_number
                            result.append(current_chapter)

                        ntitle = int(round(size - most_common_size))
                        current_chapter = {
                            "title": text,
                            "content": "",
                            "ntitle": ntitle,
                            "pages": [page_number, page_number]
                        }
                    else:
                        # Add content to current chapter
                        if current_chapter:
                            current_chapter["content"] += text + " "

    # Add the last chapter
    if current_chapter:
        result.append(current_chapter)

    # Remove invalid chapters
    result = [ch for ch in result if is_valid_title(ch["title"]) or ch["content"].strip()]

    # Group empty content chapters with same title level
    grouped = []
    empty_by_ntitle = defaultdict(list)

    for ch in result:
        if not ch["content"].strip():
            empty_by_ntitle[ch["ntitle"]].append(ch)
        else:
            grouped.append(ch)

    for ntitle, chs in empty_by_ntitle.items():
        if len(chs) > 1:
            pages = [p for c in chs for p in c["pages"]]
            new_ch = {
                "title": "",
                "content": " ".join([c["title"] for c in chs]),
                "ntitle": ntitle,
                "pages": [min(pages), max(pages)]
            }
            grouped.append(new_ch)
        else:
            grouped.append(chs[0])

    # Merge empty chapters with next if same level
    final_chapters = []
    i = 0
    while i < len(grouped):
        current = grouped[i]
        if not current["content"].strip() and i + 1 < len(grouped):
            next_ch = grouped[i + 1]
            if current["ntitle"] == next_ch["ntitle"]:
                next_ch["title"] = current["title"].strip() + " " + next_ch["title"].strip()
                next_ch["pages"][0] = min(current["pages"][0], next_ch["pages"][0])
                i += 1
                continue
        final_chapters.append(current)
        i += 1

    # Further processing: clean and merge
    final_chapters = process_chapters(final_chapters)

    # Split large chapters
    final_chapters = split_long_chapters(final_chapters, max_tokens=800)

    # Also check links and remove trash chapters
    final_chapters = filter_and_mark_links(final_chapters)

    # Save as JSON if it was required
    if json_output:
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(final_chapters, f, indent=4, ensure_ascii=False)

    # And return
    return final_chapters


# Example usage
# analyze ("libro-emociones.pdf", "chapters.json")
# pip install PyMuPDF tiktoken