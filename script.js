const toggle = document.getElementById("toggle");
if (toggle) {
  toggle.addEventListener("click", () => {
    document.body.classList.toggle("light");
    if (document.body.classList.contains("light")) {
      toggle.textContent = "🌞";
    } else {
      toggle.textContent = "🌙";
    }
  });
}
document.querySelectorAll('.skin-tone').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('.skin-tone').forEach(e => e.classList.remove('active'));
    el.classList.add('active');
  });
});
document.querySelectorAll('.color-swatch').forEach(el => {
  el.addEventListener('click', () => {
    el.classList.toggle('active');
  });
});
// Style chip selection
const chips = document.querySelectorAll(".style-chip");
chips.forEach(chip => {
  chip.addEventListener("click", () => {
    chip.classList.toggle("active");
  });
});

// ==================== HOME PAGE RECOMMENDATION ====================
document.getElementById('outfit-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const button = this.querySelector('button[type="submit"]');
    const originalText = button.textContent;
    button.textContent = "Generating...";
    button.disabled = true;
    // Collect form data
    const formData = {
        bodyType: document.getElementById('bodyType').value,
        gender: document.getElementById('gender').value,
        occasion: document.getElementById('occasion').value,
        season: document.getElementById('season').value,
        budget: document.getElementById('budget').value,
        context: document.getElementById('context').value || "",
        styles: Array.from(document.querySelectorAll('.style-chip.active')).map(chip => chip.textContent),
        colors: Array.from(document.querySelectorAll('.color-swatch.active')).map(s => s.style.backgroundColor)
    };
    try {
        const response = await fetch('/api/recommend-gemini', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const result = await response.json();
        if (result.success) {
            showRecommendation(result.response || result.text || "Recommendation generated!");
        } else {
            alert("Error: " + (result.error || "Something went wrong"));
        }
    } catch (err) {
        console.error(err);
        alert("Failed to connect to AI. Check if server is running. (Wait 1 min if quota error)");
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
});
function showRecommendation(text) {
    let resultBox = document.getElementById('recommend-result');
    if (!resultBox) {
        resultBox = document.createElement('div');
        resultBox.id = 'recommend-result';
        resultBox.style.cssText = `
            margin-top: 30px; padding: 25px; background: rgba(255,255,255,0.05);
            border-radius: 12px; border: 1px solid rgba(255,215,0,0.2);
        `;
        document.querySelector('#outfit-recommender .card').appendChild(resultBox);
    }
    resultBox.innerHTML = `
        <h3 style="color: #ffd700; margin-bottom:15px;">✦ Your AI Recommendation</h3>
        <div style="line-height:1.7; color:#ddd;">${text.replace(/\n/g, '<br>')}</div>
    `;
    resultBox.scrollIntoView({ behavior: "smooth" });
}