# Automated Document Verification using AI

This is an AI-powered system to verify user-uploaded documents like Aadhaar, Passport. The system is built using Django and React, with intelligent OCR extraction via Tesseract and PDF handling through Poppler. It automatically extracts key fields such as name, date of birth, and document number, and validates them.

I have created the endpoint **'/api/upload/'** using Django's APIView (from Django REST Framework), which accepts document uploads along with a specified document type.
The API supports PDF, JPG, and PNG file formats and processes them using Tesseract OCR. It extracts fields such as name, date of birth, and document number based on the selected document type (aadhaar or passport).
The endpoint was tested using Postman. A sample request screenshot is attached below.

---

###  POSTMAN

<img width="943" height="500" alt="postman1" src="https://github.com/user-attachments/assets/c0da68fe-9dda-4ca8-85d5-9b61c2930726" />

---

## Backend: OCR & Document Validation Workflow

- **OCR Processing**: The uploaded file (PDF or image) is converted to text using **'Tesseract OCR'**. If the document is a PDF, the first page is converted into an image using **'Poppler'** before being passed to Tesseract for OCR.
- **Field Extraction**: Based on the selected document_type (aadhaar or passport), key fields such as name, date of birth, and document number are extracted using regex patterns tailored to each document type.
- **Validation**: The extracted fields are validated against expected formats:
  - Aadhaar number format: `xxxx xxxx xxxx`
  - Passport number format: `A1234567`
  - Name format: Alphabetic (min 3 characters)
  - Date of Birth format: `DD/MM/YYYY`

- **Verification Status**:
  - `Verified` if 2 or more fields are valid  
  - `Pending` if only 1 field is valid  
  - `Failed` if none are valid
  - 
  - **Storage**: All extracted data including **verification status**, **raw OCR text**, and **file metadata** is saved to the database using Django ORM for future access.

---

### 🔗 API Endpoints

- **POST `/api/upload/`**  
  Upload a document (PDF, JPG, or PNG) with a specified document type (`aadhaar` or `passport`).  
  The system processes it using Tesseract OCR, extracts key fields (name, DOB, document number), validates them, and stores the result.

- **GET `/api/documents/`**  
  Fetch a list of all uploaded documents along with their verification status and extracted fields.

- **GET `/api/documents/<int:pk>/download/`**  
  Download a specific uploaded document by its ID.

- **DELETE `/api/documents/<int:pk>/delete/`**  
  Delete a specific document by its ID from the system.

---

