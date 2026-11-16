with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/run_clean_build.py", "r") as f:
    text = f.read()

# Adjust slide dimensions and overflow
text = text.replace(
    "padding: 45px 70px 75px 70px;",
    "padding: 35px 70px 65px 70px; max-height: 1080px; overflow: hidden;"
)

text = text.replace("height: 510px;", "height: 470px;")
text = text.replace("max-height: 520px;", "max-height: 480px;")
text = text.replace("height: 420px;", "height: 390px;")
text = text.replace("max-height: 430px;", "max-height: 400px;")

text = text.replace("padding: 16px 20px;\n    display: flex;\n    gap: 18px;", "padding: 12px 18px;\n    display: flex;\n    gap: 14px;")
text = text.replace("gap: 16px;\n  }", "gap: 10px;\n  }")
text = text.replace("bottom: 24px;", "bottom: 18px;")
text = text.replace("color: #64748B;", "color: #94A3B8;")

with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/run_clean_build.py", "w") as f:
    f.write(text)

print("Adjustments saved.")
