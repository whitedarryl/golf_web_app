document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Script loaded!");

    const runScriptsButton = document.getElementById("run-scripts-btn");

    if (runScriptsButton) {
        runScriptsButton.addEventListener("click", function () {
            const courseName = document.getElementById("course_name").value.trim();
            const courseDate = document.getElementById("course_date").value.trim();

            if (!courseName || !courseDate) {
                alert("❌ Please enter a Course Name and Date!");
                return;
            }

            fetch("/run_scripts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    course_name: courseName,
                    course_date: courseDate
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log("✅ Scripts executed:", data);

                if (data.error) {
                    alert("❌ Error: " + data.error);
                    return;
                }

                let progressBar = document.getElementById("progress-bar");
                let totalSteps = data.progress.length;

                function updateProgress(step) {
                    if (step < totalSteps) {
                        let percent = Math.round(((step + 1) / totalSteps) * 100);
                        progressBar.style.width = percent + "%";
                        progressBar.textContent = percent + "%";
                        setTimeout(() => updateProgress(step + 1), 1000);
                    } else {
                        document.getElementById("output").textContent = data.logs.join("\n");
                    }
                }

                updateProgress(0);
            })
            .catch(error => console.error("❌ Error:", error));
        });
    } else {
        console.error("❌ Button with ID 'run-scripts-btn' not found!");
    }
});
