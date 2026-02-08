import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

def main():
    # not 100% on what this does at the moment or why I would use it
    path = Path("samples/test_1.pdf")

    # make sure it exists
    if not path.exists():
        print("File not found")
        return
    
    # open the file with pypdf
    reader = PdfReader(path)
    first_page = reader.pages[0]

    # STEP 1: Get the note number and level
    # get the first page and extract the text
    text = first_page.extract_text()

    # search for the note number and level
    note_num_level = re.search(r"[Nn]ote (\d\d?) [Ll]evel (\d\d?)", text)

    # assign the numbers to variables and strip any whitespace
    note_num, level_num = note_num_level.group(1, 2)
    note_num = note_num.strip()
    level_num = level_num.strip()

    # print it out
    if note_num_level:
        print(f"Extracted note number and level: {note_num_level.group(0)}")
        print(f"Note number: {note_num}")
        print(f"Level number: {level_num}")
    else:
        print("not found")

    # STEP 2: Extract title by font size
    # create a list to store text with sizes
    text_with_sizes = []

    def visitor_collect_fonts(text, cm, tm, font_dict, font_size):
        if text.strip(): # check if there is text
            actual_size = font_size * (tm[0] + tm[3]) / 2  # Average of x and y scaling
            text_with_sizes.append({
                'text': text.strip(),
                'size': actual_size
            })

    # get the text and font info?
    first_page.extract_text(visitor_text=visitor_collect_fonts)

    # Debug: print what we collected
    print(f"\nCollected {len(text_with_sizes)} text fragments")

    if text_with_sizes:
            max_size = max(item['size'] for item in text_with_sizes)

            title_fragments = [item['text'] for item in text_with_sizes 
                            if item['size'] == max_size]
            
            title = "_".join(title_fragments)
            title = title.replace(" ", "_")
            title = unicodedata.normalize("NFKC", title)
            print(f"Title: {title}")
    else:
         print("No text with size information found")


if __name__ == "__main__":
    main()
