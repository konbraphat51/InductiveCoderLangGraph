# Specification

## Functions
Use LangGraph to create a LLM agent to conduct inductive coding towards a directory with text/markdown files.

### Analyze

user can specify two modes: categorization and coding

#### Coding
- Force the LLM agent to read all the target files for 2 rounds:
  - 1st round is to read files while taking notes for long-term memory
    - After reading all files, create a code book file.
    - The code book file contains information on which sentence should be the coding target + what code should be applied under what criteria 
  - 2nd round is to give codes to all files based on the code book file.
    - Users can start from 2nd round if they manually created their code book
    - Per file...
      - seperate the text file in sentences, and allocate sentence ID
      - Let LLM to decide to divide the entire text to chunks or not.
        - This is to reduce LLM input tokens per coding
        - No chunking could be better if the target text is not so long.
        - If to divide, let LLM to specify the ranges of chunking.
          - Here, let LLM also decide which chunk NOT to code because of the irrelevance to the user's interest.
      - Per chunk if chuncked, otherwise entire text
        - Let LLM specify all the sets of the sentence ID and what code to apply in a single I/O        

#### Categorization
- Force the LLM agent to read all the target files for 2 rounds:
  - 1st round is to read files while taking notes for long-term memory
    - After reading all files, create a code book file.
    - The code book file contains information on what code should be applied with what criteria
  - 2nd round is to give codes to all files based on the code book file.
    - Users can start from 2nd round if they manually created their code book
    - Give the entire text and code book and retrieve what codes applied (this could be multiple codes per file)

### UI
- Create UI to quickly see where is coded with what codes for each files
- Also line up coded sentences across all files for each codes.

## I/O
### Input
Prompt by the user
- This specifies what the user is interested in, where to look at, and other related context.
- Provide a template file for user to fill to create appropriate prompt.
- Enable user to specify the prompt by filename.

Other parameters necessary

### Output
- Structured Coding Book
- Structured Code files
- UI

## Techs
- use Python 3.12 + uv + LangGraph
  - Allowed to add any useful libraries
- Make the class structure SOLID, and Clean Architecture
- Use strict typing
- Make the tokens I/O as minimal as possible to reduce LLM cost.
