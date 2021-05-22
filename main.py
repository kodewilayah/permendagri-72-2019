# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Permendagri 75/2019 data structured data extraction
# 
# Permendagri 75/2019 is a ministerial decree that  the latest edition (as of 2021) of Indonesia's administrative region codes.
# 
# The raw dataset is a single 27MB PDF which consists of:
# * The ministerial decree itself
# * An appendix which contains the region codes (this is where the data will be extracted from)

# %%
# Set the path
input_path = './raw.pdf'
output_path = './dist.csv'

# %% [markdown]
# ## Finding relevant tables from the appendix
# 
# The appendix is split into provinces. For each province has pages for:
# 1. Kabupaten-level summary
# 2. Details up to each desa, including deprecations
# 3. Kecamatan-level summary
# 
# We are only interested in (2). We need to find the ranges of pages which contain these relevant tables.
# 
# To do this, we will use `pdftotext`.

# %%
import pdftotext

def find_relevant_pages(path_to_pdf):
    with open(path_to_pdf, 'rb') as f:
        pdf = pdftotext.PDF(f)

        i = 1
        ranges = []
        temp = 0

        for page in pdf:
            if 'b. Kode Dan Data Wilayah Administrasi' in page:
                temp = i
            elif 'c. Rekapitulasi' in page and temp != 0:
                ranges.append(range(temp, i))

            i += 1

        return ranges

# %% [markdown]
# Let's call this function:

# %%
relevant_ranges = find_relevant_pages(input_path)

# %% [markdown]
# ## Converting tables into DataFrames
# 
# We use `tabula` to extract tables from all relevant pages into DataFrames.

# %%
from tabula import read_pdf

AREA_HEAD = [142, 36, 568, 602]
AREA_TAIL = [90, 35, 568, 601]

def extract_tables(input_path, pages):
    pages = list(pages)
    page_head = pages[0]
    pages_tail = pages[1:]


    tabula_args = {
        'silent': True,
        'lattice': True,
        'pandas_options': {
            'header': None,
            'dtype': 'string' # empty cells will be pandas.NA
        },
    }

    # The first frame uses a different area than the rest
    head_frames = read_pdf(input_path,
                           area=AREA_HEAD,
                           pages=[page_head],
                           **tabula_args)

    tail_frames = read_pdf(input_path,
                           area=AREA_TAIL,
                           pages=pages_tail,
                           **tabula_args)

    return head_frames + tail_frames


# %%
relevant_pages = []

for relevant_range in relevant_ranges:
    relevant_pages.extend(list(relevant_range))


# %%
frames = extract_tables(input_path, relevant_pages)

# %% [markdown]
# ## Processing each DataFrame
# 
# From each DataFrame, we can scrape the Code and a Raw Name. This Raw Name will be sanitised later.

# %%
from pandas import isna
import re

def is_code(txt):
    return re.match('^[0-9]{2}(\.[0-9]{2}(\.[0-9]{2}(\.[1-2][0-9]{3})?)?)?$', str(txt))

def parse_frame(frame):
    output = []

    # parse each row in the dataframe as a list    
    for row in frame.values:
        cells = [cell for cell in list(row) if not isna(cell)]
        if len(cells) >= 2 and is_code(cells[0]) and type(cells[1]) == str:
            code = cells[0]
            raw_name = cells[1]
            output.append((code, raw_name))


    return output

# %% [markdown]
# Let's parse all of the dataframes.

# %%
code_to_raw_name = []

for frame in frames:
    tuples = parse_frame(frame)
    code_to_raw_name.extend(tuples)

# %% [markdown]
# Let's see what we come up with.

# %%
print(len(code_to_raw_name))

# %% [markdown]
# ## Sanitising names
# 
# Two things to sanitise:
# 
# 1. An ordinal number prefixing the name – but some regions have actual numbers in the beginning of their names!
# 2. Carriage returns (`\r`) in the middle of a names
# 3. Unnecessary in-padded strings such as `P A P U A`

# %%
counter_kec = 0
counter_kel = 0
counter_des = 0

def parse_code(code):
    global counter_kec, counter_kel, counter_des
    if len(code) == 2: # provinsi
        counter_kec = 0
        counter_kel = 0
        counter_des = 0
        return '', 'provinsi'
    elif len(code) == 5: # kab/kota
        counter_kec = 0
        counter_kel = 0
        counter_des = 0
        return '', 'kabkota'
    elif len(code) == 8: # kecamatan
        counter_kec += 1
        counter_kel = 0
        counter_des = 0
        return str(counter_kec), 'kecamatan'
    elif len(code) == 13:
        if code[9] == '1': # kelurahan
            counter_kel += 1
            return str(counter_kel), 'kelurahan'
        elif code[9] == '2':
            counter_des += 1
            return str(counter_des), 'desa'


# %%
import re
csv_output = []

for row in code_to_raw_name:
    code, raw_name = row
    code = str(code)
    ctr, ctx = parse_code(code)
    name = raw_name

    if ctx == 'provinsi':
        name = raw_name.replace('\r', '')
    elif ctx == 'kabkota':
        name = raw_name.replace('\r', '')
        name = re.sub('[0-9]+', '', name)
        name = name.strip()
    elif re.search('\r' + ctr, raw_name):
        name = re.sub('\r(' + ctr + ')?', '', name)
    else:
        name = re.sub('^[0-9]+\s+', '', name)
        name = name.replace('\r', '')

    # sanitise cases like `P A P U A`
    if re.search('^([A-Za-z] )+[A-Za-z]$', name):
        name = re.sub('\s', '', name)

    # sanitise " which should be '
    name = name.replace('"', "'")

    csv_output.append((code, name, raw_name))


# %%
print(repr(csv_output[67536]))

# %% [markdown]
# ## Dump results to csv

# %%
import csv

with open(output_path, 'w') as f:
    writer = csv.writer(f)
    for row in csv_output:
        a, b, _ = row
        writer.writerow([a, b])

# %% [markdown]
# # Utilities
# %% [markdown]
# ## Find the area parameter for running tabula. Values are from Preview.

# %%
left = 35
top = 90
width = 566
height = 478

y1 = top
x1 = left
y2 = top + height
x2 = left + width

coordinates = [y1,x1,y2,x2]

print(coordinates)


