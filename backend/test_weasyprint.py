#!/usr/bin/env python
"""
Test script for WeasyPrint
This script checks if WeasyPrint is installed and working correctly
"""

import sys
import weasyprint
from io import BytesIO
from django.core.files.base import ContentFile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_weasyprint():
    logger.info(f"WeasyPrint version: {getattr(weasyprint, '__version__', 'unknown')}")
    
    # Simple HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test PDF</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 2cm; }
            h1 { color: #4f46e5; }
        </style>
    </head>
    <body>
        <h1>Test PDF Generation</h1>
        <p>This is a test document to verify WeasyPrint is working correctly.</p>
        <p>If you can see this PDF, the conversion worked!</p>
    </body>
    </html>
    """
    
    try:
        logger.info("Creating HTML document...")
        html = weasyprint.HTML(string=html_content)
        
        logger.info("Rendering to PDF...")
        pdf_bytes = html.write_pdf()
        
        # Save to file
        output_path = "test_output.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
            
        logger.info(f"PDF successfully generated and saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Testing WeasyPrint PDF generation...")
    result = test_weasyprint()
    if result:
        print("SUCCESS: WeasyPrint is working correctly!")
        sys.exit(0)
    else:
        print("ERROR: WeasyPrint test failed!")
        sys.exit(1)