import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import custom tool functions for shopping assistant
from tools import (
    eccomerce_search_aggregtor,  # Product search and filtering
    shipping_time_estimator,     # Delivery time estimation
    discount_promo_checker,      # Promo code validation
    return_policy_checker,       # Return policy information
    competitor_price_comparison  # Price comparison across sites
)

def initialize_groq_client():
    """Initialize Groq LLM client with API key from environment variables
    
    Returns:
        Groq: Initialized client object
    Raises:
        ValueError: If API key is missing
        Exception: If client initialization fails
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        raise Exception(f"Failed to initialize Groq client: {str(e)}")

# Initialize LLM client globally
try:
    client = initialize_groq_client()
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Constants
MAX_ITERATIONS = 5  # Maximum number of reasoning steps
REACT_SYSTEM_PROMPT = """You are a shopping assistant using the ReAct (Reasoning + Acting) framework. For each tool, verify parameters carefully and analyze responses.

Available Tools and Examples:

1. eccomerce_search_aggregtor:
   Parameters:
   - name (str, optional): Product name to search for (e.g., "sneakers", "dress")
   - color (str, optional): Exact color match ("white", "blue", "multi", "red", "yellow")
   - price_range: Can be specified as:
     * tuple: (min_price, max_price)
     * str: "under 70" or "between 50 and 80"
     * number: 70 (treated as maximum)
   - size (str, optional): Exact size match ("S", "M", "8")
   - in_stock (bool, optional): Filter by availability
   - store (str, optional): Filter by store ("SiteA", "SiteB", "SiteC")
   Returns: JSON list of matching products
   
   Examples:
   [[CALL eccomerce_search_aggregtor, {"name": "sneakers", "color": "white", "size": "8"}]]
   [[CALL eccomerce_search_aggregtor, {"name": "dress", "price_range": "under 100"}]]
   [[CALL eccomerce_search_aggregtor, {"name": "skirt", "size": "S", "price_range": (0, 40)}]]

2. shipping_time_estimator:
   Parameters:
   - product_name (str): Exact product name from database
   - delivery_target (str, optional): Either day name or date
   Returns: Delivery feasibility and dates
   
   Examples:
   [[CALL shipping_time_estimator, {"product_name": "Classic White Sneakers", "delivery_target": "friday"}]]
   [[CALL shipping_time_estimator, {"product_name": "Summer Floral Dress", "delivery_target": "15th"}]]

3. discount_promo_checker:
   Parameters:
   - product_name (str): Exact product name from database
   Returns: Available discount codes
   
   Example:
   [[CALL discount_promo_checker, {"product_name": "Floral Skirt"}]]

4. return_policy_checker:
   Parameters:
   - store_name (str): Must be "SiteA", "SiteB", or "SiteC"
   Returns: Return policy details
   
   Example:
   [[CALL return_policy_checker, {"store_name": "SiteB"}]]

5. competitor_price_comparison:
   Parameters:
   - product_name (str): Exact product name from database
   Returns: Price comparison across stores
   
   Example:
   [[CALL competitor_price_comparison, {"product_name": "Casual Denim Jacket"}]]

Common Query Patterns and Tool Usage:

1. "Find white sneakers under $70":
   Thought: Search for sneakers with color and price constraints
   Action: [[CALL eccomerce_search_aggregtor, {"name": "sneakers", "color": "white", "price_range": "under 70"}]]

2. "Can this be delivered by Friday?":
   Thought: Check delivery feasibility for specific product
   Action: [[CALL shipping_time_estimator, {"product_name": "Classic White Sneakers", "delivery_target": "friday"}]]

3. "Compare prices across stores":
   Thought: Get price comparison after finding exact product name
   Action: [[CALL competitor_price_comparison, {"product_name": "Casual Denim Jacket"}]]

4. "Check return policy":
   Thought: Verify store's return policy
   Action: [[CALL return_policy_checker, {"store_name": "SiteB"}]]

Response Format:
Thought: [clear reasoning step]
Action: [[CALL tool_name, {"param": "exact_value"}]]
Observation: [tool response]
Thought: [analysis of response]
...

Final Recommendation Must Include:
1. Product Details:
   - Exact name from database
   - Verified store and price
   - Confirmed size/color
2. Price Analysis:
   - Base price
   - Valid discount codes only
   - Total with discounts
3. Delivery Details:
   - Estimated delivery date
   - Delivery feasibility
4. Return Policy:
   - Return window
   - Free returns status
   - Conditions

