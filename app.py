
import streamlit as st
import google.generativeai as genai
import os

# --- Application Page Settings ---
# This MUST be the first Streamlit command in your script.
st.set_page_config(page_title="LLM2LLL Customizable Mentor", page_icon=None)

# --- Default System Prompt ---
DEFAULT_SYSTEM_PROMPT = "You are an experienced mentor for occupational therapists. You must provide professional, supportive and Short answers. Use clear and respectful language."

# --- Model Loading Function (cached based on system_instruction) ---
@st.cache_resource
def get_generative_model(system_instruction_payload):
    # st.sidebar.write(f"DEBUG: Loading/Re-initializing model with system prompt: {system_instruction_payload[:50]}...") # Optional debug
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction_payload
        )
        return model
    except Exception as e:
        st.error(f"Error creating GenerativeModel with the provided system prompt: {e}")
        return None

# --- API Key Configuration ---
ACTUAL_API_KEY = os.environ.get("GOOGLE_API_KEY_FOR_APP")

if not ACTUAL_API_KEY:
    st.error("Critical error: Google API key (GOOGLE_API_KEY_FOR_APP) is missing from environment secrets.")
    st.caption("Please ensure you have correctly set this secret in your deployment platform (e.g., Streamlit Community Cloud settings). The application cannot proceed without it.")
    st.stop() 

try:
    genai.configure(api_key=ACTUAL_API_KEY)
except Exception as e:
    st.error(f"Critical error: Error configuring the Google GenAI API with the provided key: {e}")
    st.caption("This might indicate an invalid API key or a problem with the Google Cloud project.")
    st.stop() 

# --- Sidebar for System Prompt Configuration ---
st.sidebar.header("Mentor Configuration")
custom_system_prompt_from_sidebar = st.sidebar.text_area(
    "Define the mentor's behavior (System Prompt):",
    value=st.session_state.get("system_prompt_for_chat", DEFAULT_SYSTEM_PROMPT), 
    height=250,
    key="system_prompt_input_widget" 
)

if "system_prompt_for_chat" not in st.session_state:
    st.session_state.system_prompt_for_chat = DEFAULT_SYSTEM_PROMPT

if st.sidebar.button("Apply New System Prompt & Restart Chat"):
    if custom_system_prompt_from_sidebar != st.session_state.system_prompt_for_chat:
        st.session_state.system_prompt_for_chat = custom_system_prompt_from_sidebar
        st.session_state.messages = [] 
        if "chat_session" in st.session_state:
            del st.session_state.chat_session 
        if "user_turn_count" in st.session_state: # Reset turn counter as well
            del st.session_state.user_turn_count
        st.sidebar.success("System prompt updated! Chat has been reset.")
        st.experimental_rerun() 
    else:
        st.sidebar.info("System prompt is the same as the current one. No changes applied.")

st.sidebar.markdown("---") 

# --- Load Model ---
model = get_generative_model(st.session_state.system_prompt_for_chat)

if not model:
    st.error("Failed to load/initialize the generative model. Application cannot proceed.")
    st.stop() 

# --- Initialize Session State Variables ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    if not st.session_state.get("messages"): 
         st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today based on the current system prompt?"}]

if "messages" not in st.session_state: 
    st.session_state.messages = []

# Initialize user turn counter for prompt reminder logic
if "user_turn_count" not in st.session_state:
    st.session_state.user_turn_count = 0


# --- Main Application UI ---
st.title("LLM2LLL") 
st.markdown("Welcome! This chat provides mentoring, guidance, and advice for occupational therapists. You can customize the mentor's behavior using the sidebar.") 
st.caption("Powered by Gemini 1.5 Flash")

# --- Displaying Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]): 
        st.markdown(message["content"])

# --- Getting User Input and Processing It ---
if user_input_from_chat := st.chat_input("Type your question here..."):
    # Increment user turn counter each time they send a message
    st.session_state.user_turn_count += 1

    st.session_state.messages.append({"role": "user", "content": user_input_from_chat})
    with st.chat_message("user"): 
        st.markdown(user_input_from_chat)

    if "chat_session" in st.session_state: 
        try:
            chat_session_to_use = st.session_state.chat_session
            
            prompt_to_send_to_llm = user_input_from_chat # Default: original user input
            
            # --- Conditionally augment prompt with system prompt reminder ---
            REMINDER_FREQUENCY = 3 # Remind every 3 user turns
            if st.session_state.user_turn_count % REMINDER_FREQUENCY == 0:
                current_system_prompt_for_llm = st.session_state.get("system_prompt_for_chat", DEFAULT_SYSTEM_PROMPT)
                prompt_to_send_to_llm = f"Remember your core instructions are: '{current_system_prompt_for_llm}'. Now, respond to the user's latest message: '{user_input_from_chat}'"
                # You can add a small visual cue in the sidebar if a reminder was injected:
                # st.sidebar.caption(f"Sys-prompt reminder sent on turn {st.session_state.user_turn_count}.")
            
            # Send the (potentially augmented) prompt to the model
            model_response = chat_session_to_use.send_message(prompt_to_send_to_llm)
            response_text = model_response.text

            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant"): 
                st.markdown(response_text)

        except Exception as e:
            error_for_display = f"Oops, an error occurred while communicating with the model: {e}"
            st.session_state.messages.append({"role": "assistant", "content": error_for_display})
            with st.chat_message("assistant"): 
                st.error(error_for_display)
            st.toast(f"Error: {e}")
    else:
        st.error("Chat session is not initialized. Please ensure the model and system prompt are correctly configured.")
