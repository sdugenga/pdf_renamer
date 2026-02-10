import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter

def main():
    # TODO file picking and argument passing here
    # To get to the stage of single file or whole folder
    
    # There will be logic for passing args etc. and then:
    path = Path("samples/test.pdf")
    input_dir = False # For now
    output_dir = Path("samples/processed")
    # Create the folder if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    # make sure it exists
    if not path.exists():
        print("File not found")
        return

    # If it's a single file
    process_single_pdf(path, output_dir)

    # If it's a whole folder
    # process_folder(input_dir, output_dir)


def process_single_pdf(pdf_path, output_dir):
    # Open the pdf
    reader = PdfReader(pdf_path)
    # Point to the first page
    first_page = reader.pages[0]
    # Extract the text
    text = first_page.extract_text()

    note_num, level_num = extract_note_and_level(text)

    title = extract_title(first_page)

    filename = generate_filename(note_num, level_num, title)

    doc_title = generate_doc_title(note_num, level_num, title)

    output_path = output_dir / filename

    save_pdf_with_metadata(reader, output_path, doc_title)


# TODO
def process_folder():
    pass


def extract_note_and_level(text):
    # search for the note number and level
    note_num_level = re.search(r"[Nn]ote (\d\d?) [Ll]evel (\d\d?)", text)
    # assign the numbers to variables and strip any whitespace
    note_num, level_num = note_num_level.group(1, 2)
    note_num = note_num.strip()
    level_num = level_num.strip()
    return(note_num, level_num)


def extract_title(first_page):
    text_with_sizes = []

    def visitor_collect_fonts(text, cm, tm, font_dict, font_size):
        if text.strip(): # check if there is text
            # Average of x and y scaling
            actual_size = font_size * (tm[0] + tm[3]) / 2
            # add text with sizes to list
            text_with_sizes.append({
                'text': text.strip(),
                'size': actual_size
            })
    
    # get the text and font info?
    first_page.extract_text(visitor_text=visitor_collect_fonts)

    # This could definitely be moved out into its own function:
    if text_with_sizes:
            max_size = max(item['size'] for item in text_with_sizes)

            title_fragments = [item['text'] for item in text_with_sizes 
                            if item['size'] == max_size]
            
            title = " ".join(title_fragments)

            # This gets rid of the weird ligament font e.g. fi
            title = unicodedata.normalize("NFKC", title)
            # DEBUG print(f"Title: {title}")
    else:
         print("No text with size information found")

    return(title)


def generate_filename(num, level, title):
    filename = f"{num.zfill(2)}_" + f"{level.zfill(2)}_" + title.lower()
    filename = filename.replace(" ", "_")
    filename = filename + ".pdf"
    return(filename)


def generate_doc_title(num, level, title):
    doc_title = (
        f"{num.zfill(2)} "
        f"{level.zfill(2)} "
        f"{title.title()}"
    )
    return(doc_title)


def save_pdf_with_metadata(reader, output_path, doc_title):
    writer = PdfWriter()

    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)

    # Update metadata (copy existing and modify title)
    metadata = reader.metadata if reader.metadata else {}
    writer.add_metadata({
        **metadata,  # Keep existing metadata
        '/Title': doc_title  # Update title
    })

    # Write to new location
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()