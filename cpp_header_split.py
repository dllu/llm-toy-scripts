import os
import sys
from pathlib import Path

import requests

MODEL = "deepseek-r1-distill-llama-70b"
API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
OPENAI_API_KEY = os.getenv("GROQ_TOKEN")


def split_cpp_files(hh, cc):
    hh = Path(hh)
    cc = Path(cc)
    # Read the input file content
    with open(hh, "r") as f:
        hh_code = f.read()
    with open(cc, "r") as f:
        cc_code = f.read()

    # Construct a detailed prompt to minimize unnecessary output
    prompt = "\n".join(
        [
            """You are an expert C++ programmer. I have provided a C++ header file with multiple classes and their implementations in a cc file. I need you to split this into separate .hh and .cc files for each class. 

The input code is:""",
            f"// {hh.name}",
            hh_code,
            "---",
            f"// {cc.name}",
            cc_code,
            """
Please respond ONLY with the split code in the following exact format:
For each class, provide two files: [class_name].hh and [class_name].cc by converting the class name from PascalCase to snake_case
Use your understanding of how the code works in order to #include the appropriate files from each other as necessary.
Most classes are defined in .hh files ending with the class converted to their snake_case, so try to copy the relevant #includes from the original file to the new split files as necessary.
Ensure that the class definitions and implementations remain in the same namespaces as before.
Put #pragma once at the top of header files.
Use '---' as a separator between each class's files
Precede each file with a comment line in the format: // [FileName]
Include ONLY the file content immediately following the comment line
Ensure the code is properly formatted and correct.
Do NOT include ANY explanations, comments, or extra text outside of the file output

The output should look like this example:
// my_class.hh
#pragma once

#include "necessary_includes.hh"
#include "foo.hh"

namespace my_namespace {

class MyClass {
  Foo foo;
 public:
  void my_method();
};
}  // namespace my_namespace

---
// my_class.cc
#include "my_class.hh"

namespace my_namespace {

class MyClass {
public:
  void my_method() {
    // Implementation
  }
}
}  // namespace my_namespace
    """,
        ]
    )

    # Set up the API request
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a C++ expert. Respond ONLY with the split files as described.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 50000,
    }

    # Send the request
    response = requests.post(API_ENDPOINT, json=data, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    result = response.json()["choices"][0]["message"]["content"]

    # Process the result into files
    files = result.split("</think>")[1].split("---")

    # Create an output directory
    output_dir = Path("split_files")
    output_dir.mkdir(exist_ok=True, parents=True)

    for file_content in files:
        print(file_content)
        if not file_content.strip():
            continue

        lines = file_content.strip().split("\n")
        file_path = None

        for line in lines:
            if line.startswith("//"):
                # Extract the file name from the comment
                file_name = line.strip().strip("// ").strip('"')
                file_path = output_dir / file_name
                break

        if not file_path:
            continue  # Skip if no valid file name found

        # Write the file content
        content = "\n".join(lines)
        with open(file_path, "w") as f:
            f.write(content)

    print(f"Files have been created in {output_dir}")


if __name__ == "__main__":
    split_cpp_files(sys.argv[1], sys.argv[2])
