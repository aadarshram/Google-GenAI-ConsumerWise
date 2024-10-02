import os
import ast
from datetime import datetime

def create_mit_license(full_name):
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
    readme_content = f"""# {project_name}

## Description
{description}

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Installation
1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
[Provide instructions on how to use your project]

## Features
- [List key features of your project]
- ...

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
{author} - {email}

Project Link: [Add your project repository URL here]

## Acknowledgments
- [Add any acknowledgments or credits here]
- ...
"""

    with open("README.md", "w") as readme_file:
        readme_file.write(readme_content)

def scan_for_imports(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:  # absolute import
                imports.add(node.module.split('.')[0])
    
    return imports

def create_libraries_txt():
    all_imports = set()
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                all_imports.update(scan_for_imports(file_path))
    
    # Remove standard library modules
    standard_libs = set(['os', 'sys', 'datetime', 'math', 'random', 'time', 'json', 're', 'collections', 'itertools'])
    third_party_imports = all_imports - standard_libs
    
    with open("libraries.txt", "w") as lib_file:
        lib_file.write("Project Dependencies:\n\n")
        for lib in sorted(third_party_imports):
            lib_file.write(f"{lib}\n")

def main():
    project_name = input("Enter your project name: ")
    description = input("Enter a brief description of your project: ")
    author = input("Enter the author's name: ")
    email = input("Enter the author's email: ")

    create_mit_license(author)
    create_readme(project_name, description, author, email)
    create_libraries_txt()

    print("Files created successfully: LICENSE, README.md, and libraries.txt")

if __name__ == "__main__":
    main()