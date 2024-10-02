import os
from datetime import datetime

def create_mit_license(project_name, full_name):
    current_year = datetime.now().year
    license_text = f"""MIT License

Copyright (c) {current_year} {full_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

    with open("LICENSE", "w") as license_file:
        license_file.write(license_text)

def create_readme(project_name, description, author, email):
    readme_content = f"""\\documentclass{{article}}
\\usepackage{{hyperref}}

\\title{{{project_name}}}
\\author{{{author}}}

\\begin{{document}}

\\maketitle

\\section{{Description}}
{description}

\\section{{Installation}}
\\begin{{enumerate}}
    \\item Clone this repository
    \\item Install the required dependencies:
    \\begin{{verbatim}}
    pip install -r requirements.txt
    \\end{{verbatim}}
\\end{{enumerate}}

\\section{{Usage}}
[Provide instructions on how to use your project]

\\section{{Features}}
\\begin{{itemize}}
    \\item [List key features of your project]
    \\item ...
\\end{{itemize}}

\\section{{Contributing}}
Contributions are welcome! Please feel free to submit a Pull Request.

\\section{{License}}
This project is licensed under the MIT License - see the \\href{{./LICENSE}}{{LICENSE}} file for details.

\\section{{Contact}}
{author} - \\href{{mailto:{email}}}{{{email}}}

Project Link: [Add your project repository URL here]

\\section{{Acknowledgments}}
\\begin{{itemize}}
    \\item [Add any acknowledgments or credits here]
    \\item ...
\\end{{itemize}}

\\end{{document}}
"""

    with open("README.md", "w") as readme_file:
        readme_file.write(readme_content)

def create_libraries_txt():
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found.")
        return

    with open("requirements.txt", "r") as req_file:
        requirements = req_file.readlines()

    with open("libraries.txt", "w") as lib_file:
        lib_file.write("Project Dependencies:\n\n")
        for req in requirements:
            package = req.strip().split('==')[0]
            version = req.strip().split('==')[1] if '==' in req else 'latest'
            lib_file.write(f"{package},{version}\n")

def main():
    project_name = input("Enter your project name: ")
    description = input("Enter a brief description of your project: ")
    author = input("Enter the author's name: ")
    email = input("Enter the author's email: ")

    create_mit_license(project_name, author)
    create_readme(project_name, description, author, email)
    create_libraries_txt()

    print("Files created successfully: LICENSE, README.md, and libraries.txt")

if __name__ == "__main__":
    main()