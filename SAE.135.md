## Part 5: Project - Interactive Learning Tool

![a bot teacher](https://intra-content-image-bucket.s3.eu-north-1.amazonaws.com/img/h98u9YD.png)

You will design and implement an AI-Powered Learning Companion. This tool will utilize an LLM (like OpenAI's GPT) to generate study questions based on user-provided topics and evaluate freeform answers. It will also allow users to practice, test their knowledge, and track their progress.

We are intentionally leaving some finer implementation details open for you to decide. This encourages you to think critically about program design, user experience, and the practical application of AI tools, not just the technical coding aspects.

<br>

## Core Requirements

When the program starts, the user should be able to choose between the following modes:

- **Generate Questions (using LLM)**
- **Statistics Viewing**
- **Practice Mode (with LLM evaluation)**
- **Test Mode (with LLM evaluation)**
- **Manage Questions** (Enable/Disable/List)

<br>

## Generate Questions Mode (LLM-Powered):

- The user should be prompted to enter a **topic** (e.g., "Python Dictionaries", "Linear Regression Basics", "Convolutional Neural Networks").
- The program will then use an external LLM API (e.g., OpenAI) to generate a set of questions based on this topic.
 - You should aim to generate both **multiple-choice questions** (MCQ) with distinct options and a clearly indicated correct answer and freeform text questions with a reference correct answer.
 - *Hint: Craft clear prompts for the LLM to get structured output (e.g., ask for JSON format, specific delimiters, or particular responses you could parse in Python).*
- The generated questions should be presented to the user for **validation/editing** before being saved. The user should be able to accept, reject, or perhaps even slightly modify the question or answer.
- Accepted questions (along with their type, topic, reference answer/options) should be saved persistently (e.g., in a JSON or CSV file). Each question needs a unique ID.
- The program should handle sensitive information like API keys securely (e.g., loaded from environment variables or a configuration file not committed to Git).
- Error handling for API calls (e.g., network issues, invalid key, rate limits) is crucial.

<br>

## Statistics Viewing Mode:

- Display all questions currently stored.
- For each question, list at a minimum: Unique ID, Active Status, Topic, Question Text, Type (MCQ/Freeform), Source (LLM/Manual), Times Shown (Practice/Test), and Correct Answer Percentage.

<br>

## Manage Questions Mode:

- Allow users to list questions.
- Allow users to turn specific questions on or off using their ID. Disabled questions should not appear in Practice or Test modes.
- Show the details of the question before confirming whether the turn action is on/off.
- Persist the enabled/disabled status.

<br>

## Practice Mode:

- Present active questions to the user.
- Implement a selection strategy where questions answered incorrectly appear more frequently, while correctly answered ones appear less often (weighted random choice based on past performance is suitable).
- For **freeform questions**:
 - Capture the user's text answer.
 - Send the original question, the correct answer, and the user's answer to the LLM API.
 - Prompt the LLM to evaluate if the user's answer is correct based on the reference answer (e.g., asking for a "Correct" or "Incorrect" judgment, possibly with a brief explanation).
 - Use the LLM's judgment to mark the question as correct/incorrect and update statistics.
- For **MCQ questions**: Evaluate correctness directly by comparing the user's choice to the stored correct option.
- Statistics (correct/incorrect counts) should be updated and persisted.

<br>

## Test Mode:

- User selects the number of questions for the test (up to the total number of active questions).
- Questions are chosen randomly from the active pool without repetition within a single test.
- **Freeform questions** are evaluated using the LLM API, similar to Practice Mode.
- **MCQ questions** are evaluated directly.
- At the end of the test, display the final score (e.g., "You answered 7 out of 10 questions correctly").
- Append the score and the date and time to a `results.txt` file.

<br>

## Disable/Enable Questions mode:

Users should be able to write the ID of the question they want to disable or enable. The question information (question text, answer) should be shown, and the user should be asked to confirm if they wish to disable/enable it. Disabled questions should not appear in practice and test modes. The enabled/disabled status should be stored in a file, just like the questions (you should choose whether it is the same file or a different one).

<br>

## Technical Requirements:

- **Object-Oriented Programming (OOP):** Structure your code using classes (e.g., `Question`, `QuizManager`, `LLMClient`). Use constructors, methods, and potential properties/decorators where appropriate.
- **LLM API Integration:** Use an external LLM API (like OpenAI's GPT-4o-mini, 4.1 or newer). Handle API requests, responses, and potential errors gracefully.
- **API Key Security:** Do **NOT** hardcode API keys in your script. Use environment variables or a configuration file (added to `.gitignore`).
- **File I/O:** Persist questions, statistics, and test results to files (e.g., JSON, CSV, plain text).
- **Unit Tests:** Write at least 3 meaningful unit tests for non-API-dependent logic (e.g., testing MCQ evaluation, statistics calculation, file loading/saving logic). Mocking API calls for testing is encouraged but not strictly required for this stage.
- **Git & GitHub:** Use Git for version control and host your project on GitHub. Submit the generated output files (e.g., the question file, `results.txt`) to the repository with your code.

**At the end of the file, add a link to the public GitHub repository that contains your work from the previous hands-on exercise.** If you are ahead in your batch, we expect you might not yet have it entirely done – however, the initial repository should still be there.

<br>

## Reviewer role

First, present the program as if you were presenting it to a potential user. Explain the code as if you are explaining it to a technical team lead. Try to go rather quickly through easy parts and focus more on presenting the most complicated parts of the code.

During a task review, you may get asked questions that test your understanding of covered topics.

**Sample questions for a reviewer to ask (a reviewer is encouraged and expected to think of more, however!)**

- How did you design the prompt(s) for the LLM to generate questions? What challenges did you face?
- How does your program evaluate the correctness of a freeform answer using the LLM? What are the potential limitations of this approach?
- How are you handling the LLM API key securely? Why is this important?
- What happens in your program if the LLM API call fails?
- Explain your OOP structure. Why did you choose these classes?
- What are the benefits and drawbacks of storing data in JSON vs CSV format for this project?
- Walk me through your weighted random selection logic in Practice Mode.

<br>

## Project Evaluation Criteria:

- **LLM Question Generation:** The Program successfully uses LLM to generate questions based on a topic; the user can validate/save them.
- **LLM Freeform Evaluation:** Program correctly uses LLM to evaluate freeform answers in Practice and Test modes.
- **Core Functionality:** Statistics viewing, Question management (Enable/Disable), Practice mode logic (weighted selection), and Test mode logic (random selection, scoring) work correctly.
- **OOP Implementation:** Code demonstrates reasonable use of OOP principles.
- **API Handling:** LLM API is integrated correctly; API key security is maintained; basic error handling for API calls is present.
- **Persistence:** Questions, stats, and test results are saved to and loaded from files correctly.
- **Unit Tests:** At least 3 meaningful unit tests are included.
- **Git Usage:** Repository is well-maintained.

<br>


## Submission:

Read an [in-depth guide about reviews here](https://doku.turingcollege.com/p/0771306d-bc1e-4b00-9153-c63adeb63a85).

### Submission and Scheduling a Project Review

To submit the project and allow the reviewer to view your work beforehand, you need to use the Github repository that has been created for you.
Please go through these material to learn more about submitting projects, scheduling project reviews and using Github:

- [Completing a Sprint, Submitting a Project and Scheduling Reviews](https://doku-v02-production.up.railway.app/p/f3dbf8bc-2dae-4230-938d-3144110ea74a)
- [Git and GitHub for Beginners](https://www.youtube.com/watch?v=RGOj5yH7evk)


<br>

**Estimate average time to complete: 25-30 hours**
