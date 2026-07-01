import pandas as pd


def lade_sp500_ticker():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    tabellen = pd.read_html(url)
    sp500 = tabellen[0]

    ticker = sp500["Symbol"].tolist()

    # Yahoo Finance braucht bei manchen Tickern "-" statt "."
    ticker = [t.replace(".", "-") for t in ticker]

    return ticker