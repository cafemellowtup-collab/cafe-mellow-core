"""
Professional Chat Interface Component with Siri-like styling
"""
import streamlit as st
from utils.gemini_chat import chat_with_gemini, get_conversation_history

def render_chat_interface(client, settings):
    """Render the chat interface with professional styling"""
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Load conversation history
        history = get_conversation_history(client, settings)
        for conv in reversed(history):
            st.session_state.messages.append({
                "role": "user",
                "content": conv.get('user_message', '')
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": conv.get('ai_response', '')
            })
    
    # Chat styling
    st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
    }
    .stChatMessage[data-testid="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }
    .stChatMessage[data-testid="assistant"] {
        background: #f0f2f6;
        color: #333;
        margin-right: 20%;
    }
    .chat-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Chat header
    st.markdown("""
    <div class="chat-header">
        <h2 style="color: white; margin: 0;">🤖 TITAN AI Assistant</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Ask me anything about your business - Sales, Expenses, Inventory, Operations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask TITAN about your business data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response with typing indicator
        response = None
        with st.chat_message("assistant"):
            with st.spinner("🤔 TITAN is thinking..."):
                # Get conversation history
                history = get_conversation_history(client, settings)
                
                # Get AI response
                response = chat_with_gemini(client, settings, prompt, history)
                
                # Display response
                st.markdown(response)
        
        # Add assistant message to state
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
