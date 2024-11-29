# AI Morpheus (in development)

AI Morpheus is going to be a web app with similar features like ChatGPT. At this moment, there is no frontend-design, just basic html/css.

## Features
- **Register**
- **Login**
- **Modify Account**
- **Create Inference**
- **Tool Calling**: DuckDuckGo Search, PythonREPL
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

## Contributing

Contributions are welcome. 

## License

Thinking about it... will be updated.

## Contact 

For any inquiries or support, please contact me here: goodly-rises.0i@icloud.com or through my website linked on my GitHub profile.