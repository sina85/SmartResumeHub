import time
from classes import log_debug_info

def format_personal_details_into_html(personal_details, filename):
    log_debug_info(f"[S] Formatting personal details {filename}...")
    start_time = time.time()
    res = f"""
    <!-- Name and Contact Information -->
    <h1 style="text-align: center; font-size: 40px; margin-bottom: 5px;">{personal_details.name}</h1>
    <h2 style="text-align: center; font-size: 16px; color: #555;">{personal_details.address}</h2>
    <p style="text-align: center;">{personal_details.phone} | {personal_details.secondary_phone or ''} | {personal_details.email}</p>
    <p style="text-align: center;">Fax: {personal_details.fax}</p>
    """
    elapsed_time = time.time() - start_time
    log_debug_info(f"[D] Formating personal details took {elapsed_time} seconds for {filename} | start_time:{start_time}")
    return res

def format_educational_details_into_html(education_list, filename):
    log_debug_info(f"[S] Formatting educational details {filename}...")
    start_time = time.time()
    education_entries_html = "".join([
        f"""<tr>
                <td style="width: 20%; text-align: left;">{ed.graduation_year}</td>
                <td>
                    <h4 style="font-size: 18px; color: #333; text-align: left;">{ed.degree} in {ed.major}</h4>
                    <p>{ed.institution}, {ed.location}</p>
                    <p>Contact: {ed.contact}</p>
                </td>
            </tr>"""
        for ed in education_list.educations
    ])
    res = f"""
    <!-- Education Section -->
    <h3 style="font-size: 26px; margin-top: 30px; text-align: left;">Education</h3>
    <table style="border: 0px;">
        {education_entries_html}
    </table>
    """
    elapsed_time = time.time() - start_time
    log_debug_info(f"[D] Formating educational details took {elapsed_time} seconds for {filename} | start_time:{start_time}")
    return res

def format_work_experience_details_into_html(work_experiences, T, filename):
    log_debug_info(f"[S] Formatting work experience {filename}...")
    start_time = time.time()
    work_info_html = """
    <!-- Work Experience -->
    <h3 style="font-size: 26px; margin-top: 30px; text-align: left;">Work Experience</h3>
    <table style="border: 0px;">
    """
    for work_experience_list in work_experiences:
        for work_experience in work_experience_list.experiences:
            work_info_html += f"""
            <tr>
                <td style="width: 20%; text-align: left;">{work_experience.start_date} - {work_experience.end_date}</td>
                <td>
                    <h4 style="font-size: 18px; color: #333; text-align: left;">{work_experience.position} at {work_experience.company}, {work_experience.department or ''}</h4>
                    <p>Location: {work_experience.location}</p>
                    <p>Description: {work_experience.description}</p>
                </td>
            </tr>
            """
    if T:
        work_info_html += """
        <tr>
            <td> </td>
            <td><p>"Placeholder"</p></td>
        </tr>
        """
    work_info_html += "</table>"
    elapsed_time = time.time() - start_time
    log_debug_info(f"[D] Formating work experience took {elapsed_time} seconds for {filename} | start_time:{start_time}")
    return work_info_html


def format_other_details_into_html(license_list, certification_list, filename):
    log_debug_info(f"[S] Formatting licenses and certifications {filename}...")

    start_time = time.time()

    licenses_html = "<ul>" + "".join([f'<li style="font-size: 14px; text-align: left;">{lic.license_name} (Exp: {lic.expiration})</li>' for lic in license_list.licenses]) + "</ul>"
    certifications_html = "<ul>" + "".join([f'<li style="font-size: 14px; text-align: left;">{cert.certification_name} (Exp: {cert.expiration})</li>' if cert.expiration else f'<li style="font-size: 14px; text-align: left;">{cert.certification_name}</li>' for cert in certification_list.certifications]) + "</ul>"
    
    res = f"""
    <!-- Licensure -->
    <div>
        <h3 style="font-size: 26px; margin-top: 30px; text-align: left;">Licensure</h3>
        {licenses_html}
    </div>

    <!-- Certifications -->
    <div>
        <h3 style="font-size: 26px; margin-top: 30px; text-align: left;">Certifications</h3>
        {certifications_html}
    </div>
    """
    elapsed_time = time.time() - start_time

    log_debug_info(f"[D] Formating licenses and certifications took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res

def format_final_template(personal, educational, work_experience, other, filename):
    log_debug_info(f"[S] Formatting final template {filename}...")

    start_time = time.time()

    res = f"""
    <section style="text-align: center; width: 33.33%; margin: 0 auto; padding: 20px; max-width: 800px; font-family: 'Arial', sans-serif;">
        {personal}
        <hr />
        {educational}
        <br/>
        {work_experience}
        <br/>
        {other}
        <br/>
    </section>
    """
    elapsed_time = time.time() - start_time

    log_debug_info(f"[D] Formating final template took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res

def get_final_html(final_response):
    return f"""
        <style>
            section {{
                margin: 0 auto; /* Centers the section */
                padding: 20px; /* Adds padding around the section */
                max-width: 800px; /* Sets a maximum width for readability */
                font-family: 'Arial', sans-serif; /* Sets a readable font */
            }}

            /* Centering the top part (Doctor's info) */
            section > h1, 
            section > h2, 
            section > p {{
                text-align: center; /* Center alignment for name, address, and contact */
            }}

            h1, h2, h3, h4, p, li {{
                margin: 0 0 10px 0; /* Adds consistent spacing below each element */
                line-height: 1.6; /* Improves readability with line spacing */
            }}

            h1 {{
                font-size: 40px; /* Larger font size for the name */
                margin-bottom: 5px; /* Reduces space below the name */
            }}

            h2 {{
                font-size: 16px; /* Smaller font size for address */
                color: #555; /* Slightly muted color for less emphasis */
            }}

            h3 {{
                font-size: 26px; /* Emphasizes section headers */
                margin-top: 30px; /* Adds more space above section headers */
                text-align: left; /* Left alignment for section headers */
            }}

            h4 {{
                font-size: 18px; /* Slightly larger font size for sub-headers */
                color: #333; /* Dark color for emphasis */
                text-align: left; /* Left alignment for sub-headers */
            }}

            p, li {{
                font-size: 14px; /* Standard font size for body text */
                text-align: left; /* Left alignment for paragraphs and list items */
            }}

            ul {{
                padding-left: 20px; /* Indents bullet points */
            }}

            @media (max-width: 768px) {{
                section {{
                    padding: 15px; /* Reduces padding on smaller screens */
                }}
            }}
            
            /* CSS for table-like layout */
            .table-row {{
                display: table-row; /* Makes the div behave like a row in a table */
            }}

            .table-cell {{
                display: table-cell; /* Makes the div behave like a cell in a table */
                vertical-align: top; /* Aligns content to the top of the cell */
                padding: 3px; /* Adds some padding inside each cell for spacing */
            }}

            .date-column {{
                width: 20%; /* Sets the width of the date column */
                text-align: left; /* Aligns the text to the left */
            }}
        </style>
        {final_response}
    """