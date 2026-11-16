"""
Amalan definitions, default targets, and helper functions for Mutabaah Bot.
"""
from typing import Dict, Any, List

AMALAN_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "tilawah": {
        "id": "tilawah",
        "name": "Tilawah Al-Qur'an",
        "short_name": "Tilawah",
        "icon": "📖",
        "column": "Tilawah Pages",
        "type": "int",
        "unit": "halaman",
        "default_target": 20,
        "target_period": "daily",
        "quick_options": [0, 5, 10, 15, 20, 25, 30, 40],
        "max_value": 100,
        "allow_berhalangan": True,
        "prompt": "Berapa halaman Tilawah hari ini?",
    },
    "sholat_wajib": {
        "id": "sholat_wajib",
        "name": "Sholat Wajib",
        "short_name": "Sholat Wajib",
        "icon": "🕌",
        "column": "Sholat Wajib",
        "type": "int",
        "unit": "waktu",
        "default_target": 5,
        "target_period": "daily",
        "quick_options": [0, 1, 2, 3, 4, 5],
        "max_value": 5,
        "allow_berhalangan": True,
        "prompt": "Berapa sholat wajib yang dilakukan tepat waktu / berjamaah hari ini? (0 - 5)",
    },
    "rawatib": {
        "id": "rawatib",
        "name": "Sholat Sunnah Rawatib",
        "short_name": "Rawatib",
        "icon": "🌙",
        "column": "Rawatib Rakaat",
        "type": "int",
        "unit": "rakaat",
        "default_target": 12,
        "target_period": "daily",
        "quick_options": [0, 2, 4, 6, 8, 10, 12],
        "max_value": 12,
        "prompt": "Berapa rakaat sholat sunnah rawatib hari ini?",
    },
    "almatsurat": {
        "id": "almatsurat",
        "name": "Al-Ma’tsurat",
        "short_name": "Al-Ma’tsurat",
        "icon": "📿",
        "column": "Almatsurat",
        "type": "int",
        "unit": "kali",
        "default_target": 2,
        "target_period": "daily",
        "quick_options": [0, 1, 2],
        "max_value": 2,
        "prompt": "Berapa kali membaca Al-Ma’tsurat hari ini?\n• 0 = Tidak\n• 1 = Pagi atau petang\n• 2 = Pagi dan petang",
    },
    "shalawat": {
        "id": "shalawat",
        "name": "Shalawat",
        "short_name": "Shalawat",
        "icon": "🌸",
        "column": "Shalawat",
        "type": "int",
        "unit": "kali",
        "default_target": 100,
        "target_period": "daily",
        "quick_options": [0, 33, 50, 100, 200, 300, 500, 1000],
        "max_value": 10000,
        "prompt": "Berapa kali membaca Shalawat hari ini?",
    },
    "istighfar": {
        "id": "istighfar",
        "name": "Istighfar",
        "short_name": "Istighfar",
        "icon": "🤲",
        "column": "Istighfar",
        "type": "int",
        "unit": "kali",
        "default_target": 100,
        "target_period": "daily",
        "quick_options": [0, 33, 50, 100, 200, 300, 500, 1000],
        "max_value": 10000,
        "prompt": "Berapa kali beristighfar hari ini?",
    },
    "tadabbur": {
        "id": "tadabbur",
        "name": "Tadabbur Al-Qur'an",
        "short_name": "Tadabbur",
        "icon": "📜",
        "column": "Tadabbur Ayat",
        "type": "int",
        "unit": "ayat",
        "default_target": 1,
        "target_period": "daily",
        "quick_options": [0, 1, 2, 3, 5, 10],
        "max_value": 100,
        "prompt": "Berapa ayat yang Anda tadabburi hari ini?",
    },
    "shaum_sunnah": {
        "id": "shaum_sunnah",
        "name": "Shaum Sunnah",
        "short_name": "Shaum Sunnah",
        "icon": "🍽️",
        "column": "Shaum Sunnah",
        "type": "bool",
        "unit": "hari",
        "default_target": 4,  # min 4x per bulan
        "target_period": "monthly",
        "prompt": "Apakah Anda melaksanakan shaum (puasa) sunnah hari ini?",
    },
    "qiyamulail": {
        "id": "qiyamulail",
        "name": "Qiyamulail",
        "short_name": "Qiyamulail",
        "icon": "🌃",
        "column": "Qiyamulail",
        "type": "bool",
        "unit": "hari",
        "default_target": 12,  # min 3x / pekan = ~12x / bulan
        "target_period": "monthly",
        "prompt": "Apakah Anda melaksanakan Qiyamulail hari ini?",
    },
    "dhuha": {
        "id": "dhuha",
        "name": "Sholat Dhuha",
        "short_name": "Dhuha",
        "icon": "☀️",
        "column": "Dhuha",
        "type": "bool",
        "unit": "hari",
        "default_target": 12,  # min 3x / pekan = ~12x / bulan
        "target_period": "monthly",
        "prompt": "Apakah Anda melaksanakan Sholat Dhuha hari ini?",
    },
    "olahraga": {
        "id": "olahraga",
        "name": "Olahraga",
        "short_name": "Olahraga",
        "icon": "🏃",
        "column": "Olahraga",
        "type": "int",
        "unit": "menit",
        "default_target": 30,  # default 30 menit per minggu
        "target_period": "weekly",
        "quick_options": [0, 10, 15, 20, 30, 45, 60],
        "max_value": 1440,
        "prompt": "Berapa menit Anda berolahraga hari ini?\n_Target: 30 menit / pekan_",
    },
    "silaturahim": {
        "id": "silaturahim",
        "name": "Silaturahim",
        "short_name": "Silaturahim",
        "icon": "🤝",
        "column": "Silaturahim",
        "type": "bool",
        "unit": "hari",
        "default_target": 4,  # min 1x / pekan = ~4x / bulan
        "target_period": "monthly",
        "prompt": "Apakah Anda melaksanakan silaturahim hari ini? (ya/tidak)",
    },
    "doa_ummat_islam": {
        "id": "doa_ummat_islam",
        "name": "Doa untuk Kebaikan Ummat Islam",
        "short_name": "Doa Ummat",
        "icon": "🤲",
        "column": "Doa Ummat Islam",
        "type": "int",
        "unit": "kali",
        "default_target": 1,
        "target_period": "daily",
        "quick_options": [0, 1, 2, 3, 5, 10],
        "max_value": 1000,
        "prompt": "Berapa kali Anda mendoakan kebaikan ummat Islam hari ini?",
    },
}

