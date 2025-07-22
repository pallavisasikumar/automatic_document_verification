from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.generics import ListAPIView
from .models import UploadedDocument
from .serializers import UploadedDocumentSerializer

import mimetypes
import pytesseract
import cv2
import os
import re
from django.conf import settings
from pdf2image import convert_from_path
import tempfile
from datetime import datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status

# Paths
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
poppler_path = r'C:\poppler-24.08.0\Library\bin'

# --- Extract Fields ---
def extract_fields(text, doc_type):
    fields = {"name": None, "dob": None, "document_number": None}
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]

    if doc_type == "aadhaar":
        dob_match = re.search(r'DOB\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})', text)
        fields["dob"] = dob_match.group(1) if dob_match else None

        doc_num_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', text)
        fields["document_number"] = doc_num_match.group(0) if doc_num_match else None

        if dob_match:
            for i, line in enumerate(lines):
                if dob_match.group(0) in line and i > 0:
                    fields["name"] = lines[i - 1]
                    break

    elif doc_type == "passport":
        # 1. Try MRZ lines (bottom 2-3 lines)
        for line in lines[-3:]:
            match = re.search(r"\b([A-Z0-9]{8})<", line)
            if match:
                passport_number = match.group(1)
                if re.match(r"[A-Z][0-9]{7}", passport_number):
                    fields["document_number"] = passport_number
                    break
                elif re.match(r"\d{8}", passport_number):
                    fields["document_number"] = passport_number
                    break

        # 2. DOB
        for i, line in enumerate(lines):
            if "Date of Birth" in line or "DOB" in line:
                dob_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                if not dob_match and i + 1 < len(lines):
                    dob_match = re.search(r'(\d{2}/\d{2}/\d{4})', lines[i + 1])
                if dob_match:
                    fields["dob"] = dob_match.group(1)
                    break

        # 3. Name
        for i, line in enumerate(lines):
            if "Given Name" in line or "Given Names" in line:
                if i + 1 < len(lines):
                    fields["name"] = lines[i + 1].strip().title()
                    break

    return fields

# --- Status Check ---
def determine_status(fields, doc_type):
    mismatches = {}
    valid = 0

    def is_valid_date(date_str):
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            return True
        except:
            return False

    if fields["name"]:
        if re.match(r'^[A-Za-z\s]{3,}$', fields["name"].strip()):
            valid += 1
        else:
            mismatches["name"] = "Invalid format"
    else:
        mismatches["name"] = "Missing"

    if fields["dob"] and is_valid_date(fields["dob"]):
        valid += 1
    else:
        mismatches["dob"] = "Invalid or missing"

    doc_no = fields["document_number"]

    if doc_type == "aadhaar":
        if doc_no and re.match(r"\b\d{4}\s\d{4}\s\d{4}\b", doc_no):
            valid += 1
        else:
            mismatches["document_number"] = "Invalid Aadhaar format"

    elif doc_type == "passport":
        if doc_no and re.match(r"[A-Z]\d{7}", doc_no):
            valid += 1
        else:
            mismatches["document_number"] = "Invalid Passport format"

    if valid >= 2:
        status = "Verified"
    elif valid == 1:
        status = "Pending"
    else:
        status = "Failed"

    return status, mismatches

# --- Upload View ---
@method_decorator(csrf_exempt, name='dispatch')
class FileUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        doc_type = request.data.get('document_type', '').lower()
        file_type, _ = mimetypes.guess_type(file.name)

        doc = UploadedDocument.objects.create(
            file=file,
            file_type=file_type or 'unknown',
            document_type=doc_type,
            uploader_ip=request.META.get('REMOTE_ADDR'),
            device_info=request.META.get('HTTP_USER_AGENT', 'unknown'),
        )

        file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
        text = ""

        try:
            if file.name.lower().endswith('.pdf'):
                images = convert_from_path(file_path, poppler_path=poppler_path)
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                    temp_path = temp_img.name
                    images[0].save(temp_path, 'PNG')
                image = cv2.imread(temp_path)
                text = pytesseract.image_to_string(image)
                os.remove(temp_path)
            else:
                image = cv2.imread(file_path)
                if image is None:
                    raise Exception("Unsupported image or read error")
                text = pytesseract.image_to_string(image)

            print("\u2705 OCR Text:\n", text)
            doc.extracted_text = text

            fields = extract_fields(text, doc_type)
            status, mismatches = determine_status(fields, doc_type)

            doc.name = fields.get('name')
            doc.dob = fields.get('dob')
            doc.passport_no = fields.get('document_number')
            doc.verification_status = status
            doc.save()

        except Exception as e:
            print("\u274c OCR or processing error:", e)

        return Response({
            'status': 'uploaded',
            'document_type': doc.document_type,
            'verification_status': doc.verification_status,
            'fields': {
                'name': doc.name,
                'dob': doc.dob,
                'document_number': doc.passport_no
            },
            'mismatches': mismatches if status != "Verified" else {},
            'raw_text': doc.extracted_text
        })

# --- List Documents View ---
class DocumentsListView(ListAPIView):
    queryset = UploadedDocument.objects.all().order_by('-uploaded_at')
    serializer_class = UploadedDocumentSerializer

class DocumentDownloadView(APIView):
    def get(self, request, pk):
        doc = get_object_or_404(UploadedDocument, pk=pk)
        file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
        else:
            raise Http404("File not found")

class DocumentDeleteView(APIView):
    def delete(self, request, pk):
        doc = get_object_or_404(UploadedDocument, pk=pk)
        doc.delete()
        return Response({"status": "deleted"}, status=status.HTTP_204_NO_CONTENT)
