from unstructured.partition.pdf import partition_pdf
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The extracted text from the PDF.
    """
    elements = partition_pdf(filename=pdf_path)
    text = "\n".join([element.text for element in elements if hasattr(element, 'text')])
    return text


def get_info_from_text(text):
    """
    Extract structured information from resume text using OpenAI API.
    
    Args:
        text (str): Resume text to parse
        
    Returns:
        dict: Extracted resume information in JSON format
    """
    
    prompt = f"""
    Extract the following information from the resume text and return it as a valid JSON object. 
    Be intelligent about parsing dates, locations, and skills. If information is not available, use null.

    Resume Text:
    {text}

    Please extract and structure the information into the following JSON format:

    {{
        "personal_info": {{
            "name": "Full name",
            "email": "Email address",
            "phone": "Phone number",
            "location": {{
                "city": "City",
                "state": "State/Province",
                "country": "Country"
            }},
            "linkedin": "LinkedIn URL",
            "github": "GitHub URL",
            "portfolio": "Portfolio website URL"
        }},
        "summary": "Professional summary or objective statement",
        "experience": [
            {{
                "company": "Company name",
                "position": "Job title",
                "location": "Job location",
                "start_date": "YYYY-MM format",
                "end_date": "YYYY-MM format or 'Present'",
                "responsibilities": ["List of key responsibilities and achievements"],
                "technologies": ["Technologies/tools used"]
            }}
        ],
        "education": [
            {{
                "institution": "School/University name",
                "degree": "Degree type and field",
                "location": "Institution location",
                "start_date": "YYYY-MM or YYYY",
                "end_date": "YYYY-MM or YYYY",
                "gpa": "GPA if mentioned"
            }}
        ],
        "skills": {{
            "technical": ["Technical skills"],
            "programming_languages": ["Programming languages"],
            "frameworks": ["Frameworks and libraries"],
            "tools": ["Tools and software"],
            "soft_skills": ["Soft skills"]
        }},
        "projects": [
            {{
                "name": "Project name",
                "description": "Project description",
                "technologies": ["Technologies used"],
                "url": "Project URL if available"
            }}
        ],
        "certifications": [
            {{
                "name": "Certification name",
                "issuer": "Issuing organization",
                "date": "YYYY-MM"
            }}
        ]
    }}

    Important instructions:
    1. Be intelligent about date parsing - convert various date formats to standardized YYYY-MM format
    2. Extract skills smartly - categorize them appropriately
    3. If a field is not present in the resume, use null
    4. For arrays, if no items exist, use empty array []
    5. Extract email addresses, phone numbers, and URLs accurately
    6. Don't hallucinate information not present in the resume

    Return only the JSON object, no additional text.
    """
    
    try:
        # Make API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" for cost efficiency
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume parser. Extract information accurately and return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        # Extract JSON from response
        json_text = response.choices[0].message.content.strip()
        
        # Clean up the response (remove any markdown formatting)
        if json_text.startswith("```json"):
            json_text = json_text[7:-3]
        elif json_text.startswith("```"):
            json_text = json_text[3:-3]

        # store the raw JSON text for debugging
        with open("resume_extraction.json", "w") as debug_file:
            debug_file.write(json_text)
        
        # Parse and return JSON
        return json.loads(json_text)
        
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}"}
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}


if __name__ == "__main__":
    # Example usage:
    # Replace with your PDF file path
    pdf_path = "Yutong-GenAI Engineer.pdf"
    
    # Extract text from the PDF
    resume_text = extract_text_from_pdf(pdf_path)
    
    # Get structured information from the resume text
    resume_info = get_info_from_text(resume_text)
    
    # Print the extracted information
    print(json.dumps(resume_info, indent=2))
# text = extract_text_from_pdf("Yutong-GenAI Engineer.pdf")
# resume_info = get_info_from_text(text)
# Save the extracted information to a JSON file
# print(json.dumps(resume_info, indent=2))