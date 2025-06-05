"use client";

import { useState } from "react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [htmlContent, setHtmlContent] = useState("");

  const handleClone = async () => {
    if (!url) return;

    setLoading(true);
    setHtmlContent("");

    try {
      const response = await fetch("http://127.0.0.1:8000/clone", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();
      setHtmlContent(data.html || "<p>Failed to load HTML.</p>");
    } catch (error) {
      console.error("Error cloning site:", error);
      setHtmlContent("<p>Error occurred while cloning the website.</p>");
    }

    setLoading(false);
  };

  return (
    <main className="min-h-screen p-10 flex flex-col items-center gap-6 bg-gray-50 text-black">
      <h1 className="text-3xl font-bold">Website Cloner</h1>

      <input
        type="text"
        placeholder="Enter a website URL (e.g., https://example.com)"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="border px-4 py-2 w-full max-w-lg rounded shadow"
      />

      <button
        onClick={handleClone}
        className="bg-black text-white px-6 py-2 rounded hover:bg-gray-800"
      >
        Clone Website
      </button>

      {loading && <p>Loading...</p>}

      {htmlContent && (
        <div className="w-full max-w-5xl mt-8 border rounded overflow-hidden">
          <iframe
            srcDoc={htmlContent}
            title="Cloned Website"
            sandbox=""
            className="w-full h-[600px] bg-white"
          />
        </div>
      )}
    </main>
  );
}
