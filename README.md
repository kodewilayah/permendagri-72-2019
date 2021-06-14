# kodewilayah/permendagri-72-2019

Scraper & scraping results for Permendagri No. 72/2019. The results are available in [`dist/base.csv`](dist/base.csv), each row containing:

* Region code
* Name as it appears on the Permendagri with minimal sanitisation

## Dependencies

If you're on Windows, using WSL would make installing the dependencies a lot easier. [You can use Visual Studio Code with WSL too for the best development experience.](https://code.visualstudio.com/docs/remote/wsl)

### pdftotext

pdftotext is used for finding relevant pages from the raw PDF file. There are [several dependencies](https://pypi.org/project/pdftotext/) that need to be installed beforehand.

    sudo apt install build-essential libpoppler-cpp-dev pkg-config python3-dev
    pip install pdftotext

### tabula-py

We use [tabula-py](https://pypi.org/project/tabula-py/), which is a wrapper for [tabula-java](https://github.com/tabulapdf/tabula-java).

Java needs to be installed and available from your `PATH`.
