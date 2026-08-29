import json

ADMIN_CONFIG = {
    "super_admin": "esaidi2013@gmail.com",
    "allowed_google_accounts": [
        "esaidi2013@gmail.com"
    ],
    "role": "SUPERUSER_FULL_ACCESS",
    "features_unlocked": [
        "FORCE_CROSS_REGISTRY_SYNC",
        "EXECUTE_FINANCIAL_UNDERWRITING",
        "ACCESS_LEGAL_RAW_DOSSIERS",
        "DISPATCH_INSTANT_ALERTS"
    ]
}

def is_admin(email):
    return email.strip().lower() in ADMIN_CONFIG["allowed_google_accounts"]

if __name__ == "__main__":
    with open("admin_config.json", "w", encoding="utf-8") as f:
        json.dump(ADMIN_CONFIG, f, indent=4, ensure_ascii=False)
    print(f"[✓] Административният достъп е активиран за: {ADMIN_CONFIG['super_admin']}")
