from sec_api import XbrlApi
import pandas as pd
import io
import base64
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

API_KEY = "f9e5178b13db13f31034b3f8364bf2a0590789a48df65c4ae03fda8376bc0f48"
xbrlApi = XbrlApi(API_KEY)
matplotlib.use("Agg")


def generate_plots(tick):
    ticker_to_10k = {
        "AAPL": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
        "GOOG": "https://www.sec.gov/Archives/edgar/data/1652044/000165204423000045/goog-20230331.htm",
    }

    # Link to 10K via SEC EDGAR
    url_10k_2023 = ticker_to_10k[tick]

    xbrl_json_2023 = xbrlApi.xbrl_to_json(htm_url=url_10k_2023)

    all_revenues_json = xbrl_json_2023["StatementsOfIncome"][
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ]

    all_revenues = pd.json_normalize(all_revenues_json)

    if tick == "AAPL":
        # convert the 'value' column to a numeric type
        all_revenues["value"] = all_revenues["value"].astype(int)

        mask_iphone = all_revenues["segment.value"] == "aapl:IPhoneMember"
        mask_ipad = all_revenues["segment.value"] == "aapl:IPadMember"
        mask_mac = all_revenues["segment.value"] == "aapl:MacMember"
        mask_wearables = (
            all_revenues["segment.value"] == "aapl:WearablesHomeandAccessoriesMember"
        )

        revenue_product = all_revenues[
            (mask_iphone | mask_ipad | mask_mac | mask_wearables)
        ]

        # pivot the dataframe to create a new dataframe with period.endDate as the index,
        # segment.value as the columns, and value as the values
        revenue_product_pivot = revenue_product.pivot(
            index="period.endDate", columns="segment.value", values="value"
        )

        # plot the histogram bar chart
        ax = revenue_product_pivot.plot(kind="bar", stacked=True)

        plt.ion()
        # rotate the x-axis labels by 0 degrees
        plt.xticks(rotation=0)

        # set the title and labels for the chart
        ax.set_title(
            "Apple's Revenue by Product Category", fontsize=16, fontweight="bold"
        )
        ax.set_xlabel("Period End Date", fontsize=12)
        ax.set_ylabel("Revenue (USD)", fontsize=12)

        # set the legend properties
        ax.legend(
            title="Product Category",
            loc="upper left",
            fontsize="small",
            title_fontsize=10,
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

        # Convert plot 1 to HTML
        buf1 = io.BytesIO()
        ax.get_figure().savefig(buf1, format="png")
        buf1.seek(0)
        plot1_html = '<img src="data:image/png;base64,{}">'.format(
            base64.b64encode(buf1.read()).decode("utf-8")
        )

        mask_america = all_revenues["segment.value"] == "aapl:AmericasSegmentMember"
        mask_europe = all_revenues["segment.value"] == "aapl:EuropeSegmentMember"
        mask_china = all_revenues["segment.value"] == "aapl:GreaterChinaSegmentMember"
        mask_japan = all_revenues["segment.value"] == "aapl:JapanSegmentMember"
        mask_asia_rest = (
            all_revenues["segment.value"] == "aapl:RestOfAsiaPacificSegmentMember"
        )

        revenue_geo = all_revenues[
            (mask_america | mask_europe | mask_china | mask_japan | mask_asia_rest)
        ]

        # pivot the dataframe to create a new dataframe with period.endDate as the index, segment.value as the columns, and value as the values
        revenue_geo_pivot = revenue_geo.pivot(
            index="period.endDate", columns="segment.value", values="value"
        )

        # plot the histogram bar chart
        ax = revenue_geo_pivot.plot(kind="bar", stacked=True)

        # rotate the x-axis labels by 0 degrees
        plt.xticks(rotation=0)

        # set the title and labels for the chart
        ax.set_title("Apple's Revenue by Region", fontsize=16, fontweight="bold")
        ax.set_xlabel("Period End Date", fontsize=12)
        ax.set_ylabel("Revenue (USD)", fontsize=12)

        # set the legend properties
        ax.legend(title="Region", loc="upper left", fontsize="small", title_fontsize=10)

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
            "aapl:AmericasSegmentMember": "America",
            "aapl:EuropeSegmentMember": "Europe",
            "aapl:GreaterChinaSegmentMember": "China",
            "aapl:JapanSegmentMember": "Japan",
            "aapl:RestOfAsiaPacificSegmentMember": "Rest of Asia",
        }

        # create a list of new labels based on the original labels
        new_labels = [
            label_map[label]
            for label in sorted(pd.Series(revenue_geo["segment.value"]).unique())
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

        # Save plot to html
        buf2 = io.BytesIO()
        ax.get_figure().savefig(buf2, format="png")
        buf2.seek(0)
        plot2_html = '<img src="data:image/png;base64,{}">'.format(
            base64.b64encode(buf2.read()).decode("utf-8")
        )
        return plot1_html, plot2_html

    # Generate plots for Google
    else:
        # explode segment list of dictionaries
        all_revenues = all_revenues.explode("segment")

        segment_split = all_revenues["segment"].apply(pd.Series)
        segment_split = segment_split.rename(
            columns={"dimension": "segment.dimension", "value": "segment.value"}
        )
        segment_split = segment_split.drop(0, axis=1)

        all_revenues = all_revenues.combine_first(segment_split)
        all_revenues = all_revenues.drop("segment", axis=1)
        all_revenues = all_revenues.reset_index(drop=True)

        xbrl_dimensions = all_revenues.pivot(
            columns="segment.dimension", values="segment.value"
        ).dropna(how="all")

        xbrl_dimensions = pd.DataFrame(
            [(col, xbrl_dimensions[col].unique()) for col in xbrl_dimensions.columns],
            columns=["segment.dimension", "segment.values"],
        )

        all_revenues["value"] = all_revenues["value"].astype(int)

        mask = all_revenues["segment.dimension"] == "srt:StatementGeographicalAxis"

        revenue_region = all_revenues[mask]

        # pivot the dataframe to create a new dataframe with period.endDate as the index,
        # segment.value as the columns, and value as the values
        revenue_region_pivot = revenue_region.pivot(
            index="period.endDate", columns="segment.value", values="value"
        )
        # plot the histogram bar chart
        ax = revenue_region_pivot.plot(kind="bar", stacked=True)

        # rotate the x-axis labels by 0 degrees
        plt.xticks(rotation=0)

        # set the title and labels for the chart
        ax.set_title("Google's Revenue by Region", fontsize=16, fontweight="bold")
        ax.set_xlabel("Period End Date", fontsize=12)
        ax.set_ylabel("Revenue (USD)", fontsize=12)

        # set the legend properties
        ax.legend(
            title="Product Category",
            loc="upper left",
            fontsize="small",
            title_fontsize=10,
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
            "country:US": "US",
            "goog:AmericasExcludingUnitedStatesMember": "Americas Excluding US",
            "srt:AsiaPacificMember": "Asia Pacific",
            "us-gaap:EMEAMember": "EMEA",
        }

        # create a list of new labels based on the original labels
        new_labels = [
            label_map[label]
            for label in sorted(pd.Series(revenue_region["segment.value"]).unique())
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

        # Convert plot 1 to HTML
        buf1 = io.BytesIO()
        ax.get_figure().savefig(buf1, format="png")
        buf1.seek(0)
        plot1_html = '<img src="data:image/png;base64,{}">'.format(
            base64.b64encode(buf1.read()).decode("utf-8")
        )

        all_revenues["value"] = all_revenues["value"].astype(int)

        mask_1 = all_revenues["segment.dimension"] == "srt:ProductOrServiceAxis"
        mask_2 = (
            all_revenues["segment.dimension"] == "us-gaap:StatementBusinessSegmentsAxis"
        )

        revenue_product = all_revenues[mask_1 | mask_2]

        # pivot the dataframe to create a new dataframe with period.endDate as the index,
        # segment.value as the columns, and value as the values

        revenue_product = revenue_product.drop_duplicates(
            subset=["period.endDate", "segment.value"]
        )
        revenue_product_pivot = revenue_product.pivot(
            index="period.endDate", columns="segment.value", values="value"
        )

        # merge: goog:GoogleCloudMember + goog:GoogleNetworkMembersPropertiesMember
        revenue_product_pivot["goog:GoogleNetwork"] = revenue_product_pivot[
            "goog:GoogleNetworkMember"
        ]

        revenue_product_pivot = revenue_product_pivot.drop(
            ["goog:GoogleNetworkMember"],
            axis=1,
        )

        revenue_product_pivot = revenue_product_pivot[
            [
                "goog:GoogleSearchOtherMember",
                "goog:YouTubeAdvertisingRevenueMember",
                "goog:GoogleNetwork",
                "goog:GoogleCloudMember",
                "goog:OtherRevenuesMember",
            ]
        ]
        # plot the histogram bar chart
        ax = revenue_product_pivot.plot(kind="bar", stacked=True)

        # rotate the x-axis labels by 0 degrees
        plt.xticks(rotation=0)

        # set the title and labels for the chart
        ax.set_title("Google's Revenue by Product", fontsize=16, fontweight="bold")
        ax.set_xlabel("Period End Date", fontsize=12)
        ax.set_ylabel("Revenue (USD)", fontsize=12)

        # set the legend properties
        ax.legend(
            title="Product Category",
            loc="upper left",
            fontsize="small",
            title_fontsize=10,
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
            "goog:GoogleCloudMember": "Google Cloud",
            "goog:GoogleNetwork": "Google Network",
            "goog:YouTubeAdvertisingRevenueMember": "YouTube Ads",
            "goog:GoogleSearchOtherMember": "Google Search & other",
            "goog:OtherRevenuesMember": "Google other",
        }

        # create a list of new labels based on the original labels
        new_labels = [
            label_map[label] for label in list(revenue_product_pivot.columns.unique())
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

        # Save plot to html
        buf2 = io.BytesIO()
        ax.get_figure().savefig(buf2, format="png")
        buf2.seek(0)
        plot2_html = '<img src="data:image/png;base64,{}">'.format(
            base64.b64encode(buf2.read()).decode("utf-8")
        )

        return plot1_html, plot2_html
