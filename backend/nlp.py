import re
import logging
from typing import List, Dict, Any
from rapidfuzz import process, fuzz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import advanced NLP libraries, fallback to basic processing if not available
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers library available - using advanced NLP")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.info("Transformers not available - using basic NLP processing")

try:
    from word2number import w2n
    WORD2NUMBER_AVAILABLE = True
except ImportError:
    WORD2NUMBER_AVAILABLE = False
    logger.info("word2number not available - using basic number parsing")

class RestaurantNLP:
    """NLP processor for restaurant orders"""
    
    def __init__(self):
        self.intent_classifier = None
        self.setup_models()
        
        # Define intent patterns
        self.intent_patterns = {
            'order_food': [
                r'\b(want|need|order|get|give me|i\'ll have|can i have)\b',
                r'\b(pizza|burger|chicken|food|drink|eat)\b',
                r'\b\d+\b.*\b(pizza|burger|chicken|coke|tea|coffee)\b'
            ],
            'show_menu': [
                r'\b(menu|what do you have|what\'s available|show|list)\b',
                r'\b(see.*menu|menu.*please)\b'
            ],
            'cancel_order': [
                r'\b(cancel|remove|delete|stop)\b.*\b(order)\b',
                r'\b(don\'t want|changed my mind)\b'
            ],
            'greeting': [
                r'\b(hello|hi|hey|good morning|good evening)\b',
                r'\b(how are you|what\'s up)\b'
            ],
            'help': [
                r'\b(help|how|what can)\b',
                r'\b(assist|support|guide)\b'
            ]
        }
        
        # Common quantity words
        self.quantity_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'a': 1, 'an': 1, 'single': 1, 'double': 2, 'triple': 3,
            'couple': 2, 'few': 3, 'several': 3, 'dozen': 12, 'half': 0.5
        }
        
    def setup_models(self):
        """Initialize NLP models"""
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight model for intent classification
                self.intent_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1  # Use CPU to avoid GPU issues
                )
                logger.info("Intent classifier loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
                self.intent_classifier = None
    
    def classify_intent(self, text: str) -> str:
        """Classify the intent of the input text"""
        text_lower = text.lower()
        
        # First try pattern matching (fast and reliable)
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    logger.debug(f"Intent '{intent}' matched by pattern: {pattern}")
                    return intent
        
        # If no pattern match and transformer is available, use it
        if self.intent_classifier is not None:
            try:
                candidate_intents = ["order_food", "show_menu", "cancel_order", "greeting", "help"]
                result = self.intent_classifier(text, candidate_intents)
                intent = result['labels'][0]
                confidence = result['scores'][0]
                
                # Only trust high confidence predictions
                if confidence > 0.5:
                    logger.debug(f"Intent '{intent}' classified by transformer with confidence {confidence:.2f}")
                    return intent
                else:
                    logger.debug(f"Low confidence classification ({confidence:.2f}), defaulting to order_food")
            except Exception as e:
                logger.error(f"Error in transformer classification: {e}")
        
        # Default to order_food if no clear intent found
        return "order_food"
    
    def extract_quantities(self, text: str) -> List[int]:
        """Extract quantities from text"""
        quantities = []
        text_lower = text.lower()
        
        # Find digit numbers
        digit_matches = re.findall(r'\b\d+\b', text)
        quantities.extend([int(match) for match in digit_matches])
        
        # Find word numbers
        words = text_lower.split()
        for word in words:
            if word in self.quantity_words:
                quantities.append(self.quantity_words[word])
        
        # Try word2number library if available
        if WORD2NUMBER_AVAILABLE:
            try:
                for word in words:
                    try:
                        num = w2n.word_to_num(word)
                        if num not in quantities:
                            quantities.append(num)
                    except ValueError:
                        continue
            except Exception as e:
                logger.debug(f"word2number processing error: {e}")
        
        # Remove duplicates and sort
        quantities = sorted(list(set(quantities)))
        
        logger.debug(f"Extracted quantities: {quantities}")
        return quantities
    
    def fuzzy_match_items(self, text: str, menu_names: List[str], threshold: int = 75) -> List[str]:
        """Find menu items in text using fuzzy matching"""
        if not menu_names:
            return []
        
        matched_items = []
        text_lower = text.lower()
        
        # Direct substring matching first (highest priority)
        for name in menu_names:
            if name.lower() in text_lower:
                matched_items.append(name)
        
        # If no direct matches, try fuzzy matching
        if not matched_items:
            words = text_lower.split()
            
            # Check each word against menu items
            for word in words:
                if len(word) > 2:  # Ignore very short words
                    best_match = process.extractOne(
                        word, 
                        menu_names, 
                        scorer=fuzz.WRatio
                    )
                    if best_match and best_match[1] >= threshold:
                        if best_match[0] not in matched_items:
                            matched_items.append(best_match[0])
            
            # Also try matching the entire text against each menu item
            for name in menu_names:
                similarity = fuzz.partial_ratio(text_lower, name.lower())
                if similarity >= threshold and name not in matched_items:
                    matched_items.append(name)
        
        logger.debug(f"Fuzzy matched items: {matched_items}")
        return matched_items
    
    def extract_items_advanced(self, text: str, menu_names: List[str]) -> List[str]:
        """Advanced item extraction with context awareness"""
        items = []
        text_lower = text.lower()
        
        # Look for patterns like "2 pizzas", "chicken burger", etc.
        patterns = [
            r'\b\d+\s+(\w+(?:\s+\w+)?)\b',  # "2 pizzas", "1 chicken pizza"
            r'\b(a|an)\s+(\w+(?:\s+\w+)?)\b',  # "a burger", "an ice cream"
            r'\b(some|few)\s+(\w+(?:\s+\w+)?)\b'  # "some fries", "few samosas"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # match might be a tuple from group captures
                item_text = match if isinstance(match, str) else ' '.join(match).strip()
                
                # Try to match against menu items
                best_match = process.extractOne(item_text, menu_names, scorer=fuzz.WRatio)
                if best_match and best_match[1] >= 75:
                    if best_match[0] not in items:
                        items.append(best_match[0])
        
        # If no pattern matches, fall back to fuzzy matching
        if not items:
            items = self.fuzzy_match_items(text, menu_names)
        
        return items

def parse_order(text: str, menu_names: List[str]) -> Dict[str, Any]:
    """
    Main function to parse a restaurant order from natural language text
    
    Args:
        text: Natural language input from user
        menu_names: List of available menu item names
    
    Returns:
        Dictionary containing:
        - intent: The classified intent (order_food, show_menu, etc.)
        - items: List of matched menu items
        - quantities: List of extracted quantities
        - confidence: Confidence score for the parsing
    """
    
    if not text or not text.strip():
        return {
            "intent": "help",
            "items": [],
            "quantities": [],
            "confidence": 0.0
        }
    
    # Initialize NLP processor
    nlp = RestaurantNLP()
    
    # Clean input text
    text = text.strip()
    logger.info(f"Processing order text: {text}")
    
    # Classify intent
    intent = nlp.classify_intent(text)
    
    # Extract items and quantities
    items = []
    quantities = []
    
    if intent == "order_food":
        # Extract items using advanced matching
        items = nlp.extract_items_advanced(text, menu_names)
        
        # If no items found with advanced method, try basic fuzzy matching
        if not items:
            items = nlp.fuzzy_match_items(text, menu_names, threshold=75)
        
        # Extract quantities
        quantities = nlp.extract_quantities(text)
        
        # Ensure we have at least as many quantities as items
        while len(quantities) < len(items):
            quantities.append(1)
        
        # If we have more quantities than items, keep only the first few
        if len(quantities) > len(items) and items:
            quantities = quantities[:len(items)]
    
    # Calculate confidence score
    confidence = calculate_confidence(text, intent, items, quantities)
    
    result = {
        "intent": intent,
        "items": items,
        "quantities": quantities,
        "confidence": confidence
    }
    
    logger.info(f"Parse result: {result}")
    return result

def calculate_confidence(text: str, intent: str, items: List[str], quantities: List[int]) -> float:
    """Calculate confidence score for the parsing result"""
    
    confidence = 0.5  # Base confidence
    
    # Intent confidence
    if intent in ["greeting", "help", "show_menu", "cancel_order"]:
        # These are usually easier to detect
        confidence += 0.2
    elif intent == "order_food":
        if items:
            confidence += 0.3  # Found items
        else:
            confidence -= 0.2  # No items found for food order
    
    # Item extraction confidence
    if items:
        confidence += 0.2
        
        # Check if quantities match items
        if len(quantities) == len(items):
            confidence += 0.1
    
    # Text quality indicators
    text_lower = text.lower()
    
    # Common ordering phrases boost confidence
    ordering_phrases = ['want', 'need', 'order', 'get', 'give me', "i'll have", 'can i have']
    if any(phrase in text_lower for phrase in ordering_phrases):
        confidence += 0.1
    
    # Numbers in text usually indicate quantities
    if re.search(r'\b\d+\b', text) and intent == "order_food":
        confidence += 0.1
    
    # Ensure confidence is between 0 and 1
    confidence = max(0.0, min(1.0, confidence))
    
    return round(confidence, 2)

# Utility functions for testing
def test_nlp_parsing():
    """Test function for NLP parsing"""
    
    sample_menu = [
        "Chicken Pizza", "Beef Burger", "Chicken Burger", "Coke", "Pepsi", 
        "French Fries", "Chicken Wings", "Fish Sandwich", "Ice Cream", 
        "Hot Tea", "Coffee", "Samosa", "Biryani", "Pasta"
    ]
    
    test_cases = [
        "I want 2 chicken pizzas and 1 coke",
        "Give me a burger and fries",
        "I need 3 samosas and 2 teas", 
        "Show me the menu",
        "Cancel my order",
        "Hello, how are you?",
        "What do you have?",
        "I'll have pizza",
        "Can I get some wings and a drink?",
        "Two burgers please"
    ]
    
    print("Testing NLP Parsing:")
    print("=" * 50)
    
    for test_text in test_cases:
        result = parse_order(test_text, sample_menu)
        print(f"\nInput: {test_text}")
        print(f"Intent: {result['intent']}")
        print(f"Items: {result['items']}")
        print(f"Quantities: {result['quantities']}")
        print(f"Confidence: {result['confidence']}")
        print("-" * 30)

if __name__ == "__main__":
    # Run tests if script is executed directly
    test_nlp_parsing()