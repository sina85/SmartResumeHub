# SmartResumeHub

SmartResumeHub is an intelligent resume processing application that extracts key information from resumes and generates formatted HTML output. It leverages the power of OpenAI's GPT-4 language model to accurately parse and structure the data from resumes in PDF or DOCX format.

## Features

- **Resume Parsing**: SmartResumeHub can process resumes in both PDF and DOCX formats, extracting relevant information such as personal details, educational background, work experience, licenses, and certifications.

- **Pre-processing**: The application performs a pre-processing step to analyze the structure and content of each resume section. It provides a detailed report on the presence, format, and potential issues of each section, enabling more accurate data extraction in subsequent steps.

- **OCR Capability**: SmartResumeHub incorporates Optical Character Recognition (OCR) functionality to handle resumes in PDF format. If the extracted text from a PDF resume is insufficient, the application automatically applies OCR to extract the text from the resume images.

- **Parallel Processing**: To enhance performance and speed up the resume processing, SmartResumeHub utilizes parallel processing techniques. It employs concurrent futures to process multiple resumes simultaneously, optimizing resource utilization and reducing overall processing time.

- **Customizable Templates**: The application generates formatted HTML output based on customizable templates. The templates are designed to present the extracted resume information in a structured and visually appealing manner, with sections for personal details, education, work experience, licenses, and certifications.

- **Doctor and Nurse Resume Handling**: SmartResumeHub provides separate processing pipelines for doctor and nurse resumes. It takes into account the specific requirements and formats of each profession, ensuring accurate extraction and presentation of relevant information.

- **ZIP File Generation**: After processing the resumes, SmartResumeHub generates a ZIP file containing the formatted HTML files for each resume. This allows for convenient distribution and sharing of the processed resumes.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/SmartResumeHub.git
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the OpenAI API key:
   - Create a `config.json` file in the project root directory.
   - Add the following content to the file:
     ```json
     {
       "api_key": "YOUR_API_KEY"
     }
     ```
   - Replace `"YOUR_API_KEY"` with your actual OpenAI API key.

## Usage

1. Run the application:
   ```
   streamlit run main.py
   ```

2. Access the application through the provided URL in your web browser.

3. Upload the doctor and nurse resumes in PDF or DOCX format using the respective file uploader widgets.

4. Click the "Process Files" button to start the resume processing.

5. Once the processing is complete, you can download the processed resumes as ZIP files for doctors and nurses separately.

## Improvements

1. Improve speed by writing a function to find the sweat spot for the amount of task and number of threads to call in parallel.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [OpenAI](https://openai.com) for providing the GPT-4 language model.
- [Streamlit](https://streamlit.io) for the web application framework.
- [PDFMiner](https://github.com/euske/pdfminer) for PDF text extraction.
- [python-docx](https://python-docx.readthedocs.io) for DOCX processing.