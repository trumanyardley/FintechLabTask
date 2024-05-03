import os
from sec_edgar_downloader import Downloader
import anthropic
from bs4 import BeautifulSoup
import re
import pandas as pd

ANTHROPIC_API_KEY = "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"

# Initialize anthropic client
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=ANTHROPIC_API_KEY,
)

# Initialize downloader, download files to local Docs folder
dl = Downloader("Personal", "truman.yardley@gmail.com", "Docs/")

# Download 10-K files for Apple, Google, and Microsoft from 1995 to 2023
dl.get("10-K", "AAPL", after="1995-01-01", before="2024-01-01")
dl.get("10-K", "GOOG", after="1995-01-01", before="2024-01-01")
dl.get("10-K", "MSFT", after="1995-01-01", before="2024-01-01")

# Dictionary of the tickers and their latest 10K filing for 2023
ticker_to_file_path = {
    "AAPL": "Docs/sec-edgar-filings/AAPL/10-K/0000320193-23-000106/full-submission.txt",
    "GOOG": "Docs/sec-edgar-filings/GOOG/10-K/0001652044-23-000016/full-submission.txt",
    "MSFT": "Docs/sec-edgar-filings/MSFT/10-K/0000950170-23-035122/full-submission.txt",
}

# Which ticker's we will study
ticker = "AAPL"

# Get text of 2023 10K submission
file_path = ticker_to_file_path[ticker]
with open(file_path, "r") as file:
    raw_text = file.read()

########### PARSING INFORMATION FOR SECTIONS 1A, 7, and 7A ##############

# Useful 10K information is contained within Document tags
### Regex to find <DOCUMENT> tags
doc_start_pattern = re.compile(r"<DOCUMENT>")
doc_end_pattern = re.compile(r"</DOCUMENT>")
### Regex to find <TYPE> tag prceeding any characters, terminating at new line
type_pattern = re.compile(r"<TYPE>[^\n]+")

# Create 3 lists with the span idices for each regex

### There are many <Document> Tags in this text file, each as specific exhibit like 10-K, EX-10.17 etc
### First filter will give us document tag start <end> and document tag end's <start>
### We will use this to later grab content in between these tags
doc_start_is = [x.end() for x in doc_start_pattern.finditer(raw_text)]
doc_end_is = [x.start() for x in doc_end_pattern.finditer(raw_text)]

### Type filter is interesting, it looks for <TYPE> with Not flag as new line, ie terminare there, with + sign
### to look for any char afterwards until new line \n. This will give us <TYPE> followed Section Name like '10-K'
### Once we have have this, it returns String Array, below line will with find content after <TYPE> ie, '10-K'
### as section names
doc_types = [x[len("<TYPE>") :] for x in type_pattern.findall(raw_text)]


# Create a dictionary, '10-K' as the key and the value as contents of the 10-K section
document = {}

# Create a loop to go through each section type and save only the 10-K section in the dictionary
for doc_type, doc_start, doc_end in zip(doc_types, doc_start_is, doc_end_is):
    if doc_type == "10-K":
        document[doc_type] = raw_text[doc_start:doc_end]

# Write the regex, find items in the document
regex = re.compile(r"(>(Item|ITEM)(\s|&#160;|&nbsp;)(1A|1B|7A|7|8)\.{0,1})")

# Use finditer to math the regex
matches = regex.finditer(document["10-K"])

# Write a for loop to print the matches
for match in matches:
    print(match)

# Matches
matches = regex.finditer(document["10-K"])

# Remove double matches
# Create the dataframe
test_df = pd.DataFrame([(x.group(), x.start(), x.end()) for x in matches])

test_df.columns = ["item", "start", "end"]
test_df["item"] = test_df.item.str.lower()

# Display the dataframe
print(test_df.head())

# Get rid of unnesesary charcters from the dataframe
test_df.replace("&#160;", " ", regex=True, inplace=True)
test_df.replace("&nbsp;", " ", regex=True, inplace=True)
test_df.replace(" ", "", regex=True, inplace=True)
test_df.replace("\\.", "", regex=True, inplace=True)
test_df.replace(">", "", regex=True, inplace=True)

# display the dataframe
print(test_df.head())

# Drop duplicates
pos_dat = test_df.sort_values("start", ascending=True).drop_duplicates(
    subset=["item"], keep="last"
)

# Display the dataframe
print(pos_dat)

# Set item as the dataframe index
pos_dat.set_index("item", inplace=True)

# display the dataframe
print(pos_dat)

# Get Item 1a
item_1a_raw = document["10-K"][
    pos_dat["start"].loc["item1a"] : pos_dat["start"].loc["item1b"]
]

# Get Item 7
item_7_raw = document["10-K"][
    pos_dat["start"].loc["item7"] : pos_dat["start"].loc["item7a"]
]

# Get Item 7a
item_7a_raw = document["10-K"][
    pos_dat["start"].loc["item7a"] : pos_dat["start"].loc["item8"]
]

# Apply beautofulsoup to refine content because it's still in html and xml
item_1a_content = BeautifulSoup(item_1a_raw, "lxml")
item_7_content = BeautifulSoup(item_7_raw, "lxml")
item_7a_content = BeautifulSoup(item_7a_raw, "lxml")

print(item_7a_content.get_text())

print(len(item_1a_content.get_text()))
print(len(item_7_content.get_text()))
print(len(item_7a_content.get_text()))

# Combine all the documents content from sections into one string
combined_content = (
    item_1a_content.get_text()
    + "\n"
    + item_7_content.get_text()
    + "\n"
    + item_7a_content.get_text()
)

# Claude prompt to generate insights
prompt = """
Analyze the following excerpt from a company's 10K annual report filing, which includes the "Risk Factors," "Management's Discussion and Analysis of Financial Condition and Results of Operations," and "Quantitative and Qualitative Disclosures about Market Risk" sections:

<report>
{}
</report>

Provide a concise summary and analysis of the key information, focusing on the following:

1. Risk Factors:
   - Identify the most significant risks mentioned, categorizing them as economy-wide, industry-specific, or company-specific.
   - Briefly explain each risk and its potential impact on the company.

2. Management's Discussion and Analysis (MD&A):
   - Summarize the company's perspective on its business results for the past financial year.
   - Identify key factors that influenced the company's performance, such as revenue drivers, expenses, or market conditions.
   - Discuss any significant changes in the company's financial condition or operations.

3. Market Risk Exposures:
   - List the main types of market risks the company is exposed to (e.g., interest rate risk, foreign currency exchange risk, commodity price risk, or equity price risk).
   - Summarize how the company manages these risks, if mentioned.

For each section, provide a concise summary followed by relevant details and analysis. Use the following format for your response:

1. Risk Factors:
   - [Summary]
   - [Economy-wide Risks]
   - [Industry-Specific Risks]
   - [Company-Specific Risks]

2. Management's Discussion and Analysis (MD&A):
   - [Summary]
   - [Key Factors Influencing Performance]
   - [Changes in Financial Condition or Operations]

3. Market Risk Exposures:
   - [Summary]
   - [Types of Market Risks]
   - [Risk Management Strategies (if mentioned)]
""".format(combined_content)

# Ask claude to generate insights based on 10K document information
# message = client.messages.create(
#     model="claude-3-opus-20240229",
#     max_tokens=2000,
#     temperature=0,
#     messages=[
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": prompt
#                 }
#             ],
#         }
#     ],
# )

# Print claude response
# print(message.content[0].text)
