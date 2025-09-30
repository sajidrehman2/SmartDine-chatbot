import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Configure the page
st.set_page_config(
    page_title="Sajid SmartDine - AI Restaurant Assistant",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL configuration
try:
    BACKEND_URL = st.secrets["BACKEND_URL"]
except (KeyError, FileNotFoundError):
    BACKEND_URL = "http://localhost:5000"

# Enhanced CSS with vibrant gradients and animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        padding: 1rem 2rem;
    }
    
    /* Vibrant Custom Header */
    .custom-header {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 50%, #ffa500 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(240, 147, 251, 0.4);
        animation: headerGlow 3s ease-in-out infinite alternate;
    }
    
    @keyframes headerGlow {
        0% { box-shadow: 0 10px 40px rgba(240, 147, 251, 0.4); }
        100% { box-shadow: 0 15px 50px rgba(245, 87, 108, 0.5); }
    }
    
    .custom-header h1 {
        color: white;
        font-size: 3.5rem;
        margin: 0;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    .custom-header p {
        color: white;
        font-size: 1.3rem;
        margin: 0.8rem 0 0 0;
        opacity: 0.95;
        font-weight: 500;
    }
    
    .status-badge-header {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
        padding: 0.6rem 1.5rem;
        border-radius: 30px;
        margin-top: 1rem;
        border: 2px solid rgba(255, 255, 255, 0.3);
        font-weight: 600;
    }
    
    .status-dot-online {
        width: 14px;
        height: 14px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 15px #10b981;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.1); }
    }
    
    /* Menu Card Styling */
    .menu-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.35);
        transition: all 0.3s ease;
    }
    
    .menu-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(102, 126, 234, 0.45);
    }
    
    .menu-card h3 {
        color: white;
        margin-top: 0;
        font-size: 1.8rem;
        text-align: center;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .menu-content {
        background: rgba(255, 255, 255, 0.15);
        padding: 1.5rem;
        border-radius: 15px;
        backdrop-filter: blur(15px);
        border: 2px solid rgba(255, 255, 255, 0.25);
    }
    
    .menu-item {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
        border-radius: 18px;
        padding: 1.8rem;
        margin: 1.2rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        border: 2px solid transparent;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .menu-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        transition: left 0.5s;
    }
    
    .menu-item:hover::before {
        left: 100%;
    }
    
    .menu-item:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 15px 45px rgba(102, 126, 234, 0.3);
        border-color: #667eea;
    }
    
    .menu-item h4 {
        color: #1e293b;
        font-weight: 700;
        margin-bottom: 0.8rem;
        font-size: 1.4em;
    }
    
    .menu-item p {
        color: #64748b;
        margin: 0.6rem 0;
        line-height: 1.7;
        font-size: 1em;
    }
    
    .price-tag {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff1744 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        font-weight: 700;
        font-size: 1.3em;
        display: inline-block;
        margin: 1rem 0;
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
        transition: all 0.3s ease;
    }
    
    .price-tag:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 30px rgba(255, 107, 107, 0.5);
    }
    
    /* Chat Container */
    .chat-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.35);
    }
    
    .chat-container h3 {
        color: white;
        text-align: center;
        margin-top: 0;
        font-size: 1.8rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .stChatMessage {
        background: white;
        border-radius: 18px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 2px solid rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    
    .stChatMessage:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 30px rgba(0, 0, 0, 0.12);
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 30px;
        padding: 0.9rem 2.2rem;
        font-weight: 700;
        font-size: 1em;
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 35px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Success/Error Cards */
    .success-card {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 1.5rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(86, 171, 47, 0.35);
        font-weight: 600;
    }
    
    .error-card {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1.5rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(255, 65, 108, 0.35);
        font-weight: 600;
    }
    
    /* Order Card Styling */
    .order-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        border-left: 6px solid #f093fb;
        transition: all 0.3s ease;
    }
    
    .order-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.15);
    }
    
    .order-item {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-radius: 15px;
        border-left: 4px solid #ff6b6b;
        transition: all 0.3s ease;
        font-weight: 600;
    }
    
    .order-item:hover {
        transform: translateX(8px);
        box-shadow: 0 6px 25px rgba(255, 107, 107, 0.25);
    }
    
    /* Status Badges */
    .status-badge {
        padding: 0.6rem 1.3rem;
        border-radius: 25px;
        font-weight: 700;
        display: inline-block;
        font-size: 0.9em;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        transition: all 0.2s ease;
    }
    
    .status-badge:hover {
        transform: scale(1.05);
    }
    
    .status-pending {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        color: white;
    }
    
    .status-confirmed {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
    }
    
    .status-preparing {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .status-ready {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .status-delivered {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    .status-cancelled {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        border: 3px solid transparent;
        background-clip: padding-box;
        position: relative;
        transition: all 0.3s ease;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 20px;
        padding: 3px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 50px rgba(240, 147, 251, 0.3);
    }
    
    .metric-value {
        font-size: 3.5em;
        font-weight: 800;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: #64748b;
        font-size: 1.1em;
        font-weight: 600;
    }
    
    /* Badge Styling */
    .badge {
        padding: 0.5rem 1.1rem;
        border-radius: 25px;
        font-size: 0.85em;
        font-weight: 700;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    
    .badge:hover {
        transform: scale(1.05);
    }
    
    .badge-available {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
    }
    
    .badge-unavailable {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
    }
    
    .badge-veg {
        background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%);
        color: white;
    }
    
    .badge-nonveg {
        background: linear-gradient(135deg, #ffd89b 0%, #ff9a76 100%);
        color: #333;
    }
    
    .badge-spicy {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff1744 100%);
        color: white;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
        border-radius: 15px;
        border: 3px solid #f093fb;
        font-weight: 700;
        transition: all 0.3s ease;
        padding: 1rem 1.5rem;
    }
    
    .streamlit-expanderHeader:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(240, 147, 251, 0.3);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #64748b;
        font-size: 1em;
        border-top: 3px solid transparent;
        border-image: linear-gradient(90deg, #f093fb 0%, #f5576c 100%) 1;
        margin-top: 3rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def render_custom_header(is_online):
    """Render vibrant custom header"""
    status_html = f'<div class="status-badge-header"><div class="status-dot-online"></div>System Online</div>' if is_online else '<div class="status-badge-header">System Offline</div>'
    
    st.markdown(f"""
    <div class="custom-header">
        <h1>🍽️ Sajid SmartDine</h1>
        <p>AI-Powered Restaurant Ordering Experience</p>
        {status_html}
    </div>
    """, unsafe_allow_html=True)

def make_request(endpoint, method="GET", data=None):
    """Make HTTP request to backend API"""
    try:
        url = f"{BACKEND_URL}/{endpoint.lstrip('/')}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        return response.json()
    
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {BACKEND_URL}")
        st.info("Make sure the backend server is running and the URL is correct.")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid response from server")
        return None

def display_menu():
    """Display the restaurant menu with enhanced styling"""
    st.markdown('<div class="menu-card"><h3>📖 Our Delicious Menu</h3><div class="menu-content">', unsafe_allow_html=True)
    
    menu_data = make_request("menu")
    
    if menu_data and menu_data.get("success"):
        menu_items = menu_data.get("menu", [])
        
        if not menu_items:
            st.info("No menu items available at the moment.")
            st.markdown('</div></div>', unsafe_allow_html=True)
            return
        
        categories = {}
        for item in menu_items:
            category = item.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        for category, items in categories.items():
            st.markdown(f"### {category}")
            
            cols = st.columns(3)
            
            for idx, item in enumerate(items):
                with cols[idx % 3]:
                    available_badge = f'<span class="badge badge-available">✓ Available</span>' if item.get('available') else f'<span class="badge badge-unavailable">✗ Unavailable</span>'
                    veg_badge = f'<span class="badge badge-veg">🥬 Veg</span>' if item.get('vegetarian') else f'<span class="badge badge-nonveg">🥩 Non-Veg</span>'
                    spicy_badge = f'<span class="badge badge-spicy">🌶️ Spicy</span>' if item.get('spicy') else ''
                    
                    st.markdown(f"""
                    <div class="menu-item">
                        <h4>{item.get('name', 'Unknown')}</h4>
                        <p>{item.get('description', 'No description available')}</p>
                        <div class="price-tag">💰 PKR {item.get('price', 0)}</div>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1rem;">
                            {available_badge}
                            {veg_badge}
                            {spicy_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Quick Order", key=f"order_{item.get('item_id')}", use_container_width=True):
                        st.session_state.quick_order = item.get('name')
                        st.rerun()
    else:
        st.error("Failed to load menu. Please try again later.")
    
    st.markdown('</div></div>', unsafe_allow_html=True)

def display_orders():
    """Display order history with enhanced cards"""
    st.markdown("## 📋 Order History")
    
    orders_data = make_request("orders?limit=20")
    
    if orders_data and orders_data.get("success"):
        orders = orders_data.get("orders", [])
        
        if not orders:
            st.info("No orders found.")
            return
        
        for order in orders:
            status = order.get('status', 'Unknown')
            status_class = f"status-{status.lower()}"
            
            with st.expander(f"🎫 Order #{order.get('order_id', 'Unknown')[:8]} - PKR {order.get('total_price', 0)}", expanded=False):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**👤 Customer:** {order.get('user', {}).get('name', 'Guest')}")
                    st.markdown(f'**📊 Status:** <span class="status-badge {status_class}">{status}</span>', unsafe_allow_html=True)
                    st.markdown(f"**💰 Total:** PKR {order.get('total_price', 0)}")
                    
                    created_at = order.get('created_at', 'Unknown')
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    st.markdown(f"**🕐 Created:** {created_at}")
                
                with col2:
                    st.markdown("**🛒 Items:**")
                    for item in order.get('items', []):
                        st.markdown(f"""
                        <div class="order-item">
                            <strong>{item.get('quantity', 1)}x {item.get('name', 'Unknown')}</strong> - PKR {item.get('total_price', 0)}
                        </div>
                        """, unsafe_allow_html=True)
                
                if order.get('original_message'):
                    st.markdown(f"**💬 Original Message:** *'{order['original_message']}'*")
                
                st.markdown("---")
                
                col_status1, col_status2 = st.columns([3, 1])
                
                with col_status1:
                    new_status = st.selectbox(
                        "Update Status:",
                        ["Pending", "Confirmed", "Preparing", "Ready", "Delivered", "Cancelled"],
                        index=["Pending", "Confirmed", "Preparing", "Ready", "Delivered", "Cancelled"].index(order.get('status', 'Pending')),
                        key=f"status_{order.get('order_id')}"
                    )
                
                with col_status2:
                    if st.button("Update", key=f"update_{order.get('order_id')}", use_container_width=True):
                        update_data = {"status": new_status}
                        result = make_request(f"orders/{order.get('order_id')}/status", "PUT", update_data)
                        
                        if result and result.get("success"):
                            st.success(f"Status updated to {new_status}")
                            st.rerun()
                        else:
                            st.error("Failed to update status")
    else:
        st.error("Failed to load orders. Please try again later.")

def chat_interface():
    """Main chat interface for placing orders"""
    st.markdown('<div class="chat-container"><h3>💬 Chat with AI Assistant</h3></div>', unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "🍽️ Welcome to Sajid SmartDine! I'm your AI ordering assistant. What delicious food can I help you with today? Try saying 'I want 2 pizzas' or 'show menu'!"}
        ]
    
    if "quick_order" in st.session_state and st.session_state.quick_order:
        quick_item = st.session_state.quick_order
        user_message = f"I want 1 {quick_item}"
        st.session_state.messages.append({"role": "user", "content": user_message})
        
        order_data = {"message": user_message}
        result = make_request("order", "POST", order_data)
        
        if result:
            if result.get("success"):
                if result.get("intent") == "order_food" and result.get("order"):
                    response = result.get("response", "Order processed successfully!")
                else:
                    response = result.get("response", "Thank you for your message!")
            else:
                response = f"Sorry, I couldn't process that: {result.get('error', 'Unknown error')}"
        else:
            response = "Sorry, I'm having trouble connecting right now. Please try again."
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.quick_order = None
        st.rerun()
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if prompt := st.chat_input("Tell me what you'd like to order..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Processing your order..."):
                order_data = {"message": prompt}
                result = make_request("order", "POST", order_data)
                response = ""
                
                if result:
                    if result.get("success"):
                        if result.get("intent") == "order_food" and result.get("order"):
                            order = result["order"]
                            response = result.get("response", "Order processed successfully!")
                            
                            st.write(response)
                            
                            st.markdown('<div class="success-card">', unsafe_allow_html=True)
                            st.markdown(f"### 🧾 Order Summary")
                            st.markdown(f"**🎫 Order ID:** `{order.get('order_id')}`")
                            st.markdown(f"**💰 Total:** PKR {order.get('total_price')}")
                            st.markdown("**🛒 Items:**")
                            
                            for item in order.get('items', []):
                                st.write(f"- {item['quantity']}x {item['name']} @ PKR {item['unit_price']} = PKR {item['total_price']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        elif result.get("intent") == "show_menu" and result.get("menu"):
                            response = result.get("response", "Here's our menu:")
                            st.write(response)
                            
                            for item in result["menu"]:
                                if item.get("available"):
                                    st.write(f"• {item['name']} - PKR {item['price']}")
                                    if item.get("description"):
                                        st.caption(item["description"])
                        
                        else:
                            response = result.get("response", "Thank you for your message!")
                            st.write(response)
                    else:
                        error_msg = f"Sorry, I couldn't process that: {result.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        response = error_msg
                else:
                    response = "Sorry, I'm having trouble connecting right now. Please try again."
                    st.error(response)
                
                st.session_state.messages.append({"role": "assistant", "content": response})

def system_status():
    """Display system status and health"""
    st.markdown("## 🔧 System Status")
    
    health_data = make_request("health")
    
    if health_data:
        st.markdown('<div class="success-card">✅ Backend is running smoothly</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**🔧 Service:** {health_data.get('service', 'Unknown')}")
            st.markdown(f"**📌 Version:** {health_data.get('version', 'Unknown')}")
        
        with col2:
            st.markdown(f"**💾 Database:** {health_data.get('database', 'Unknown')}")
            timestamp = health_data.get("timestamp", "Unknown")
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    pass
            st.markdown(f"**⏰ Last Check:** {timestamp}")
    else:
        st.markdown('<div class="error-card">❌ Backend is not responding</div>', unsafe_allow_html=True)
        st.info(f"Backend URL: {BACKEND_URL}")
    
    st.markdown("### ⚙️ Configuration")
    st.code(f"Backend URL: {BACKEND_URL}", language="text")
    
    st.markdown("### 📊 Statistics")
    
    menu_data = make_request("menu")
    menu_count = len(menu_data.get("menu", [])) if menu_data and menu_data.get("success") else 0
    
    orders_data = make_request("orders?limit=1000")
    orders_count = len(orders_data.get("orders", [])) if orders_data and orders_data.get("success") else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{menu_count}</div>
            <div class="metric-label">Menu Items</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{orders_count}</div>
            <div class="metric-label">Total Orders</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        status_icon = "✓" if health_data else "✗"
        status_text = "Online" if health_data else "Offline"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{status_icon}</div>
            <div class="metric-label">Backend {status_text}</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application"""
    
    # Check backend status
    health_data = make_request("health")
    is_online = health_data is not None
    
    # Render custom header
    render_custom_header(is_online)
    
    # Sidebar
    st.sidebar.title("🎯 Navigation")
    page = st.sidebar.radio("", [
        "💬 Chat & Order", 
        "🍽️ View Menu", 
        "📋 Order History",
        "🔧 System Status"
    ], label_visibility="collapsed")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configuration")
    backend_url = st.sidebar.text_input("Backend URL:", value=BACKEND_URL)
    
    if backend_url != BACKEND_URL:
        globals()['BACKEND_URL'] = backend_url.rstrip('/')
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Quick Actions")
    
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
        if "messages" in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "🍽️ Welcome to Sajid SmartDine! I'm ready to take your next order. What can I get started for you today?"}
            ]
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💡 Try These Examples")
    sample_queries = [
        "I want 2 chicken pizzas",
        "Show me the menu",
        "Give me a burger and fries", 
        "I need 3 samosas and 2 teas",
        "What do you have?"
    ]
    
    for query in sample_queries:
        if st.sidebar.button(f"💬 {query}", key=f"sample_{hash(query)}", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            
            st.session_state.messages.append({"role": "user", "content": query})
            
            order_data = {"message": query}
            result = make_request("order", "POST", order_data)
            
            if result and result.get("success"):
                response = result.get("response", "Thank you for your message!")
            else:
                response = "Sorry, I'm having trouble right now. Please try again."
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    # Main content
    if page == "💬 Chat & Order":
        chat_interface()
    elif page == "🍽️ View Menu":
        display_menu()
    elif page == "📋 Order History":
        display_orders()
    elif page == "🔧 System Status":
        system_status()
    
    # Footer
    st.markdown("""
    <div class="footer">
        🍽️ Sajid SmartDine - Powered by AI | Made with ❤️ and Streamlit<br>
        <em>Smart Restaurant Ordering Assistant v1.0</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()