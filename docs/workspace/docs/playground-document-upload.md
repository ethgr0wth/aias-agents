# Playground & Dashboard Document Upload

## What & Why
Add file upload capability to the Playground and Dashboard Knowledge Base so users can upload documents (PDF, TXT, CSV, DOCX) instead of manually pasting text. Text is extracted server-side and stored as knowledge items (same Redis pattern as today). This makes the playground feel like a real workstation and removes friction from the knowledge base workflow.

## Done looks like
- Playground: Users can drag-and-drop or click-to-upload files in the Knowledge panel. File content is extracted and added as a knowledge item to the session.
- Dashboard Knowledge Base: Users can upload a document in the "Add Knowledge" form. The extracted text populates the content field automatically.
- Supported formats: .txt, .csv, .pdf, .docx
- Upload size limit enforced (e.g. 5MB)
- Clear error messages for unsupported formats or extraction failures
- Mobile-friendly upload UI

## Out of scope
- Image/OCR extraction from scanned PDFs
- Cloud storage backends (S3, etc.) — text is extracted and stored in Redis, files are not persisted
- Artifact Portal document upload (not needed yet)

## Tasks
1. **Backend file upload endpoint** — Add a multipart POST endpoint that accepts file uploads, extracts text content based on file type (plain text for .txt/.csv, pdf extraction for .pdf, docx extraction for .docx), and returns the extracted text. Install any needed Python packages (e.g. PyPDF2/pdfplumber, python-docx).

2. **Playground knowledge upload integration** — Add a file upload button/drop zone to the Playground's Knowledge panel. On upload, call the extraction endpoint and create a knowledge item with the extracted text. Show upload progress and success/error states.

3. **Dashboard knowledge base upload** — Add a file upload option to the Dashboard's "Add Knowledge" form (Training Contexts). On upload, call the same extraction endpoint and populate the title (from filename) and content (from extracted text) fields.

4. **Session-level file attachments** — Allow uploaded files to persist as attachments on a playground session, shown as chips/tags that can be viewed or removed. The extracted text content is what gets sent to the AI, but the file metadata (name, size, type) is stored for reference.

## Relevant files
- `aias_production_clone/client/src/pages/OraclePlayground.tsx:937-979,1599-1678`
- `aias_production_clone/client/src/pages/Dashboard.tsx:2118-2174`
- `aias_production_clone/api/routes/playground.py:218-224`
- `aias_production_clone/api/routes/users.py:496-536`
- `aias_production_clone/api/services/redis_storage.py:3740`
