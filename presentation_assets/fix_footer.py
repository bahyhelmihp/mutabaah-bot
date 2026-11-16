with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/run_clean_build.py", "r") as f:
    text = f.read()

# Replace footer style
old_footer = """.slide-footer {
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 16px;
    font-size: 14.5px;
    color: #64748B;
  }"""

new_footer = """.slide-footer {
    position: absolute;
    bottom: 24px;
    left: 70px;
    right: 70px;
    z-index: 10;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    padding-top: 14px;
    font-size: 14.5px;
    color: #64748B;
  }"""

text = text.replace(old_footer, new_footer)
text = text.replace("padding: 45px 80px 35px 80px;", "padding: 45px 70px 75px 70px;")
text = text.replace("height: 550px;", "height: 510px;")
text = text.replace("max-height: 560px;", "max-height: 520px;")
text = text.replace("height: 460px;", "height: 420px;")
text = text.replace("max-height: 470px;", "max-height: 430px;")

with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/run_clean_build.py", "w") as f:
    f.write(text)

print("Replacement done.")
