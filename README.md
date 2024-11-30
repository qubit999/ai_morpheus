# AI Morpheus (in development)

AI Morpheus is going to be a web app with similar features like ChatGPT. At this moment, there is no frontend-design, just basic html/css.

## Features
- **Register**
- **Login**
- **Modify Account**
- **Create Inference**
- **Tool Calling**: Google Search, Fetch URL Content, PythonREPL
- **Streaming Responses**

Next (in development):
- **Managing Inference Threads (CRUD)**
- **Frontend Design**
- **Payment Integration**
- **API Key Management**

## Dependencies

Some of the dependencies:
- **FastAPI**
- **langchain**
- **langgraph**
- **Ollama**
- **MongoDB**
- **httpx**
- **pydantic**
- **motor**

Please check requirements.txt to see all.

## Project Structure

- **main.py**: Entry point for the application.
- **ai.py, ai_tools.py**: AI-related functionalities and tools.
- **controller.py**: Handles the business logic and application flow.
- **database.py**: Database connection and ORM setup.
- **helper.py**: Utility functions and helpers.
- **models.py**: Database models and schemas.
- **.env**: Configuration file.

### Static Files

- **static/css/styles.css**: Main stylesheet for the application.
- **static/js/script.js, test.js**: JavaScript files for client-side logic and testing.

### Templates

- **templates/account.html, base.html, index.html, login.html, logout.html, register.html**: HTML templates for various pages.

## Installation

   ```bash
   git clone https://github.com/yourusername/ai_morpheus.git
   cd ai_morpheus
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

You also need to set up a MongoDB database and create the database + collections (messages, payments, settings, threads, users).

   ```bash
   brew tap mongodb/brew
   brew update
   brew install mongodb-community@8.0
   ```

To create the collections, you can use [MongoDB Compass](https://www.mongodb.com/try/download/compass).

## Contributing

Contributions are welcome. 

## License

MIT License

Copyright (c) 2024 Alexander Slatina

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
SOFTWARE.

## Contact 

For any inquiries or support, please contact me here: goodly-rises.0i@icloud.com or through my website linked on my GitHub profile.