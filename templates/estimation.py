import os
from groq import Groq

# Initialize client - replace with your API key
client = Groq(api_key="ec499e5e-439b-4bb3-aa32-a9145d0af29f")

# Project context
PROJECT_CONTEXT = """
You are a senior agile software engineering consultant with 15 years of experience in story point estimation.

PROJECT: UniEats - Campus Food Ordering Platform
SCOPE: Mobile-first web application for university food ordering from campus outlets. 
Features include menu browsing, dietary filtering, basket management, payment integration, 
order tracking, vendor dashboards, and admin reporting.

STORY POINT SCALE (Modified Fibonacci):
1 point: ~2-4 person-hours (trivial)
2 points: ~4-8 person-hours (simple)
3 points: ~8-16 person-hours (moderate)
5 points: ~16-32 person-hours (significant)
8 points: ~32-48 person-hours (complex)
13 points: ~48-80 person-hours (very complex)

TEAM: 3 Software Engineers (£35/hr), 2 QA Engineers (£30/hr), 1 DevOps (£40/hr)
CAPACITY: 20 hours/week per person, 34 weeks total
"""

USER_STORIES = [
    "US01: As a customer, I want to browse menus from all campus food outlets",
    "US02: As a customer, I want to filter menu items by dietary requirements",
    "US03: As a customer, I want to add items to a basket and modify quantities",
    "US04: As a customer, I want to pay using the university payment gateway",
    "US05: As a customer, I want to receive a confirmation with estimated collection time",
    "US06: As a customer, I want to track my order status in real-time",
    "US07: As a customer, I want to view my order history",
    "US08: As a customer, I want to save favourite items",
    "US09: As a customer, I want to receive push notifications when my order is ready",
    "US10: As a vendor, I want to update menu items and prices in real-time",
    "US11: As a vendor, I want to mark items as unavailable temporarily",
    "US12: As a vendor, I want to view incoming orders on a dashboard",
    "US13: As a vendor, I want to update order status",
    "US14: As a vendor, I want to set preparation time estimates per item",
    "US15: As an admin, I want to generate sales reports by outlet and time period",
    "US16: As an admin, I want to manage vendor accounts and permissions",
    "US17: NFR - App loads within 2 seconds on campus WiFi",
    "US18: NFR - PCI-DSS compliant payment handling",
    "US19: NFR - Handle 500 concurrent users at peak",
    "US20: NFR - University SSO authentication",
    "US21: NFR - Vendor dashboard works on tablets",
    "US22: NFR - Automated daily backups",
    "US23: NFR - WCAG 2.1 AA accessibility compliance",
    "US24: NFR - Comprehensive audit logging",
]

# Few-shot examples (custom)
CUSTOM_EXAMPLES = """
CALIBRATION EXAMPLES:
| Story | Points | Rationale |
|-------|--------|-----------|
| Search restaurants by cuisine | 3 | Simple filter |
| Add items to cart | 3 | Standard CRUD |
| Checkout and pay | 8 | Payment integration |
| Real-time delivery tracking | 8 | WebSocket infrastructure |
| Update restaurant menu | 5 | CRUD with images |
| Login with Google | 5 | OAuth integration |
| View sales analytics | 8 | Data aggregation |
"""

def estimate_stories(scenario: str, examples: str = None) -> str:
    """Run estimation for a given scenario."""
    
    prompt = PROJECT_CONTEXT + "\n\n"
    
    if examples:
        prompt += examples + "\n\n"
    
    prompt += "USER STORIES TO ESTIMATE:\n"
    prompt += "\n".join(USER_STORIES)
    prompt += """

Provide:
1. Story point estimate for each user story (table format)
2. Total story points
3. Total effort in person-hours  
4. Calendar time required
5. Stories deliverable in 34 weeks
"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert agile estimation consultant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

def main():
    print("=" * 60)
    print("SCENARIO 1: ZERO-SHOT ESTIMATION")
    print("=" * 60)
    result1 = estimate_stories("zero-shot")
    print(result1)
    
    print("\n" + "=" * 60)
    print("SCENARIO 2: FEW-SHOT WITH PROVIDED DATA")
    print("=" * 60)
    # Load from CSV file
    with open("COM663-CW1-2025-26-SUS.csv", "r") as f:
        provided_examples = f.read()
    result2 = estimate_stories("few-shot-provided", provided_examples)
    print(result2)
    
    print("\n" + "=" * 60)
    print("SCENARIO 3: FEW-SHOT WITH CUSTOM DATA")
    print("=" * 60)
    result3 = estimate_stories("few-shot-custom", CUSTOM_EXAMPLES)
    print(result3)
    
    # Save results
    with open("estimation_results.txt", "w") as f:
        f.write("SCENARIO 1: ZERO-SHOT\n" + result1)
        f.write("\n\nSCENARIO 2: FEW-SHOT PROVIDED\n" + result2)
        f.write("\n\nSCENARIO 3: FEW-SHOT CUSTOM\n" + result3)
    
    print("\nResults saved to estimation_results.txt")

if __name__ == "__main__":
    main()