Validation Rules:
- Use exact product names after initial search
- Verify all prices and discounts
- Confirm stock status
- Use exact store names (SiteA, SiteB, SiteC)
- Don't assume unavailable information"""

def call_llm(prompt):
    """Make API call to Groq LLM with system prompt and user query
    
    Args:
        prompt (str): User query and conversation context
    Returns:
        str: LLM response or None if call fails
    """
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": REACT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.5,
            max_tokens=1000
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in LLM call: {e}")
        return None
    
def parse_tool_calls(text):
    """Extract tool calls from LLM response using regex
    
    Args:
        text (str): LLM response text
    Returns:
        list: List of tuples containing (tool_name, parameters)
    """
    tool_calls = []
    pattern = r"\[\[CALL (\w+),\s*(\{.*?\})\]\]"
    matches = re.findall(pattern, text, re.DOTALL)
    for tool_name, params_str in matches:
        try:
            params = json.loads(params_str)
            tool_calls.append((tool_name, params))
        except json.JSONDecodeError:
            print(f"Error parsing parameters for {tool_name}")
    return tool_calls


def execute_tools(tool_name, params):
    """Execute the specified tool with given parameters
    
    Args:
        tool_name (str): Name of tool to execute
        params (dict): Parameters for tool execution
    Returns:
        str: Result of tool execution or error message
    """
    tool_mapping = {
        "eccomerce_search_aggregtor": eccomerce_search_aggregtor,
        "shipping_time_estimator": shipping_time_estimator,
        "discount_promo_checker": discount_promo_checker,
        "return_policy_checker": return_policy_checker,
        "competitor_price_comparison": competitor_price_comparison
    }
    
    try:
        if tool_name in tool_mapping:
            return tool_mapping[tool_name](**params)
        return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"


def react_loop(query):
    """Main ReAct reasoning loop for processing user queries
    
    Args:
        query (str): User's shopping-related query
    Returns:
        str: Final response after reasoning and tool usage
    """
    conversation_context = f"User Query: {query}\n"
    
    for _ in range(MAX_ITERATIONS):
        # Get LLM response with current context
        llm_response = call_llm(conversation_context)
        if not llm_response:
            return "Error: Failed to get LLM response"
        
        # Extract and execute tool calls from response
        tool_calls = parse_tool_calls(llm_response)
        observations = ""
        
        # Execute each tool and collect observations
        for tool_name, params in tool_calls:
            result = execute_tools(tool_name, params)
            observations += f"\nTool: {tool_name}\nParameters: {params}\nObservation: {result}\n"
            print(f"\n[Executed {tool_name}] with params: {params}\nResult: {result}")
        
        # Update conversation history
        conversation_context += f"\nAssistant: {llm_response}\nObservations: {observations}\n"
        
        # Return final answer if no more tool calls needed
        if not tool_calls:
            return llm_response
    
    print("\n[Max iterations reached. Returning final response.]")
    return llm_response

def main():
    """
    Test different scenarios with mock product data
    """
    # Task A: Basic Item Search + Price Constraint
    query_a = (
        "I'm looking for a floral skirt in size S under $40. "
        "Can you check if it's in stock and if I can use the discount code 'SAVE10'?"
    )

    # Task B: Shipping Deadline
    query_b = (
        "I need white sneakers in size 8 under $70 that can be delivered by Friday. "
        "Are there any available options?"
    )

    # Task C: Competitor Price Comparison
    query_c = (
        "I found the Casual Denim Jacket for $80. "
        "Can you check if other sites have better prices for the same jacket?"
    )

    # Task D: Returns & Policies
    query_d = (
        "I'm interested in the red Cocktail Dress from SiteB. "
        "Before buying, can you check their return policy? "
        "I want to make sure returns are hassle-free."
    )

    # Task E: Complex Multi-Tool Query
    query_e = (
        "I'm looking at the Summer Floral Dress ($75) in size S. "
        "Could you: 1) verify it's in stock, "
        "2) check for any discount codes, "
        "3) compare prices on other sites, "
        "4) check shipping time to ZIP 12345, and "
        "5) verify the return policy?"
    )

    # Test queries
    queries = [query_a, query_b, query_c, query_d, query_e]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*20} Test Query {i} {'='*20}")
        print(query)
        final_answer = react_loop(query)
        print("\n=== Final Answer ===")
        print(final_answer)
        print('='*50)

if __name__ == "__main__":
    main()
