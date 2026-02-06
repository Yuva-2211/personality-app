const textarea = document.getElementById("inputText");
const charCount = document.getElementById("charCount");

textarea.addEventListener("input", () => {
  charCount.textContent = textarea.value.length;
});

function getScoreClass(score) {
  if (score >= 0.65) return "high";
  if (score >= 0.35) return "moderate";
  return "low";
}

function getScoreLabel(score) {
  if (score >= 0.65) return "High";
  if (score >= 0.35) return "Moderate";
  return "Low";
}

function analyzeText() {
  const text = document.getElementById("inputText").value.trim();
  
  if (text.length < 50) {
    alert("Please write at least 50 characters for a meaningful analysis.");
    return;
  }

  // Add loading state
  const button = document.querySelector(".analyze-btn");
  const originalContent = button.innerHTML;
  button.innerHTML = '<span>Analyzing...</span>';
  button.disabled = true;

  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text })
  })
  .then(res => res.json())
  .then(data => {
    // Reset button
    button.innerHTML = originalContent;
    button.disabled = false;

    // Show results
    document.getElementById("results").classList.remove("hidden");
    
    // Scroll to results
    setTimeout(() => {
      document.getElementById("results").scrollIntoView({ 
        behavior: "smooth", 
        block: "start" 
      });
    }, 100);

    // Render trait bars
    const traitContainer = document.getElementById("traitScores");
    traitContainer.innerHTML = "";
    
    let dominantTrait = "";
    let dominantScore = -1;

    const traitOrder = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"];
    
    traitOrder.forEach(trait => {
      if (data.scores[trait] !== undefined) {
        const score = data.scores[trait];
        const scoreClass = getScoreClass(score);
        const scoreLabel = getScoreLabel(score);
        
        const traitItem = document.createElement("div");
        traitItem.className = "trait-item";
        traitItem.innerHTML = `
          <div class="trait-header">
            <span class="trait-name">${trait}</span>
            <span class="trait-score score-${scoreClass}">${scoreLabel} (${score.toFixed(2)})</span>
          </div>
          <div class="trait-bar-bg">
            <div class="trait-bar-fill bar-${scoreClass}" style="width: ${score * 100}%"></div>
          </div>
        `;
        traitContainer.appendChild(traitItem);

        if (score > dominantScore) {
          dominantScore = score;
          dominantTrait = trait;
        }
      }
    });

    // Set dominant trait
    document.getElementById("dominantTrait").innerHTML = 
      `${dominantTrait} <span style="font-size: 1.25rem; opacity: 0.9;">(${dominantScore.toFixed(2)})</span>`;

    // Render profiles
    const profileList = document.getElementById("profiles");
    profileList.innerHTML = "";
    data.profiles.forEach(profile => {
      const li = document.createElement("li");
      li.textContent = profile;
      profileList.appendChild(li);
    });
  })
  .catch(error => {
    button.innerHTML = originalContent;
    button.disabled = false;
    alert("An error occurred during analysis. Please try again.");
    console.error("Error:", error);
  });
}