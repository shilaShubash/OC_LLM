
import streamlit as st
import google.generativeai as genai
import os

# --- Application Page Settings ---
# This MUST be the first Streamlit command in your script.
st.set_page_config(page_title="Occupational Therapy Mentor", page_icon=None)

# --- API Key Configuration ---
# Reading the key from an environment variable defined outside this file (in the Colab cell)
ACTUAL_API_KEY = os.environ.get("GOOGLE_API_KEY_FOR_APP")

if not ACTUAL_API_KEY:
    st.error("Critical error: Google API key is missing in the environment.")
    st.caption("Please ensure you have set the 'GOOGLE_API_KEY' secret in Colab and run the cell that defines it as an environment variable before running this application.")
    st.stop() # Stopping the application if there's no key

try:
    genai.configure(api_key=ACTUAL_API_KEY)
except Exception as e:
    st.error(f"Error configuring the Google GenAI API: {e}")
    st.stop()

# --- Model Loading (with Streamlit's caching mechanism) ---
@st.cache_resource
def load_generative_model():
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction="You are an experienced mentor for occupational therapists. You must provide professional, supportive and Short answers. Use clear and respectful language."
        )
        return model
    except Exception as e:
        st.error(f"Error loading the Gemini model: {e}")
        return None

model = load_generative_model()

if not model:
    st.warning("The model could not be loaded. The application will not be able to function properly.")
    st.stop()

# --- Chat Session and Message History Management ---
# Initialize only if not already present in session_state
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Main Application UI (after page config and setup) ---
st.title("LLM2LLL")
st.markdown("Welcome! This chat provides mentoring, guidance, and advice for occupational therapists.")
st.caption("Powered by Gemini 1.5 Flash")

# --- Displaying Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Getting User Input and Processing It ---
if user_prompt := st.chat_input("Type your question here..."):
    # Adding the user's message to the display and history
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Sending the message to the Gemini model and receiving a response
    try:
        chat_session = st.session_state.chat_session
        model_response = chat_session.send_message(user_prompt)
        response_text = model_response.text

        # Adding the model's response to the display and history
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        with st.chat_message("assistant"):
            st.markdown(response_text)

    except Exception as e:
        error_for_display = f"Oops, an error occurred while communicating with the model: {e}"
        st.session_state.messages.append({"role": "assistant", "content": error_for_display})
        with st.chat_message("assistant"): # Removed emoji avatar
            st.error(error_for_display)
        st.toast(f"Error: {e}") # Removed emoji icon
