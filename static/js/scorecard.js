document.addEventListener('DOMContentLoaded', function() {
    const scoreInputs = document.querySelectorAll('input[type="number"]');
    const totalScoreSpan = document.getElementById('total-score');
  
    scoreInputs.forEach(input => {
      input.addEventListener('input', updateTotalScore);
    });
  
    function updateTotalScore() {
      let total = 0;
      scoreInputs.forEach(input => {
        const score = parseInt(input.value, 10);
        if (!isNaN(score)) {
          total += score;
        }
      });
      totalScoreSpan.textContent = total;
    }
  });
  