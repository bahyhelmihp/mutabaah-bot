import re

with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/build_presentation.py", "r") as f:
    code = f.read()

# Replace padding
code = code.replace("padding: 70px 90px;", "padding: 50px 80px; max-height: 1080px; box-sizing: border-box;")

# Fix the slide extraction logic
old_split = """{HTML_SLIDES.split('<!-- SLIDE ' + str(i) + ':')[1].split('<!-- SLIDE ' if i < 10 else '</body>')[0]}"""
new_split = """{HTML_SLIDES.split('<!-- SLIDE ' + str(i) + ':')[1].split('-->', 1)[1].split('<!-- SLIDE ' if i < 10 else '</body>')[0].strip()}"""

code = code.replace(old_split, new_split)

# Add keyboard navigation script for HTML presentation
interactive_script = """
<script>
  let currentSlide = 0;
  const slides = document.querySelectorAll('.slide');
  
  function showSlide(idx) {
    if (idx < 0) idx = 0;
    if (idx >= slides.length) idx = slides.length - 1;
    currentSlide = idx;
    slides[currentSlide].scrollIntoView({ behavior: 'smooth' });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
      e.preventDefault();
      showSlide(currentSlide + 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault();
      showSlide(currentSlide - 1);
    } else if (e.key === 'Home') {
      e.preventDefault();
      showSlide(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      showSlide(slides.length - 1);
    } else if (e.key.toLowerCase() === 'f') {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
    }
  });
</script>
</body>
"""
code = code.replace("</body>", interactive_script, 1)

with open("/home/bahy/aibrain/mutabaah-bot/presentation_assets/build_presentation.py", "w") as f:
    f.write(code)

print("Updated build_presentation.py successfully.")
