document.addEventListener("DOMContentLoaded", () => {
    const runScriptsButton = document.getElementById("runScriptsBtn");
    const progressBar = document.getElementById("progressBar");
    const courseNameInput = document.getElementById("courseName");
    const courseDateInput = document.getElementById("courseDate");
    const errorBox = document.getElementById("error-box");
  
    function showError(message) {
      if (errorBox) {
        errorBox.textContent = message;
        errorBox.style.display = "block";
      } else {
        alert(message);
      }
    }
  
    function hideError() {
      if (errorBox) {
        errorBox.style.display = "none";
        errorBox.textContent = "";
      }
    }
  
    function disableButton(disabled) {
      runScriptsButton.disabled = disabled;
      runScriptsButton.textContent = disabled ? "Running..." : "Run Scripts";
    }
  
    function updateProgress(current, total, courseName, courseDate) {
      const percent = Math.round((current / total) * 100);
      progressBar.style.width = `${percent}%`;
      progressBar.textContent = `${percent}%`;
  
      if (current < total) {
        setTimeout(() => {
          updateProgress(current + 1, total, courseName, courseDate);
        }, 150); // Can be adjusted
      } else {
        disableButton(false);
      }
    }
  
    runScriptsButton.addEventListener("click", () => {
      const courseName = courseNameInput.value.trim();
      const courseDate = courseDateInput.value.trim();
  
      hideError();
  
      if (!courseName || !courseDate) {
        showError("❌ Please enter a Course Name and Date!");
        return;
      }
  
      disableButton(true);
      progressBar.style.width = "0%";
      progressBar.textContent = "0%";
  
      fetch("/run_scripts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ course_name: courseName, course_date: courseDate }),
      })
        .then((res) => {
          if (!res.ok) throw new Error("Network response was not ok.");
          return res.json();
        })
        .then((data) => {
          if (data.success) {
            updateProgress(1, 10, courseName, courseDate);
          } else {
            showError(data.message || "Something went wrong.");
            disableButton(false);
          }
        })
        .catch((err) => {
          console.error("❌ Error:", err);
          showError("An unexpected error occurred.");
          disableButton(false);
        });
    });
  });
  