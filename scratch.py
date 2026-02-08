import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter

def main():
    path = Path("samples/test.pdf")
    output_dir = Path("samples/processed")
    # Create the folder if it doesn't exist
    output_dir.mkdir(exist_ok=True)

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

    # DEBUG to get print out of level and number
    '''
    # print it out
    if note_num_level:
        print(f"Extracted note number and level: {note_num_level.group(0)}")
        print(f"Note number: {note_num}")
        print(f"Level number: {level_num}")
    else:
        print("not found")
    '''

    # STEP 2: Extract title by font size
    # create a list to store text with sizes
    text_with_sizes = []

    # ideally this would be moved out of main, but i'm not sure about it
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

    # DEBUG print what we collected
    # print(f"\nCollected {len(text_with_sizes)} text fragments")

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

    new_filename = generate_filename(note_num, level_num, title)
    # DEBUG print(new_filename)
    # TODO This needs it's own function really
    doc_title = f"{note_num.zfill(2)} " + f"{level_num.zfill(2)} " + title.title()
    # DEBUG print(doc_title)

    # STEP 3: Save the pdf!
    output_path = output_dir / new_filename
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


    # TODO write function to generate file name
    # TODO write function to generate file title
    # TODO save renamed, retitled pdf in a subdirectory
    # TODO figure out how to apply it to batches/whole folders
    # TODO break visitor function out into own function
    # TODO sort out main and break out functions where necessary


def generate_filename(note_num, level_num, title):
     filename = f"{note_num.zfill(2)}_" + f"{level_num.zfill(2)}_" + title.lower()
     filename = filename.replace(" ", "_")
     filename = filename + ".pdf"
     return(filename)

if __name__ == "__main__":
    main()
