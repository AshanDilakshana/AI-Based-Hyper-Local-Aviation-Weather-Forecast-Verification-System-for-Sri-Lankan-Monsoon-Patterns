const express = require("express");
const cors = require("cors");
const { execFile } = require("child_process");
const path = require("path");

const app = express();

app.use(cors());
app.use(express.json());

app.post("/api/predict", (req, res) => {
  const { temperature, humidity, pressure } = req.body;

  if (
    temperature === undefined ||
    humidity === undefined ||
    pressure === undefined
  ) {
    return res.status(400).json({
      error: "temperature, humidity and pressure are required",
    });
  }

  const scriptPath = path.join(__dirname, "predict.py");

  execFile(
    "python",
    [scriptPath, temperature, humidity, pressure],
    { cwd: __dirname },
    (error, stdout, stderr) => {
      if (error) {
        console.error("Python error:", stderr);
        return res.status(500).json({
          error: "Prediction failed",
          details: stderr,
        });
      }

      try {
        const result = JSON.parse(stdout);
        res.json(result);
      } catch (err) {
        console.error("Parse error:", stdout);
        res.status(500).json({
          error: "Invalid prediction output",
          output: stdout,
        });
      }
    }
  );
});

app.listen(5000, () => {
  console.log("Backend running on http://localhost:5000");
});