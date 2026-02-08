import { API_BASE_URL } from "@/lib/api/client";

export async function synthesizeSpeech(text: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/tts/elevenlabs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `TTS failed with status ${response.status}${errorText ? `: ${errorText}` : ""}`
    );
  }

  return response.blob();
}

export async function transcribeSpeech(audio: Blob): Promise<string> {
  const form = new FormData();
  form.append("file", audio, "voice-note.webm");

  const response = await fetch(`${API_BASE_URL}/tts/elevenlabs/transcribe`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `STT failed with status ${response.status}${errorText ? `: ${errorText}` : ""}`
    );
  }

  const payload = (await response.json()) as { text?: string };
  const text = (payload.text ?? "").trim();
  if (!text) {
    throw new Error("STT returned empty transcript.");
  }

  return text;
}
