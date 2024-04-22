from sec_edgar_downloader import Downloader

# Initialize downloader, download files to local Docs folder
dl = Downloader("Personal", "truman.yardley@gmail.com", "Docs/")

# Download 10-K files for Apple, Google, and Microsoft from 1995 to 2023
dl.get("10-K", "AAPL", after="1995-01-01", before="2023-01-01")
dl.get("10-K", "GOOG", after="1995-01-01", before="2023-01-01")
dl.get("10-K", "MSFT", after="1995-01-01", before="2023-01-01")
