def berechne_position(einstieg, stop_loss, kontostand=10000, risiko_pro_trade=0.02):
    risiko_betrag = kontostand * risiko_pro_trade
    risiko_pro_aktie = einstieg - stop_loss

    if risiko_pro_aktie <= 0:
        return {
            "Positionsgröße $": 0,
            "Aktien": 0,
            "Max Risiko $": 0,
        }

    aktien = risiko_betrag / risiko_pro_aktie
    positionsgroesse = aktien * einstieg

    return {
        "Positionsgröße $": round(positionsgroesse, 2),
        "Aktien": round(aktien, 2),
        "Max Risiko $": round(risiko_betrag, 2),
    }