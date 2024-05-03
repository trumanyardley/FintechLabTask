from sec_api import XbrlApi
import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

API_KEY = "f9e5178b13db13f31034b3f8364bf2a0590789a48df65c4ae03fda8376bc0f48"

xbrlApi = XbrlApi(API_KEY)


# convert XBRL-JSON of income statement to pandas dataframe
def get_income_statement(xbrl_json):
    income_statement_store = {}

    # iterate over each US GAAP item in the income statement
    for usGaapItem in xbrl_json["StatementsOfIncome"]:
        values = []
        indicies = []

        for fact in xbrl_json["StatementsOfIncome"][usGaapItem]:
            # only consider items without segment. not required for our analysis.
            if "segment" not in fact:
                index = fact["period"]["startDate"] + "-" + fact["period"]["endDate"]
                # ensure no index duplicates are created
                if index not in indicies:
                    values.append(fact["value"])
                    indicies.append(index)

        income_statement_store[usGaapItem] = pd.Series(values, index=indicies)

    income_statement = pd.DataFrame(income_statement_store)
    # switch columns and rows so that US GAAP items are rows and each column header represents a date range
    return income_statement.T


# Dictionary of the tickers and json file containing urls to 10Ks for sec-api visualization use
ticker_to_json_path = {
    "AAPL": "Docs/sec-edgar-filings/AAPL/apple_10k_urls.json",
    "GOOG": "Docs/sec-edgar-filings/AAPL/google_10k_urls.json",
    "MSFT": "Docs/sec-edgar-filings/AAPL/microsoft_10k_urls.json",
}

ticker = "AAPL"

file_path = ticker_to_json_path[ticker]

income_statements_list = []

all_revenues_json = []

# Open json containing links to Apple 10K files
with open(file_path) as f:
    apple_10k_urls = json.load(f)

# Process the xbrl_json data for the given year
for year, url in apple_10k_urls.items():
    xbrl_json = xbrlApi.xbrl_to_json(htm_url=url)
    income_statement = get_income_statement(xbrl_json)
    income_statements_list.append(income_statement)
    revenue_json = xbrl_json["StatementsOfIncome"][
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ]
    all_revenues_json = all_revenues_json + revenue_json

# Reevnues of all years
all_revenues = pd.json_normalize(all_revenues_json)

income_statements_merged = pd.concat(income_statements_list)

# sort & reset the index of the merged dataframe
income_statements_merged = income_statements_merged.sort_index().reset_index()

# convert cells to float
income_statements_merged = income_statements_merged.applymap(
    lambda x: pd.to_numeric(x, errors="ignore")
)

print("Merged, uncleaned financials of all income statements")
print("-----------------------------------------------------")
print(income_statements_merged.head(10))

income_statements = income_statements_merged.groupby("index").max()

# Reindex the merged dataframe using the index of the first dataframe
income_statements = income_statements.reindex(income_statements_list[0].index)

# loop over the columns
for col in income_statements.columns[1:]:
    # extract start and end dates from the column label
    splitted = col.split("-")
    start = "-".join(splitted[:3])
    end = "-".join(splitted[3:])

    # convert start and end dates to datetime objects
    start_date = pd.to_datetime(start)
    end_date = pd.to_datetime(end)

    # calculate the duration between start and end dates
    duration = (end_date - start_date).days / 360

    # drop the column if duration is less than a year
    if duration < 1:
        income_statements.drop(columns=[col], inplace=True)

# convert datatype of cells to readable format, e.g. "2.235460e+11" becomes "223546000000"
income_statements = income_statements.apply(
    lambda row: pd.to_numeric(row, errors="coerce", downcast="integer").astype(str),
    axis=1,
)

print("Income statements from Apple's 10-K filings (2016 to 2022) as dataframe")
print("------------------------------------------------------------------------")
print(income_statements)


all_revenues.drop_duplicates(inplace=True)
# convert the 'value' column to a numeric type
all_revenues["value"] = all_revenues["value"].astype(int)

mask_iphone = all_revenues["segment.value"] == "aapl:IPhoneMember"
mask_ipad = all_revenues["segment.value"] == "aapl:IPadMember"
mask_mac = all_revenues["segment.value"] == "aapl:MacMember"
mask_wearables = (
    all_revenues["segment.value"] == "aapl:WearablesHomeandAccessoriesMember"
)

revenue_product = all_revenues[(mask_iphone | mask_ipad | mask_mac | mask_wearables)]

# pivot the dataframe to create a new dataframe with period.endDate as the index,
# segment.value as the columns, and value as the values
revenue_product_pivot = revenue_product.pivot(
    index="period.endDate", columns="segment.value", values="value"
)

print("Apple's revenues by product from 2017 to 2022")
print("---------------------------------------------")
print(revenue_product_pivot)

# plot the histogram bar chart
ax = revenue_product_pivot.plot(kind="bar", stacked=True, figsize=(8, 6))

# rotate the x-axis labels by 0 degrees
plt.xticks(rotation=0)

# set the title and labels for the chart
ax.set_title("Apple's Revenue by Product Category", fontsize=16, fontweight="bold")
ax.set_xlabel("Period End Date", fontsize=12)
ax.set_ylabel("Revenue (USD)", fontsize=12)

# set the legend properties
ax.legend(
    title="Product Category", loc="upper left", fontsize="small", title_fontsize=10
)

# add gridlines
ax.grid(axis="y", linestyle="--", alpha=0.3)

# remove the top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# format y-axis ticks to show values in millions in dollars
formatter = ticker.FuncFormatter(lambda x, pos: "$%1.0fB" % (x * 1e-9))
plt.gca().yaxis.set_major_formatter(formatter)

# map the original labels to new labels
label_map = {
    "aapl:IPhoneMember": "iPhone",
    "aapl:MacMember": "Mac",
    "aapl:IPadMember": "iPad",
    "aapl:WearablesHomeandAccessoriesMember": "Wearables & Home",
}

# create a list of new labels based on the original labels
new_labels = [
    label_map[label]
    for label in sorted(pd.Series(revenue_product["segment.value"]).unique())
]
handles, _ = ax.get_legend_handles_labels()
plt.legend(handles=handles[::-1], labels=new_labels[::-1])

# add the values in billions of dollars to each part of the bar
for p in ax.containers:
    ax.bar_label(
        p,
        labels=["%.1f" % (v / 1e9) for v in p.datavalues],
        label_type="center",
        fontsize=8,
    )

plt.show()
