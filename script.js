async function analyzeSentiment() {
  const url = document.getElementById("url").value;
  const errorDiv = document.getElementById("error");
  const resultDiv = document.getElementById("result");
  errorDiv.innerText = "";
  resultDiv.innerHTML = `
    <div class="text-center">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2">Analyzing comments...</p>
    </div>
  `;

  try {
    const response = await fetch("http://127.0.0.1:5000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error);

    const { sentiment_percent, top_positive, top_negative, wordcloud_path, csv_path } = data;

    resultDiv.innerHTML = `
  <div class="text-center mb-4">
    <h4>Sentiment Breakdown</h4>
    <canvas id="sentimentChart" width="300" height="300"></canvas>
  </div>

  <div class="row">
    <div class="col-md-6">
      <h5 class="text-success">Top 3 Positive Comments</h5>
      <ul class="list-group">
        ${top_positive.map(c => `<li class="list-group-item">${c.text}</li>`).join("")}
      </ul>
    </div>
    <div class="col-md-6">
      <h5 class="text-danger">Top 3 Negative Comments</h5>
      <ul class="list-group">
        ${top_negative.map(c => `<li class="list-group-item">${c.text}</li>`).join("")}
      </ul>
    </div>
  </div>

  <div class="mt-4 text-center">
    <h5>Word Cloud</h5>
    <img src="http://127.0.0.1:5000/download/${wordcloud_path}" class="wordcloud-img" alt="Word Cloud" />
  </div>

  <div class="mt-3 text-center">
    <a href="http://127.0.0.1:5000/download/${csv_path}" class="btn btn-outline-primary">Download CSV Summary</a>
  </div>
`;


    const ctx = document.getElementById("sentimentChart").getContext("2d");
    new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["Positive", "Negative", "Neutral"],
        datasets: [{
          data: [
            sentiment_percent.positive,
            sentiment_percent.negative,
            sentiment_percent.neutral
          ],
          backgroundColor: ["#4caf50", "#f44336", "#ffc107"]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom"
          }
        }
      }
    });

  } catch (err) {
    errorDiv.innerText = err.message;
    resultDiv.innerHTML = "";
  }
}
