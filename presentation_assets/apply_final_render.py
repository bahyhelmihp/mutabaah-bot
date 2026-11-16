with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/run_clean_build.py", "r") as f:
    text = f.read()

# Replace rendering command and add cropping
old_render = """    cmd_shot = [
        "google-chrome",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1920,1080",
        f"--screenshot={slide_png}",
        tmp_path
    ]
    subprocess.run(cmd_shot, check=True)
    slide_images.append(slide_png)"""

new_render = """    cmd_shot = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1920,1167",
        f"--screenshot={slide_png}",
        tmp_path
    ]
    subprocess.run(cmd_shot, check=True)
    from PIL import Image
    im = Image.open(slide_png)
    if im.size != (1920, 1080):
        im = im.crop((0, 0, 1920, 1080))
        im.save(slide_png)
    slide_images.append(slide_png)"""

text = text.replace(old_render, new_render)

with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/run_clean_build.py", "w") as f:
    f.write(text)

print("Applied final render changes successfully.")
