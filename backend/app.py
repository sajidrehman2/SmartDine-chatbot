from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from firebase_client import db
from nlp import parse_order
import uuid
import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Smart Restaurant Ordering Assistant",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

@app.route('/health')
def health():
    """Detailed health check"""
    try:
        # Test database connection
        db.collection('menus').limit(1).get()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

@app.route('/menu', methods=['GET'])
def get_menu():
    """Get all menu items"""
    try:
        docs = db.collection('menus').where('available', '==', True).stream()
        menu = []
        for doc in docs:
            item = doc.to_dict()
            item['doc_id'] = doc.id
            menu.append(item)
        
        logger.info(f"Retrieved {len(menu)} menu items")
        return jsonify({
            "success": True,
            "menu": menu,
            "count": len(menu)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching menu: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch menu",
            "message": str(e)
        }), 500

@app.route('/menu/<category>', methods=['GET'])
def get_menu_by_category(category):
    """Get menu items by category"""
    try:
        docs = db.collection('menus').where('category', '==', category).where('available', '==', True).stream()
        menu = []
        for doc in docs:
            item = doc.to_dict()
            item['doc_id'] = doc.id
            menu.append(item)
        
        return jsonify({
            "success": True,
            "category": category,
            "menu": menu,
            "count": len(menu)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching menu by category {category}: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch menu by category"
        }), 500

@app.route('/order', methods=['POST'])
def place_order():
    """Process and place an order from natural language input"""
    try:
        data = request.json
        user_text = data.get('message', '').strip()
        user_info = data.get('user', {"name": "Guest", "phone": None})
        
        if not user_text:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400
        
        logger.info(f"Processing order: {user_text}")
        
        # Get menu items
        menu_docs = []
        for doc in db.collection('menus').where('available', '==', True).stream():
            menu_item = doc.to_dict()
            menu_item['doc_id'] = doc.id
            menu_docs.append(menu_item)
        
        menu_names = [item['name'] for item in menu_docs]
        
        # Parse the order using NLP
        parsed = parse_order(user_text, menu_names)
        
        logger.info(f"Parsed result: {parsed}")
        
        # Handle different intents
        if parsed['intent'] in ['greeting', 'help']:
            return jsonify({
                "success": True,
                "intent": parsed['intent'],
                "response": "Hello! Welcome to our restaurant. You can order food by saying something like 'I want 2 pizzas and 1 coke' or ask to 'show menu' to see available items."
            }), 200
        
        elif parsed['intent'] == 'show_menu':
            return jsonify({
                "success": True,
                "intent": parsed['intent'],
                "response": "Here's our menu:",
                "menu": menu_docs
            }), 200
        
        elif parsed['intent'] == 'cancel_order':
            return jsonify({
                "success": True,
                "intent": parsed['intent'],
                "response": "I understand you want to cancel. Please specify your order ID or contact our staff for assistance."
            }), 200
        
        elif parsed['intent'] == 'order_food':
            # Process the food order
            if not parsed['items']:
                return jsonify({
                    "success": False,
                    "error": "No food items found in your message. Please specify what you'd like to order."
                }), 400
            
            # Build order items
            order_items = []
            total_price = 0
            quantities = parsed['quantities'] if parsed['quantities'] else [1] * len(parsed['items'])
            
            # Ensure we have quantities for all items
            while len(quantities) < len(parsed['items']):
                quantities.append(1)
            
            for i, item_name in enumerate(parsed['items']):
                # Find matching menu item
                menu_item = next((m for m in menu_docs if m['name'].lower() == item_name.lower()), None)
                
                if menu_item:
                    quantity = quantities[i] if i < len(quantities) else 1
                    item_total = menu_item['price'] * quantity
                    
                    order_items.append({
                        "item_id": menu_item['item_id'],
                        "name": menu_item['name'],
                        "quantity": quantity,
                        "unit_price": menu_item['price'],
                        "total_price": item_total
                    })
                    total_price += item_total
            
            if not order_items:
                return jsonify({
                    "success": False,
                    "error": "No valid menu items found. Please check the menu and try again."
                }), 400
            
            # Generate order ID
            order_id = f"ORD_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            
            # Create order document
            order_doc = {
                "order_id": order_id,
                "user": user_info,
                "items": order_items,
                "total_price": total_price,
                "status": "Pending",
                "original_message": user_text,
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            }
            
            # Save to database
            db.collection('orders').document(order_id).set(order_doc)
            
            # Log the conversation
            chat_log = {
                "order_id": order_id,
                "sender": "user",
                "message": user_text,
                "timestamp": datetime.datetime.utcnow(),
                "parsed_intent": parsed['intent'],
                "extracted_items": parsed['items']
            }
            db.collection('chat_logs').add(chat_log)
            
            # Add system response to chat log
            response_message = f"Order confirmed! Your order ID is {order_id}. Total: ${total_price}. Items: {', '.join([f'{item['quantity']}x {item['name']}' for item in order_items])}"
            system_log = {
                "order_id": order_id,
                "sender": "system",
                "message": response_message,
                "timestamp": datetime.datetime.utcnow()
            }
            db.collection('chat_logs').add(system_log)
            
            logger.info(f"Order placed successfully: {order_id}")
            
            return jsonify({
                "success": True,
                "intent": parsed['intent'],
                "order": order_doc,
                "response": response_message
            }), 201
        
        else:
            return jsonify({
                "success": True,
                "intent": parsed['intent'],
                "response": "I didn't quite understand that. You can order food, ask for the menu, or get help. Try saying something like 'I want 2 pizzas' or 'show me the menu'."
            }), 200
    
    except Exception as e:
        logger.error(f"Error processing order: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to process order",
            "message": str(e)
        }), 500

