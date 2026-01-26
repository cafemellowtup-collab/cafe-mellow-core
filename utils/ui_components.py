"""
Professional UI Components - Replace emojis with icons and modern design
"""
import streamlit as st

def render_professional_button(label, key=None, icon="", type="primary", use_container_width=False):
    """Render professional button without emojis"""
    button_colors = {
        "primary": "#667eea",
        "secondary": "#6c757d",
        "success": "#28a745",
        "danger": "#dc3545",
        "warning": "#ffc107"
    }
    
    color = button_colors.get(type, button_colors["primary"])
    
    button_html = f"""
    <style>
    .btn-professional-{key} {{
        background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
    }}
    .btn-professional-{key}:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    </style>
    """
    
    st.markdown(button_html, unsafe_allow_html=True)
    return st.button(label, key=key, use_container_width=use_container_width)

def render_metric_card(title, value, delta=None, icon=""):
    """Render professional metric card"""
    delta_html = ""
    if delta:
        delta_color = "#28a745" if delta.startswith("+") else "#dc3545" if delta.startswith("-") else "#6c757d"
        delta_html = f'<span style="color: {delta_color}; font-size: 0.9rem;">{delta}</span>'
    
    card_html = f"""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    ">
        <div style="color: #6c757d; font-size: 0.9rem; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 2rem; font-weight: 700; color: #333;">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_info_alert(message, type="info"):
    """Render professional info alert"""
    colors = {
        "info": "#17a2b8",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545"
    }
    color = colors.get(type, colors["info"])
    
    alert_html = f"""
    <div style="
        background: {color}15;
        border-left: 4px solid {color};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #333;
    ">
        {message}
    </div>
    """
    st.markdown(alert_html, unsafe_allow_html=True)

def render_professional_header(title, subtitle=""):
    """Render professional page header"""
    header_html = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    ">
        <h1 style="margin: 0; color: white; font-size: 2.5rem;">{title}</h1>
        {f'<p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
