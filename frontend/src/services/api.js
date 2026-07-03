import axios from "axios";

function normalizeApiBaseUrl(value) {
  const fallback = "http://localhost:8001";
  const rawValue = (value || "").trim();
  if (!rawValue) return fallback;
  return /^https?:\/\//i.test(rawValue) ? rawValue : `https://${rawValue}`;
}

export const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 60000,
});

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("omnidocs_user") || "null");
  } catch {
    return null;
  }
}

function getGuestId() {
  const storageKey = "omnidocs_guest_id";
  const existing = localStorage.getItem(storageKey);
  if (existing) return existing;
  const generated = crypto.randomUUID ? crypto.randomUUID() : `guest-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  localStorage.setItem(storageKey, generated);
  return generated;
}

function appendEditIdentity(formData) {
  const user = getStoredUser();
  formData.append("user_id", user?.id ? String(user.id) : "");
  formData.append("guest_id", user?.id ? "" : getGuestId());
}

export async function uploadDocument(file, command, task = "", options = {}) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("command", command);
  formData.append("task", task);
  formData.append("target_size_mb", options.targetSizeMb || "");
  formData.append("crop_width", options.cropWidth || "");
  formData.append("crop_height", options.cropHeight || "");
  appendEditIdentity(formData);
  const { data } = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function uploadImagesToPdf(files, outputName = "images_combined.pdf") {
  const formData = new FormData();
  Array.from(files || []).forEach((file) => formData.append("files", file));
  formData.append("output_name", outputName);
  appendEditIdentity(formData);
  const { data } = await api.post("/upload/images-to-pdf", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function saveEditedImage({ file, outputFormat, outputName, ocrText }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("output_format", outputFormat);
  formData.append("output_name", outputName);
  formData.append("ocr_text", ocrText);
  appendEditIdentity(formData);
  const { data } = await api.post("/ocr/image/save", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getHistory() {
  const { data } = await api.get("/history");
  return data;
}

export async function getAdminStats() {
  const { data } = await api.get("/admin/stats");
  return data;
}

export async function getTablePreview(filename) {
  const { data } = await api.get(`/documents/table-preview/${encodeURIComponent(filename)}`);
  return data;
}

export async function editPdfText(file, oldText, newText, outputName) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("old_text", oldText);
  formData.append("new_text", newText);
  formData.append("output_name", outputName);
  appendEditIdentity(formData);
  const { data } = await api.post("/editor/pdf/replace", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function openDocumentForEdit(file, expectedFileType) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("expected_file_type", expectedFileType);
  const { data } = await api.post("/editor/open", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function saveOpenDocumentEdit({ originalFilename, storedFilename, detectedFileType, editedText, editedBlocks, editedParagraphs, outputName, outputFormat }) {
  const formData = new FormData();
  formData.append("original_filename", originalFilename);
  formData.append("stored_filename", storedFilename || "");
  formData.append("detected_file_type", detectedFileType);
  formData.append("edited_text", editedText);
  formData.append("edited_blocks", JSON.stringify(editedBlocks || []));
  formData.append("edited_paragraphs", JSON.stringify(editedParagraphs || []));
  formData.append("output_name", outputName);
  formData.append("output_format", outputFormat);
  appendEditIdentity(formData);
  const { data } = await api.post("/editor/save", formData);
  return data;
}

export default api;