@app.route('/orders', methods=['GET'])
def list_orders():
    """Get list of orders with optional filtering"""
    try:
        limit = request.args.get('limit', 50, type=int)
        status_filter = request.args.get('status', None)
        
        query = db.collection('orders').order_by('created_at', direction='DESCENDING').limit(limit)
        
        if status_filter:
            query = query.where('status', '==', status_filter)
        
        docs = query.stream()
        orders = []
        for doc in docs:
            order = doc.to_dict()
            order['doc_id'] = doc.id
            # Convert timestamps to ISO format
            if 'created_at' in order:
                order['created_at'] = order['created_at'].isoformat() if hasattr(order['created_at'], 'isoformat') else str(order['created_at'])
            if 'updated_at' in order:
                order['updated_at'] = order['updated_at'].isoformat() if hasattr(order['updated_at'], 'isoformat') else str(order['updated_at'])
            orders.append(order)
        
        return jsonify({
            "success": True,
            "orders": orders,
            "count": len(orders)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch orders"
        }), 500

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get specific order by ID"""
    try:
        doc = db.collection('orders').document(order_id).get()
        
        if not doc.exists:
            return jsonify({
                "success": False,
                "error": "Order not found"
            }), 404
        
        order = doc.to_dict()
        order['doc_id'] = doc.id
        
        # Convert timestamps
        if 'created_at' in order:
            order['created_at'] = order['created_at'].isoformat() if hasattr(order['created_at'], 'isoformat') else str(order['created_at'])
        if 'updated_at' in order:
            order['updated_at'] = order['updated_at'].isoformat() if hasattr(order['updated_at'], 'isoformat') else str(order['updated_at'])
        
        return jsonify({
            "success": True,
            "order": order
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch order"
        }), 500

@app.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.json
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                "success": False,
                "error": "Status is required"
            }), 400
        
        valid_statuses = ['Pending', 'Confirmed', 'Preparing', 'Ready', 'Delivered', 'Cancelled']
        if new_status not in valid_statuses:
            return jsonify({
                "success": False,
                "error": f"Invalid status. Valid statuses: {valid_statuses}"
            }), 400
        
        # Update order
        db.collection('orders').document(order_id).update({
            'status': new_status,
            'updated_at': datetime.datetime.utcnow()
        })
        
        return jsonify({
            "success": True,
            "message": f"Order {order_id} status updated to {new_status}"
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating order status {order_id}: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to update order status"
        }), 500

@app.route('/chat/<order_id>', methods=['GET'])
def get_chat_history(order_id):
    """Get chat history for an order"""
    try:
        docs = db.collection('chat_logs').where('order_id', '==', order_id).order_by('timestamp').stream()
        chat_history = []
        
        for doc in docs:
            chat = doc.to_dict()
            chat['doc_id'] = doc.id
            if 'timestamp' in chat:
                chat['timestamp'] = chat['timestamp'].isoformat() if hasattr(chat['timestamp'], 'isoformat') else str(chat['timestamp'])
            chat_history.append(chat)
        
        return jsonify({
            "success": True,
            "order_id": order_id,
            "chat_history": chat_history,
            "count": len(chat_history)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching chat history for order {order_id}: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch chat history"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested URL was not found on this server."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred."
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting Smart Restaurant Ordering Assistant on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)