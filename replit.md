# ChatGPT-like Chat Interface

## Overview
A Streamlit-based chat application that provides a ChatGPT-like interface with streaming AI responses using OpenAI's API, plus a built-in skin condition analyzer.

## Features

### Core Chat Features
- Chat interface with streaming AI responses
- Conversation history displayed in chat bubble format
- Model selection (GPT-5, GPT-4o, GPT-4, GPT-3.5-turbo)
- Adjustable temperature and max tokens settings
- Customizable system prompt
- Reset conversation functionality
- Export conversation to JSON
- Import conversation from JSON file
- Quick prompt buttons for common actions
- Dark theme UI with ChatGPT-inspired styling

### Enhanced Features
- **Code Syntax Highlighting**: Markdown code blocks (```language) are rendered with styled code blocks showing the language name
- **Message Editing**: Edit any user or assistant message with the Edit button
- **Message Regeneration**: Regenerate assistant responses or edit user messages and regenerate from that point
- **Message Deletion**: Remove individual messages from the conversation
- **Multiple Chat Sessions**: Create and switch between multiple conversations in the sidebar
- **Conversation Search**: Filter conversations by title or message content
- **Image Analysis**: Upload images (PNG, JPG, JPEG, GIF, WEBP) for vision model analysis

### Skin Condition Analyzer
- Symptom extraction from text input
- Keyword-based matching for 7 skin conditions:
  - Actinic Keratosis (akiec) - pre-cancerous
  - Basal Cell Carcinoma (bcc) - skin cancer
  - Benign Keratosis (bkl) - harmless growths
  - Dermatofibroma (df) - benign nodules
  - Melanoma (mel) - serious skin cancer
  - Melanocytic Nevus (nv) - common moles
  - Vascular Lesions (vasc) - blood vessel related
- Color-coded severity indicators (red for critical, orange for high, green for low, blue for moderate)
- Shows matched symptoms and severity level
- **Treatment suggestions**: Displays specific treatment options for identified condition
- Urgency warnings for conditions requiring immediate medical attention
- Professional consultation recommendations

## Project Structure
- `app.py` - Main Streamlit application
- `.streamlit/config.toml` - Streamlit server configuration

## Running the Application
The application runs on port 5000 using the command:
```
streamlit run app.py --server.port 5000
```

## Environment Variables
- `OPENAI_API_KEY` - Required for AI responses (can also be entered in sidebar)

## Session State
- `conversations`: Dictionary of all chat sessions
- `current_conversation_id`: ID of active conversation
- `editing_message_idx`: Index of message being edited (or None)
- `search_query`: Current search filter text
- `response_in_progress`: Whether AI is currently generating a response

## Recent Changes
- November 28, 2025: Enhanced CSS with modern design - gradient backgrounds, improved shadows, better spacing, and professional typography
- November 28, 2025: Increased max tokens to 2048 - full text responses without truncation
- November 28, 2025: Improved chat layout - 75% max-width bubbles with responsive design and better visual hierarchy
- November 28, 2025: Enabled multi-line response wrapping - full responses display without truncation
- November 28, 2025: Implemented proper chat layout - user messages on right, assistant on left with full HTML bubbles
- November 28, 2025: Fixed response truncation - now using HTML containers with proper text wrapping
- November 28, 2025: Refactored skin analyzer display - results now appear inline in chat sequence right after user message, avoiding duplication
- November 28, 2025: Fixed Gemini API streaming - assistant now properly responds with streaming text in real-time using generate_content_stream()
- November 28, 2025: Integrated skin analyzer into chat flow - auto-analyzes all messages for skin conditions, displays treatments sequentially
- November 26, 2025: Added code syntax highlighting, message editing/regeneration, multiple chat sessions, search, and image upload support
- November 26, 2025: Initial build with modern OpenAI SDK (v1.0+)
