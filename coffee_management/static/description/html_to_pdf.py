import asyncio
from playwright.async_api import async_playwright
import os

async def html_to_pdf_with_toc():
    """
    Converts an HTML file with tabbed content into a single PDF,
    prepending a generated, clickable table of contents.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # --- Use a local web server for reliable image loading ---
        # 1. In your terminal, navigate to the folder with index.html
        # 2. Run: python -m http.server
        await page.goto("http://localhost:8069/coffee_management/static/description/index.html", wait_until="networkidle")

        # --- Step 1: Inject JavaScript to build the ToC ---
        await page.evaluate("""() => {
            const tocContainer = document.createElement('div');
            tocContainer.id = 'table-of-contents';
            
            const tocTitle = document.createElement('h1');
            tocTitle.innerText = 'Table of Contents';
            tocContainer.appendChild(tocTitle);
            
            const tocList = document.createElement('ol');
            const headings = document.querySelectorAll('.tab-content h2');

            headings.forEach((heading, index) => {
                const headingId = `section-${index + 1}`;
                heading.id = headingId; // Add an ID to the heading itself

                const listItem = document.createElement('li');
                const link = document.createElement('a');
                link.href = `#${headingId}`; // Link to the heading's ID
                link.innerText = heading.innerText;
                
                listItem.appendChild(link);
                tocList.appendChild(listItem);
            });
            
            tocContainer.appendChild(tocList);
            document.body.prepend(tocContainer); // Add ToC to the top of the page
        }""")

        # --- Step 2: Inject CSS to style the page for PDF output ---
        await page.add_style_tag(content="""
            /* Style the new Table of Contents */
            #table-of-contents {
                page-break-after: always; /* Puts the ToC on its own page */
            }
            #table-of-contents h1 {
                color: #2a374c;
                border-bottom: 2px solid #714B67;
                padding-bottom: 10px;
            }
            #table-of-contents ol {
                list-style: none;
                padding-left: 5px;
            }
            #table-of-contents li {
                margin: 15px 0;
                font-size: 1.2em;
            }
            #table-of-contents a {
                text-decoration: none;
                color: #4c4c4c;
            }

            /* --- Styles from previous step --- */
            .tabs {
                display: none;
            }
            .tab-content {
                display: block !important;
                page-break-before: always;
                animation: none !important;
            }
            .tab-content:first-of-type {
                page-break-before: auto;
            }
        """)

        # --- Step 3: Save the final PDF ---
        output_filename = "coffee_management_with_toc.pdf"
        await page.pdf(
            path=output_filename,
            format="A4",
            print_background=True,
            margin={"top": "25mm", "bottom": "25mm"}
        )
        await browser.close()
        
        print(f"PDF '{output_filename}' with a ToC generated successfully!")

if __name__ == "__main__":
    asyncio.run(html_to_pdf_with_toc())