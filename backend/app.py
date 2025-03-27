from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import os
from utils.build_site import build_puzzle_site
from utils.deploy_to_netlify import deploy_to_netlify

app = Flask(__name__)
CORS(app, resources={r"/generate-site": {"origins": "*"}})

print("🔥 app started")

@app.route("/generate-site", methods=["POST"])
def generate_site():
    try:
        print("🚀 STARTED /generate-site route")
        print("📝 Form keys:", list(request.form.keys()))
        print("📎 File keys:", list(request.files.keys()))

        netlify_token = request.form.get("netlifyToken")
        target_url = request.form.get("targetUrl")
        delivery_mode = request.form.get("deliveryMode")

        filenames = request.form.getlist("filenames[]")
        indices = request.form.getlist("indices[]")

        if not netlify_token:
            raise ValueError("Missing Netlify token")
        if not target_url:
            raise ValueError("Missing target URL")
        if not filenames or not indices or len(filenames) != 10 or len(indices) != 10:
            raise ValueError("Expected 10 filenames and 10 indices")

        print("✅ Received target:", target_url)
        print("🧩 Delivery mode:", delivery_mode)
        print("🧠 Filenames:", filenames)
        print("🔢 Indices:", indices)

        with tempfile.TemporaryDirectory() as tmpdir:
            image_paths = []
            for i in range(10):
                file = request.files.get(f"image{i}")
                if not file:
                    raise ValueError(f"Missing image{i}")
                save_path = os.path.join(tmpdir, f"{i}_{file.filename}")
                file.save(save_path)
                image_paths.append(save_path)

            print("📷 Saved all uploaded images")

            zip_path, _ = build_puzzle_site(
                image_paths=image_paths,
                labels=filenames,
                indices=[int(idx) for idx in indices],
                target_url=target_url,
                delivery_mode=delivery_mode,
                output_dir=os.path.join(tmpdir, "output")
            )

            print("📦 Site built, starting deploy...")

            # Always try to deploy
            deploy_result = deploy_to_netlify(zip_path, netlify_token)

            if deploy_result["success"]:
                print("✅ Deploy successful:", deploy_result["url"])
                return jsonify({"url": deploy_result["url"]}), 200
            else:
                print("⚠️ Deploy failed:", deploy_result.get("error"))
                return send_file(
                    zip_path,
                    mimetype="application/zip",
                    as_attachment=True,
                    download_name="puzzle_site.zip"
                )
            return send_file(zip_path, as_attachment=True)

    except Exception as e:
        print("❌ Exception during /generate-site:", e)
        return jsonify({"error": str(e)}), 500
