import io
import base64
import random
from pathlib import Path

from flask import Flask, request, render_template_string, jsonify

import config
from signature_engine import generate_signature_variant, variant_to_png_bytes
from document_processor import insert_signature_pdf

app = Flask(__name__)

# Formular beim Start einmal in den Speicher laden
_FORMULAR_PFAD = Path(__file__).parent / config.FORMULAR_PFAD
with open(_FORMULAR_PFAD, "rb") as f:
    FORMULAR_BYTES = f.read()


PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Absenzen-Blatt – Signatur</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 720px;
           margin: 0 auto; padding: 24px; background: #f8f9fa; color: #212529; }
    h1 { font-size: 1.5rem; }
    .warning { background: #fff3cd; border: 1px solid #ffc107;
               padding: 12px 16px; border-radius: 8px; font-size: 0.9rem;
               margin-bottom: 20px; }
    .card { background: #fff; border-radius: 12px; padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    label { display: block; font-weight: 600; font-size: 0.9rem; margin: 14px 0 6px; }
    input[type="file"] { width: 100%; }
    button { background: #0d6efd; color: #fff; border: none;
             padding: 12px 28px; border-radius: 8px; font-size: 1rem;
             cursor: pointer; margin-top: 20px; width: 100%; }
    button:hover { background: #0b5ed7; }
    button:disabled { background: #6c757d; cursor: not-allowed; }
    .status { margin-top: 14px; font-size: 0.9rem; min-height: 20px; }
    .result { margin-top: 20px; padding: 18px; background: #d1e7dd;
              border-radius: 8px; }
    .result a { display: inline-block; background: #198754; color: #fff;
                padding: 12px 22px; border-radius: 8px; text-decoration: none;
                font-weight: 600; }
  </style>
</head>
<body>
  <h1>✍️ Absenzen-Blatt signieren</h1>
  <div class="warning">
    Nur für die <strong>eigene Unterschrift</strong> verwenden. Das Einfügen
    fremder Unterschriften ist strafbar.
  </div>

  <div class="card">
    <form id="form">
      <label>Bild deiner Unterschrift (PNG/JPG)</label>
      <input type="file" name="signature" accept=".png,.jpg,.jpeg" required>

      <button type="submit" id="btn">Dokument signieren</button>
      <div class="status" id="status"></div>
    </form>
    <div class="result" id="result" style="display:none;"></div>
  </div>

  <script>
    document.getElementById('form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btn');
      const status = document.getElementById('status');
      const resultDiv = document.getElementById('result');
      btn.disabled = true;
      status.textContent = 'Verarbeite …';
      resultDiv.style.display = 'none';

      try {
        const fd = new FormData(e.target);
        const resp = await fetch('/api/process', { method: 'POST', body: fd });
        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.error || 'Fehler');
        }
        const data = await resp.json();
        resultDiv.innerHTML = `
          <p><strong>Fertig!</strong></p>
          <a href="data:application/pdf;base64,${data.file_b64}"
             download="absenzen_signiert.pdf">⬇️ PDF herunterladen</a>
        `;
        resultDiv.style.display = 'block';
        status.textContent = '';
      } catch (err) {
        status.textContent = 'Fehler: ' + err.message;
      } finally {
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/process", methods=["POST"])
def process():
    try:
        sig_file = request.files.get("signature")
        if not sig_file:
            return jsonify({"error": "Bitte Unterschrift hochladen."}), 400

        sig_bytes = sig_file.read()

        # Neuer Seed pro Anfrage → jedes Mal andere Varianz
        random.seed(random.randint(0, 1_000_000))

        variant_img = generate_signature_variant(sig_bytes)
        variant_png = variant_to_png_bytes(variant_img)

        final_pdf = insert_signature_pdf(
            FORMULAR_BYTES, config.FORMULAR_SEITE, variant_png,
        )

        b64 = base64.b64encode(final_pdf).decode("utf-8")
        return jsonify({"file_b64": b64})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
