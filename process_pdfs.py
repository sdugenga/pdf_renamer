import argparse
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter

def main():
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='PDF file(s) to process'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None
    )

    args = parser.parse_args()

    pdf_files = expand_input_paths(args.files)

    if not pdf_files:
        print("No PDF files found.")
        return
    
    if args.output:
        output_dir = args.output
    else:
        output_dir = pdf_files[0].parent / 'processed_pdfs'

    output_dir.mkdir(exist_ok=True)
    
    # process each file
    failed_files = []
    success_count = 0
    for pdf_file in pdf_files:
        if not pdf_file.exists():
            print(f"File not found: {pdf_file}")
            continue
        print(f"Processing: {pdf_file.name}")
        try:
            process_single_pdf(pdf_file, output_dir)
            success_count += 1
        except Exception as e:
            failed_files.append((pdf_file, str(e)))

    print(f"\n{'='*50}")
    print(f"Completed: {success_count}/{len(pdf_files)} files processed")

    if failed_files:
        print(f"\nFailed files:")
        for file, error in failed_files:
            print(f"{file}: {error}")


def process_single_pdf(pdf_path, output_dir):
    # Open the pdf
    reader = PdfReader(pdf_path)
    
    try:
        # Point to the first page
        first_page = reader.pages[0]
        # Extract the text
        text = first_page.extract_text()
    except Exception:
        raise RuntimeError("Failed while extracting text from PDF")

    try:
        note_num, level_num = extract_note_and_level(text)
    except Exception as e:
        print(f"    Could not extract note/level: {e}")
        note_num, level_num = None, None

    try:
        title = extract_title(first_page)
    except Exception as e:
        print(f"  Could not extract title: {e}")
        title = None

    if not note_num or not level_num or not title:
        note_num, level_num, title = get_manual_input(pdf_path)

        if not note_num:
            return False

    try:
        filename = generate_filename(note_num, level_num, title)
        doc_title = generate_doc_title(note_num, level_num, title)
        output_path = output_dir / filename
        save_pdf_with_metadata(reader, output_path, doc_title)
    except Exception:
        raise RuntimeError("Failed while generating or saving output PDF")


def get_manual_input(pdf_path):
    print(f"\n{'='*50}")
    print(f"Could not auto-extract from: {pdf_path.name}")
    print(f"{'='*50}")
    
    response = input("Enter values manually? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Skipping file...")
        return None, None, None
    
    note_num = input("Note number: ").strip()
    level_num = input("Level number: ").strip()
    title = input("Title: ").strip()
    
    if not note_num or not level_num or not title:
        print("Invalid input. Skipping file...")
        return None, None, None
    
    return note_num, level_num, title


def expand_input_paths(paths):
    expanded_files = []
    
    for path in paths:
        path_str = str(path)
        # if it's an existing file
        if path.is_file():
            expanded_files.append(path)
        # if it's an existing directory
        if path.is_dir():
            expanded_files.extend(path.glob("*.pdf"))
        # otherwise treat it as a glob pattern
        elif '*' in path_str or '?' in path_str:
            # It's a glob pattern
            # Split into parent directory and pattern
            parent = path.parent
            pattern = path.name
            
            # If parent doesn't exist, try from current directory
            if not parent.exists():
                parent = Path('.')
            
            matches = list(parent.glob(pattern))
            if matches:
                expanded_files.extend(matches)
            else:
                print(f"No matches found for: {path}")
        
        else:
            # Path doesn't exist and isn't a pattern
            print(f"Warning: {path} not found (skipping)")
    
    return expanded_files


def extract_note_and_level(text):
    # search for the note number and level
    note_num_level = re.search(r"[Nn]ote\s+(\d\d?)\s+[Ll]evel\s+(\d\d?)", text)
    if not note_num_level:
        raise RuntimeError("Could not find 'Note X Level Y' pattern")
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