
def extract_gateway_response(data):
    return {
        "status": data.get("status"),
        "val_id": data.get("val_id"),
        "tran_id": data.get("tran_id"),
        "amount": data.get("amount"),
        "currency": data.get("currency"),
        "card_type": data.get("card_type"),
        "card_brand": data.get("card_brand"),
        "bank_tran_id": data.get("bank_tran_id"),
        "risk_level": data.get("risk_level"),
        "risk_title": data.get("risk_title"),
    }
