def format_personal_details_into_html(personal_details):
    return f"""
    <!-- Name and Contact Information -->
    <h1 style="text-align: center" class="leading-none text-3xl">{personal_details.name}</h1>
    <h2 style="text-align: center" class="text-sm">{personal_details.address}</h2>
    <p style="text-align: center">{personal_details.phone} | {personal_details.secondary_phone or ''} | {personal_details.email}</p>
    <p style="text-align: center">Fax: {personal_details.fax}</p>
    """

def format_educational_details_into_html(education_list):
    education_entries_html = "".join([
        f"""<tr>
                <td class="table-cell date-column">{ed.graduation_year}</td>
                <td class="table-cell">
                    <h4 class="text-lg">{ed.degree} in {ed.major}</h4>
                    <p>{ed.institution}, {ed.location}</p>
                    <p>Honors: {ed.honors}</p>
                    <p>Contact: {ed.contact}</p>
                </td>
            </tr>"""
        for ed in education_list.educations
    ])
    return f"""
    <!-- Education Section -->
    <h3 class="text-xl mt-8 mb-4">Education</h3>
    <table style="border: 0px;">
        {education_entries_html}
    </table>
    """

def format_work_experience_details_into_html(work_experiences, T):
    work_info_html = """
    <!-- Work Experience -->
    <h3 class="text-xl mt-8 mb-4">Work Experience</h3>
    <table style="border: 0px;">
    """
    print("Starting to format work experiences...")  # Debug print
    for work_experience_list in work_experiences:
        print(f"Processing list: {work_experience_list}")  # Debug print
        for work_experience in work_experience_list.experiences:
            print(f"Adding job: {work_experience.position} at {work_experience.company}")  # Debug print
            work_info_html += f"""
            <tr>
                <td class="table-cell date-column">{work_experience.start_date} - {work_experience.end_date}</td>
                <td class="table-cell">
                    <h4 class="text-lg">{work_experience.position} at {work_experience.company}, {work_experience.department or ''}</h4>
                    <p>Location: {work_experience.location}</p>
                    <p>Hours Worked: {work_experience.hours_worked}</p>
                    <p>Description: {work_experience.description}</p>
                </td>
            </tr>
            """

    if T:
        work_info_html += """
        <tr>
            <td class="table-cell date-column">Affiliations:</td>
            <td class="table-cell"><p>"Placeholder"</p></td>
        </tr>
        """
    
    work_info_html += "</table>"
    print("Final HTML content:")  # Debug print
    print(work_info_html)  # Debug print
    return work_info_html

def format_other_details_into_html(license_list, certification_list):
    licenses_html = "<ul>" + "".join([f"<li>{lic.license_type} - {lic.license_number}, {lic.state_or_country} (Exp: {lic.expiration})</li>" for lic in license_list.licenses]) + "</ul>"
    certifications_html = "<ul>" + "".join([f"<li>{cert.certification_name} - Issued by {cert.issuing_organization} (Exp: {cert.expiration})</li>" if cert.expiration else f"<li>{cert.certification_name} - Issued by {cert.issuing_organization}</li>" for cert in certification_list.certifications]) + "</ul>"
    
    return f"""
    <!-- Licensure -->
    <div>
        <h3 class="text-xl mt-8 mb-4">Licensure</h3>
        {licenses_html}
    </div>

    <!-- Certifications -->
    <div>
        <h3 class="text-xl mt-8 mb-4">Certifications</h3>
        {certifications_html}
    </div>
    """


def format_final_template(personal, educational, work_experience, other):
    return f"""
    <section class="text-center w-1/3">
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

        table {{
            border: 0px;
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
        }}</style>\n{final_response}
    """