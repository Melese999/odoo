import asyncio
from playwright.async_api import async_playwright
import os # Recommended for handling file paths

async def html_to_pdf():
    """
    Converts an HTML file with tabbed content into a single,
    multi-page PDF containing all tab sections.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # --- Use an absolute path to ensure the file is found ---
        # Get the directory where the script is running
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # IMPORTANT: Replace 'index.html' with the correct path to your file
        # For example: file_path = os.path.join(script_dir, 'static', 'description', 'index.html')
        file_path = os.path.abspath("index.html") # Assuming index.html is in the same folder as the script
        
        await page.goto(f"file://{file_path}", wait_until="networkidle")

        # --- This is the key step ---
        # Inject CSS to make all tab content visible and format for printing
        await page.add_style_tag(content="""
            /* Hide the tab buttons, as they are not needed in the PDF */
            .tabs {
                display: none;
            }
            /* Force all tab content sections to be visible */
            .tab-content {
                display: block !important; /* This is the crucial rule */
                page-break-before: always; /* Start each section on a new page */
                animation: none !important; /* Disable animations */
            }
            /* Ensure the first section doesn't have a page break before it */
            .tab-content:first-of-type {
                page-break-before: auto;
            }
        """)

        # Save the modified page as a PDF
        output_filename = "coffee_management_documentation.pdf"
        await page.pdf(
            path=output_filename,
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}
        )
        await browser.close()
        
        print(f"PDF '{output_filename}' generated successfully!")

# Run the asynchronous function
if __name__ == "__main__":
    asyncio.run(html_to_pdf())
    print("PDF generated successfully!")