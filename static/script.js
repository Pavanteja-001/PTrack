document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("urlForm");
    const resultsContainer = document.getElementById("results");
    const spinner = document.getElementById("loading");

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const url = document.getElementById("url").value;

        // Show results section and display loading spinner
        resultsContainer.style.display = "block";
        spinner.style.display = "block";

        // Reset UI before fetching new data
        document.getElementById("product_name").innerText = "Loading...";
        document.getElementById("product_image").src = "";
        document.getElementById("rating").innerText = "";
        document.getElementById("price").innerText = "";
        document.getElementById("best_review").innerText = "";
        document.getElementById("worst_review").innerText = "";
        document.getElementById("sentiment_graph").src = "";
        document.getElementById("wordcloud").src = "";
        document.getElementById("category_graph").src = "";

        document.getElementById("total_reviews").innerText = "-";
        document.getElementById("positive_percentage").innerText = "-";
        document.getElementById("negative_percentage").innerText = "-";

        fetch("/analyze", {
            method: "POST",
            body: new URLSearchParams({ url: url }),
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
        })
        .then((response) => response.json())
        .then((data) => {
            // Hide spinner once data is received
            spinner.style.display = "none";

            if (data.error) {
                document.getElementById("product_name").innerText = "Error: " + data.error;
                return;
            }

            // ✅ Update UI with received data
            document.getElementById("product_name").innerText = data.product_name;
            document.getElementById("product_image").src = data.product_image;
            document.getElementById("rating").innerText = data.rating_stars;
            document.getElementById("price").innerText = data.price;

            document.getElementById("total_reviews").innerText = data.total_reviews;
            document.getElementById("positive_percentage").innerText = data.positive_percentage;
            document.getElementById("negative_percentage").innerText = data.negative_percentage;

            document.getElementById("best_review").innerText = data.best_review;
            document.getElementById("worst_review").innerText = data.worst_review;
            document.getElementById("sentiment_graph").src = "data:image/png;base64," + data.sentiment_graph;
            document.getElementById("wordcloud").src = "data:image/png;base64," + data.wordcloud;
            document.getElementById("category_graph").src = "data:image/png;base64," + data.category_graph;
        })
        .catch((error) => {
            spinner.style.display = "none";
            document.getElementById("product_name").innerText = "An error occurred: " + error;
        });
    });

    // ✅ Dark Mode Toggle (Saves User Preference)
    const darkModeToggle = document.getElementById("darkModeToggle");
    if (darkModeToggle) {
        darkModeToggle.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
            localStorage.setItem("dark-mode", document.body.classList.contains("dark-mode"));
        });

        // Apply Dark Mode if User Previously Enabled It
        if (localStorage.getItem("dark-mode") === "true") {
            document.body.classList.add("dark-mode");
        }
    }
});
