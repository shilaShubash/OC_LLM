import streamlit as st
import google.generativeai as genai
import os

#Application Page Settings
st.set_page_config(page_title="LLM2LLL Customizable Mentor", page_icon=None)

#Prompts
HARDCODED_SYSTEM_PROMPT = "You are an experienced mentor for occupational therapists. You must provide professional, supportive and Short answers. Use clear and respectful language."
HARDCODED_REMINDER = "Remember to stay supportive and professional." # Leave "" (empty) to disable
REMINDER_FREQUENCY = 3 # The reminder will be injected every N turns


#Model Loading Function
@st.cache_resource
def get_generative_model(system_instruction_payload):
    # Change 2: Removed the debug line that used the sidebar
    # st.sidebar.write(f"DEBUG: ...") 
    try:
        model = genai.GenerativeModel(
            model_name = "models/gemini-2.5-flash",
            system_instruction=system_instruction_payload
        )
        return model
    except Exception as e:
        st.error(f"Error creating GenerativeModel with the provided system prompt: {e}")
        return None

#API Key Configuration
ACTUAL_API_KEY = os.environ.get("GOOGLE_API_KEY_FOR_APP")

if not ACTUAL_API_KEY:
    st.error("Critical error: Google API key (GOOGLE_API_KEY_FOR_APP) is missing from environment secrets.")
    st.caption("Please ensure you have correctly set this secret in your deployment platform. The application cannot proceed.")
    st.stop() 

try:
    genai.configure(api_key=ACTUAL_API_KEY)
except Exception as e:
    st.error(f"Critical error: Error configuring the Google GenAI API with the provided key: {e}")
    st.caption("This might indicate an invalid API key or a problem with the Google Cloud project.")
    st.stop() 

#Initialize Session State Variables (if not already present)
if "user_turn_count" not in st.session_state:
    st.session_state.user_turn_count = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
    

#Load Model based on the main system prompt
model = get_generative_model(HARDCODED_SYSTEM_PROMPT)

if not model:
    st.error("Failed to load/initialize the generative model. Application cannot proceed.")
    st.stop() 

#Chat Session Initialization
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    if not st.session_state.get("messages"): 
         st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today?"}]


# Main Application UI
st.title("LLM2LLL") 
# Change 6: Updated the welcome text (since there is no sidebar)
st.markdown("Welcome! This chat provides mentoring and guidance for occupational therapists.") 
st.caption("Powered by Gemini 2.5 Flash")

#Displaying Chat History 
for message in st.session_state.messages:
    with st.chat_message(message["role"]): 
        st.markdown(message["content"])

#Getting User Input and Processing It 
if user_input_from_chat := st.chat_input("Type your question here..."):
    st.session_state.user_turn_count += 1

    st.session_state.messages.append({"role": "user", "content": user_input_from_chat})
    with st.chat_message("user"): 
        st.markdown(user_input_from_chat)

    if "chat_session" in st.session_state: 
        try:
            chat_session_to_use = st.session_state.chat_session
            
            prompt_to_send_to_llm = user_input_from_chat 
            
            #Using the reminder prompt

            if active_reminder and st.session_state.user_turn_count % REMINDER_FREQUENCY == 0:
                prompt_to_send_to_llm = f"Reminder: '{active_reminder}'. Now, please address the user's message: '{user_input_from_chat}'"
            
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