ALL_AMALAN_KEYS: List[str] = list(AMALAN_DEFINITIONS.keys())


def get_default_targets() -> Dict[str, int]:
    """Return dictionary of default targets for each amalan."""
    return {k: v["default_target"] for k, v in AMALAN_DEFINITIONS.items()}


def get_amalan_info(key: str) -> Dict[str, Any]:
    """Get metadata for a specific amalan."""
    return AMALAN_DEFINITIONS.get(key, {})


def format_amalan_value(key: str, value: Any) -> str:
    """Format the value of an amalan for display."""
    defn = get_amalan_info(key)
    if not defn:
        return str(value)

    if defn["type"] == "bool":
        if isinstance(value, bool):
            return "✅ Ya" if value else "❌ Tidak"
        val_str = str(value).strip().upper()
        if val_str in ["TRUE", "1", "YES", "YA"]:
            return "✅ Ya"
        if val_str in ["FALSE", "0", "NO", "TIDAK"]:
            return "❌ Tidak"
        return "Belum diisi"

    # Integer types (including olahraga in minutes)
    if value is None or str(value).strip() == "":
        return "Belum diisi"

    val_clean = str(value).strip().lower()
    if val_clean in ["berhalangan", "haid", "halangan"]:
        return "🌸 Berhalangan"

    # Backward compatibility: if olahraga was stored as boolean in older rows
    if key == "olahraga":
        val_upper = str(value).strip().upper()
        if val_upper in ["TRUE", "1", "YES", "YA"]:
            return "30 menit"
        if val_upper in ["FALSE", "0", "NO", "TIDAK"]:
            return "0 menit"

    try:
        val_int = int(float(str(value).strip()))
        unit = defn.get("unit", "")
        return f"{val_int} {unit}".strip()
    except (ValueError, TypeError):
        return str(value)
