from tradingia.news import FinnhubNewsProvider

provider = FinnhubNewsProvider()

news = provider.get_news("NVDA")

print(f"{len(news)} News gefunden\n")

if news:
    print(news[0])
    print()
    print(vars(news[0]))